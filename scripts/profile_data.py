"""Profile every column of sample_10k_rows.csv and write reports/column_profile.csv.

One row per column: type, missing values, distinct values, share of zeros,
summary statistics and skewness. The literal text "None" is kept as a real
category (it means "no estate plan", "no management role", ...), not as missing.
"""
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
CSV = "sample_10k_rows.csv"
OUT = ROOT / "reports" / "column_profile.csv"


def main() -> None:
    os.chdir(ROOT)
    con = duckdb.connect()
    con.execute(f"create table t as select * from read_csv('{CSV}', sample_size = -1)")
    cols = con.execute(
        "select column_name, data_type from information_schema.columns "
        "where table_name = 't' order by ordinal_position"
    ).fetchall()
    selects = []
    for name, dtype in cols:
        q = f'"{name}"'
        numeric = dtype in ("DOUBLE", "BIGINT")
        stat = (lambda expr: f"round({expr}, 4)") if numeric else (lambda expr: "null")
        selects.append(
            f"""select '{name}' as column_name, '{dtype}' as data_type,
                count(*) - count({q}) as missing,
                round((count(*) - count({q})) / count(*), 4) as missing_share,
                count(distinct {q}) as distinct_values,
                {stat(f"avg(({q} = 0)::int)")} as zero_share,
                {stat(f"min({q})")} as min, {stat(f"median({q})")} as median,
                {stat(f"avg({q})")} as mean, {stat(f"max({q})")} as max,
                {stat(f"case when count(distinct {q}) > 1 then skewness({q}) end")} as skewness,
                {"null" if numeric else f"mode({q})"} as most_common
            from t"""
        )
    OUT.parent.mkdir(exist_ok=True)
    con.execute(f"copy ({' union all '.join(selects)}) to '{OUT}' (header)")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(cols)} columns)")


if __name__ == "__main__":
    main()

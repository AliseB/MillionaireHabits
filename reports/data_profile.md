# Data profile: sample_10k_rows.csv

Profiled with DuckDB (`python scripts/profile_data.py`). Per-column statistics are in
[`column_profile.csv`](column_profile.csv). The dataset is **synthetic**: every pattern
here describes how the generator was built, not real people.

## At a glance

| | |
|---|---|
| Rows | 10,000 (a sample of the 100,000-row full dataset) |
| Columns | 274: 180 decimal, 49 integer, 45 text |
| Unique IDs | 10,000, no duplicates |
| Countries | 25; United States 18%, India 8%, United Kingdom 7% |
| Ages | 22–85; median income $116,773; median net worth $795,391 |
| Millionaires | 42.6% (full dataset: 42.5%) |

### Column groups

| Group | Examples |
|---|---|
| Identity and demographics | `synthetic_person_id`, `country`, `region`, `age`, `gender`, `marital_status` |
| Education and learning | `education_level`, `books_read_per_year`, `online_courses_per_year` |
| Career and income | `occupation_category`, `annual_salary`, `annual_bonus`, `total_annual_income` |
| Entrepreneurship | `business_owner`, `business_revenue`, `business_profit`, `employees_count` |
| Assets, debt and net worth | `total_assets`, `stocks_value`, `mortgage_debt`, `net_worth` |
| Saving, budgeting, investing | `savings_rate`, `budgeting_frequency`, `portfolio_diversification_score` |
| Productivity and time | `deep_work_hours_per_day`, `screen_time_hours_per_day`, `wake_up_time` |
| Health | `sleep_duration_hours`, `exercise_days_per_week`, `stress_level` |
| Psychology | `delayed_gratification_score`, `risk_tolerance_score`, `growth_mindset_score` |
| Social and lifestyle | `networking_frequency`, `home_ownership`, `annual_luxury_spending` |
| Targets and derived flags | `millionaire_status`, `wealth_category`, `high_saver_status`, `*_index`, `*_ratio` |

## Missing data

- **33 columns have missing values**, from 2.3% (`management_level`) to 11.9%
  (`business_failure_count`). Only 1,088 rows (11%) are complete. Most rows miss
  1–3 values, and at most 9.
- **Missingness looks random.** The millionaire rate is within about 4 points whether a
  value is missing or present, for every column. Dropping incomplete rows would
  discard 89% of the data for little gain. Impute instead, or let the model handle
  missing values.
- **Missing values are not structural.** `business_revenue` is missing for 839 people
  who own no business, whose revenue is known to be 0. Missing is just noise added on
  top, so those gaps can be filled with 0.
- **Trap: the text `None` is a real category.** In `management_level` (49%),
  `estate_planning_status` (55%), `tax_planning_behavior` (27%) and
  `panic_selling_frequency`, `None` means "no role" or "no plan". pandas reads
  `None` as missing by default, so `estate_planning_status` looks 63% missing instead
  of 8%. Use `pd.read_csv(..., keep_default_na=False, na_values=[""])`.

## Skew and zero inflation

- **Money columns are heavily right-skewed.** Net worth runs from -$88k to $54.9M
  (mean $1.6M, median $0.8M). Investment assets have a mean of $1.34M and a median of
  $0.57M. Use logs (`net_worth_log` exists) or medians, not means.
- **Many columns are mostly zero.**
  - Business fields are 85–89% zero, because only 15% own a business.
  - Student debt and loan payments are 70% zero.
  - Credit card debt, real estate and mortgage are 65% zero.
  - Investment amounts are 40% zero.

  For modelling, pair each of these with a yes/no flag, and summarise them for owners
  only.
- **`work_to_leisure_ratio` is broken by tiny denominators.** Its median is 2.9 but its
  maximum is 8,981 (skew 70), because 402 people report under 1 leisure hour a week.
  Cap it, or recompute it from the hour columns.
- **The sample is unusually wealthy.** 87% count as "high investors" (≥ $100k
  invested) and 72% as "high savers" (≥ 20% savings rate). 123 people have a
  negative savings rate.

## Redundant and constant columns

- **Constant, so drop them:** `dataset_version`, `generation_seed`, `currency` (all
  USD), `exchange_rate_to_usd`, `has_debt`.
- **Exact duplicates:**
  - `highest_degree` = `education_level`
  - `wealth_bracket` = `wealth_category`
  - `entrepreneur_status` = `business_owner`
  - `total_debt` = `total_liabilities`
  - `credit_card_balance` = `credit_card_debt`
  - `annual_savings` = 12 × `monthly_savings`
  - `annual_investment_amount` = 12 × `monthly_investment_amount`
  - `monthly_income` = `total_annual_income` / 12
- **Nearly identical (r ≥ 0.97):**
  - `total_assets`, `investment_assets` and `net_worth`
  - `total_liabilities` and `mortgage_debt`
  - `annual_salary` and `total_annual_income`
  - `age` and `years_of_experience`
  - `passive_income_ratio` and `investment_income_ratio`

## Inconsistencies

- **Everyone has debt, yet some are debt-free.** `has_debt` is 1 for every row and
  everyone has some liabilities, but 478 people have `debt_free_status = 1`.
- **Employment status doesn't match business ownership.** Only 16% of people whose
  `employment_status` is "Business Owner" have `business_owner = 1`. That is the same
  rate as students (15%) and the unemployed (14%). The two fields were generated
  independently.
- **Currency is USD everywhere.** Values look converted to USD for all 25 countries.
  `region` mixes country-specific values (US "West", Swiss "Zurich") across 99 labels.
- **Small flag mismatches.** 7 rows have a `high_saver_status` that disagrees with
  `savings_rate ≥ 20%`.

## Insights for analysis

- **Most habit columns carry almost no signal.** 101 of 117 non-financial columns
  correlate with `millionaire_status` at |r| < 0.05. Some README questions answer
  themselves:
  - Sleep vs. productivity: r = 0.00.
  - Exercise vs. productivity: r = −0.01.
  - Delayed gratification vs. net worth: r = −0.01.
- **What does drive wealth here:** income (r ≈ 0.48), bonus (0.38), age and experience
  (0.26), education years (0.20), professional network (0.19), and country.
  Millionaires are 64% of the Swiss sample and 10% of the Nigerian one.
- **Leakage warning for modelling `millionaire_status`.** Its strongest correlates are
  computed from net worth or assets: `net_worth_percentile` (0.86), `net_worth_log`,
  `total_assets`, `investment_assets`, `wealth_category`, and probably
  `portfolio_diversification_score` (0.66) and `investment_income_ratio` (0.61).
  Drop every asset, liability, net-worth and target-derived column before training,
  or the model will just read the answer.

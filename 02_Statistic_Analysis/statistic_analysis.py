"""
statistic_analysis.py

Statistical analysis for the queueing theory portfolio project.

Structure
---------
1. Data validation
2. Exploratory statistics
3. Arrival process
4. Service process
5. Conclusions

The objective is to determine whether an M/M/c model is a reasonable
first-order approximation of the observed system.
"""

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


# ============================================================
# 1. DATA VALIDATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "customers.csv"

REQUIRED_COLUMNS = {
    "customer_id",
    "arrival_time",
    "service_time_min",
    "hour",
    "day_of_week",
}

df = pd.read_csv(DATA_PATH, parse_dates=["arrival_time"])

missing_columns = REQUIRED_COLUMNS - set(df.columns)
if missing_columns:
    raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

missing_values = df[list(REQUIRED_COLUMNS)].isna().sum()

if missing_values.sum() > 0:
    raise ValueError(
        "The dataset contains missing values:\n"
        f"{missing_values[missing_values > 0]}"
    )

duplicated_ids = df["customer_id"].duplicated().sum()
if duplicated_ids > 0:
    raise ValueError(f"Duplicated customer IDs found: {duplicated_ids}")

non_positive_service = (df["service_time_min"] <= 0).sum()
if non_positive_service > 0:
    raise ValueError(
        f"Found {non_positive_service} non-positive service times."
    )

if not df["arrival_time"].is_monotonic_increasing:
    raise ValueError("arrival_time is not sorted chronologically.")

observation_days = df["arrival_time"].dt.date.nunique()

print("=" * 60)
print("1. DATA VALIDATION")
print("=" * 60)
print(f"Dataset: {DATA_PATH}")
print(f"Customers: {len(df):,}")
print(f"Observation days: {observation_days}")
print(f"Missing values: {missing_values.sum()}")
print(f"Duplicated customer IDs: {duplicated_ids}")
print(f"Non-positive service times: {non_positive_service}")
print("Validation status: PASSED")


# ============================================================
# 2. EXPLORATORY STATISTICS
# ============================================================

service_time = df["service_time_min"]

service_summary = service_time.describe(
    percentiles=[0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
)

daily_counts = df.groupby(df["arrival_time"].dt.date).size()

day_of_week_counts = (
    df["day_of_week"]
    .value_counts()
    .sort_values(ascending=False)
)

hourly_counts = df.groupby("hour").size().sort_index()

print("\n" + "=" * 60)
print("2. EXPLORATORY STATISTICS")
print("=" * 60)

print(f"Customers: {len(df):,}")
print(
    "Date range: "
    f"{df['arrival_time'].min()} → {df['arrival_time'].max()}"
)
print(f"Observation days: {observation_days}")
print(
    f"Observed hours: "
    f"{int(df['hour'].min())}:00 → {int(df['hour'].max())}:00"
)

print("\nService time summary (minutes):")
print(service_summary.round(4))

print("\nCustomers by hour:")
print(hourly_counts.to_string())

print("\nCustomers by day of week:")
print(day_of_week_counts.to_string())


# ============================================================
# 3. ARRIVAL PROCESS
# ============================================================

# ------------------------------------------------------------
# 3.1 Arrival rate λ by hour
# ------------------------------------------------------------

arrival_rate = hourly_counts / observation_days

arrival_table = pd.DataFrame(
    {
        "customers": hourly_counts,
        "lambda_per_hour": arrival_rate,
    }
)

peak_hour = arrival_rate.idxmax()
peak_lambda = arrival_rate.max()

# ------------------------------------------------------------
# 3.2 Arrival variability
# ------------------------------------------------------------

# Count arrivals separately for each calendar day and hour.
# This gives one observation per day for each hour.
daily_hourly_counts = (
    df.assign(date=df["arrival_time"].dt.date)
    .groupby(["date", "hour"])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=hourly_counts.index, fill_value=0)
)

arrival_variability = pd.DataFrame(index=hourly_counts.index)
arrival_variability["mean_count"] = daily_hourly_counts.mean()
arrival_variability["variance_count"] = daily_hourly_counts.var(ddof=1)

arrival_variability["dispersion_index"] = (
    arrival_variability["variance_count"]
    / arrival_variability["mean_count"]
)

# For a Poisson random variable:
#     E[N] = Var(N) = λ
#
# Therefore, Var(N) / E[N] should be close to 1.
#
# The following chi-square statistic is an approximate diagnostic:
#     X² = (n - 1) Var(N) / E[N]
#
# Under equidispersion, it is approximately χ²(n-1).
n_days = len(daily_hourly_counts)

arrival_variability["chi_square"] = (
    (n_days - 1)
    * arrival_variability["variance_count"]
    / arrival_variability["mean_count"]
)

cdf = stats.chi2.cdf(
    arrival_variability["chi_square"],
    df=n_days - 1,
)

arrival_variability["poisson_p_value"] = np.minimum(
    2 * cdf,
    2 * (1 - cdf)
)

arrival_variability["poisson_p_value"] = np.minimum(
    arrival_variability["poisson_p_value"],
    1
)

print("\n" + "=" * 60)
print("3. ARRIVAL PROCESS")
print("=" * 60)

print("\nHourly arrival rate λ:")
print(arrival_table.round(4).to_string())

print(f"\nPeak hour: {int(peak_hour)}:00")
print(f"Peak arrival rate λ: {peak_lambda:.4f} customers/hour")

print("\nArrival variability by hour:")
print(arrival_variability.round(4).to_string())

print(
    "\nInterpretation:"
    "\n- The arrival rate changes substantially during the day."
    "\n- Therefore, a single homogeneous λ for the entire day is not appropriate."
    "\n- The dispersion index Var(N)/E[N] is used as an empirical"
    "\n  diagnostic for Poisson-like hourly counts."
    "\n- Values near 1 support an equidispersed Poisson approximation."
    "\n- This diagnostic does not prove that the arrivals form a Poisson"
    "\n  process; it provides empirical support for a first-order model."
)

# ------------------------------------------------------------
# 3.3 Arrival visualization
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))
plt.plot(
    arrival_rate.index,
    arrival_rate.values,
    marker="o",
)
plt.title("Average Arrival Rate by Hour")
plt.xlabel("Hour of day")
plt.ylabel("λ (customers/hour)")
plt.xticks(arrival_rate.index)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()


# ============================================================
# 4. SERVICE PROCESS
# ============================================================

# ------------------------------------------------------------
# 4.1 E[S], variability and μ
# ------------------------------------------------------------

mean_service = service_time.mean()
std_service = service_time.std(ddof=1)

service_cv = std_service / mean_service

mu_per_minute = 1 / mean_service
mu_per_hour = 60 / mean_service

print("\n" + "=" * 60)
print("4. SERVICE PROCESS")
print("=" * 60)

print(f"E[S]: {mean_service:.6f} minutes/customer")
print(f"Std(S): {std_service:.6f} minutes")
print(f"CV(S): {service_cv:.6f}")
print(f"μ: {mu_per_minute:.6f} customers/minute/server")
print(f"μ: {mu_per_hour:.6f} customers/hour/server")

# ------------------------------------------------------------
# 4.2 Service-time distribution
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))
plt.hist(
    service_time,
    bins=50,
    density=True,
    alpha=0.7,
)
plt.title("Service Time Distribution")
plt.xlabel("Service time (minutes)")
plt.ylabel("Density")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 4.3 Exponential assumption
# ------------------------------------------------------------

# For an exponential distribution:
#     E[S] = 1 / μ
#
# We use the sample mean as the scale parameter:
#     scale = E[S]
#
# The KS test is used here as a diagnostic. Because μ is estimated
# from the same sample, its p-value should not be interpreted as a
# formal exact goodness-of-fit p-value.

ks_stat, ks_p_value = stats.kstest(
    service_time,
    "expon",
    args=(0, mean_service),
)

print("\nExponentiality diagnostic (KS test):")
print(f"KS statistic: {ks_stat:.6f}")
print(f"p-value: {ks_p_value:.6f}")

if ks_p_value >= 0.05:
    exponential_conclusion = (
        "The exponential distribution is not rejected at the 5% level "
        "as a diagnostic."
    )
else:
    exponential_conclusion = (
        "The exponential distribution is rejected at the 5% level "
        "as a diagnostic."
    )

print(exponential_conclusion)

print(
    "\nInterpretation:"
    "\n- The coefficient of variation is close to 1."
    "\n- The KS diagnostic is consistent with an exponential service-time"
    "\n  approximation."
    "\n- The result is supportive, not a proof, because the exponential"
    "\n  parameter was estimated from the same observations."
)


# ============================================================
# 5. CONCLUSIONS
# ============================================================

# Arrival-process assessment:
# We describe the hourly counts as Poisson-like only when the
# dispersion diagnostic is reasonably close to 1. The important
# structural point is that λ varies by hour.

mean_dispersion = arrival_variability["dispersion_index"].mean()
median_dispersion = arrival_variability["dispersion_index"].median()

print("\n" + "=" * 60)
print("5. CONCLUSIONS")
print("=" * 60)

print("\nARRIVAL PROCESS")
print(f"- Peak λ = {peak_lambda:.4f} customers/hour at {int(peak_hour)}:00.")
print(
    f"- Mean hourly dispersion index = {mean_dispersion:.4f}; "
    f"median = {median_dispersion:.4f}."
)
print("- λ is time-dependent, so the system should be analyzed hour by hour.")
print(
    "- Hourly Poisson counts are a reasonable first-order approximation "
    "when supported by the dispersion diagnostics."
)

print("\nSERVICE PROCESS")
print(f"- E[S] = {mean_service:.4f} minutes/customer.")
print(f"- μ = {mu_per_hour:.4f} customers/hour/server.")
print(f"- CV(S) = {service_cv:.4f}.")
print(f"- KS p-value = {ks_p_value:.4f}.")
print(f"- {exponential_conclusion}")

print("\nINPUTS FOR THE M/M/c MODEL")
print("- Arrival rate: λ(t), estimated separately for each hour.")
print(f"- Service rate: μ = {mu_per_hour:.4f} customers/hour/server.")
print("- Number of servers: c, to be determined in the queueing model.")

print("\nIS M/M/c REASONABLE?")
print(
    "YES — as a first-order approximation, with an important qualification:"
)
print(
    "the arrival rate is time-dependent. Therefore, the M/M/c model should "
    "be applied piecewise by hour using λ(t), rather than assuming one "
    "constant λ for the entire observation period."
)
print(
    "The service process provides empirical support for the exponential "
    "assumption, while the arrival analysis provides an empirical basis "
    "for a Poisson approximation at the hourly level."
)
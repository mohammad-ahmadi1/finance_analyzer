# Finance Analyzer 
# Core logic for loading data, identifying patterns, forecasting, and generating recommendations.


from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

@dataclass(slots=True)
class AnalysisSummary:
    recurring_count: int
    monthly_recurring_cost: float
    current_balance: float
    projected_balance_30d: float
    average_daily_net: float

# Load financial transactions from a CSV file.
# Requires columns: date, description, amount, category. Optionally can include balance.
EXPECTED_COLUMNS = {"date", "description", "amount", "category"}

def load_transactions(csv_path: str) -> pd.DataFrame:

    df = pd.read_csv(csv_path)
    missing = EXPECTED_COLUMNS.difference(df.columns)
    if missing:
        missing_cols = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_cols}. Please ensure the CSV includes these columns with correct headers.")

    df = df.copy()
    # Basic data cleaning and type conversion for handling errors
    if df["date"].isna().any():
        raise ValueError("Found invalid dates in the dataset.")
    if df["description"].isna().any():
        raise ValueError("Found missing descriptions in the dataset.")
    if df["category"].isna().any():
        raise ValueError("Found missing categories in the dataset.")
    if df["amount"].isna().any():
        raise ValueError("Found invalid amount values in the dataset.")
    
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["description"] = df["description"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    if "balance" in df.columns:
        df["balance"] = pd.to_numeric(df["balance"], errors="coerce")

    return df.sort_values("date").reset_index(drop=True)

# Normalize merchant names by lowercasing and collapsing whitespace for better recurring transaction detection.
def _normalize_merchant(text: str) -> str:
    return " ".join(text.lower().split())


def identify_recurring_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Identify likely recurring debit transactions.

    A transaction is considered recurring when:
    - It appears at least 3 times.
    - Dates are roughly monthly (mean gap between 20 and 40 days).
    """
    expenses = df.loc[df["amount"] < 0, ["date", "description", "category", "amount"]].copy()
    if expenses.empty:
        return pd.DataFrame(
            columns=[
                "merchant",
                "category",
                "amount",
                "occurrences",
                "avg_days_between",
                "last_seen",
                "next_expected_date",
                "estimated_monthly_cost",
            ]
        )

    expenses["merchant"] = expenses["description"].map(_normalize_merchant)
    expenses["rounded_amount"] = expenses["amount"].round(2)

    rows: list[dict[str, object]] = []
    grouped = expenses.sort_values("date").groupby(["merchant", "rounded_amount"])
    for (merchant, _), group in grouped:
        if len(group) < 3:
            continue
        day_gaps = group["date"].sort_values().diff().dropna().dt.days
        if day_gaps.empty:
            continue
        avg_gap = float(day_gaps.mean())
        if not 20 <= avg_gap <= 40:
            continue

        amount_value = float(group["rounded_amount"].iloc[0])
        last_seen = group["date"].max()
        next_expected = last_seen + pd.to_timedelta(round(avg_gap), unit="D")
        rows.append(
            {
                "merchant": merchant,
                "category": group["category"].mode().iloc[0],
                "amount": amount_value,
                "occurrences": int(len(group)),
                "avg_days_between": round(avg_gap, 1),
                "last_seen": last_seen.date().isoformat(),
                "next_expected_date": next_expected.date().isoformat(),
                "estimated_monthly_cost": abs(amount_value),
            }
        )

    recurring = pd.DataFrame(rows)
    if recurring.empty:
        return recurring
    return recurring.sort_values("estimated_monthly_cost", ascending=False).reset_index(drop=True)


def build_balance_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """Build historical balance timeline sorted by date."""
    timeline = df.sort_values("date").copy()
    if "balance" in timeline.columns and timeline["balance"].notna().all():
        timeline["running_balance"] = timeline["balance"]
    else:
        timeline["running_balance"] = timeline["amount"].cumsum()

    return timeline[["date", "amount", "running_balance", "category", "description"]].reset_index(drop=True)


def forecast_30_day_balance(df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    """Forecast future balance using daily net cash-flow velocity."""
    if days <= 0:
        raise ValueError("Forecast days must be > 0")

    timeline = build_balance_timeline(df)
    if timeline.empty:
        return pd.DataFrame(columns=["date", "predicted_balance", "lower_bound", "upper_bound"])

    daily_net = timeline.groupby(timeline["date"].dt.date)["amount"].sum().reset_index(name="daily_net")
    recent = daily_net.tail(min(30, len(daily_net)))
    avg_daily_net = float(recent["daily_net"].mean())
    std_daily_net = float(recent["daily_net"].std(ddof=0)) if len(recent) > 1 else 0.0

    start_date = pd.to_datetime(timeline["date"].max())
    current_balance = float(timeline["running_balance"].iloc[-1])

    future_dates = pd.date_range(start=start_date + pd.Timedelta(days=1), periods=days, freq="D")
    day_index = pd.Series(range(1, days + 1), dtype="float")
    drift = day_index * avg_daily_net
    uncertainty = (day_index**0.5) * std_daily_net

    forecast = pd.DataFrame(
        {
            "date": future_dates,
            "predicted_balance": current_balance + drift,
            "lower_bound": current_balance + drift - uncertainty,
            "upper_bound": current_balance + drift + uncertainty,
        }
    )
    return forecast


def summarize_analysis(df: pd.DataFrame, recurring_df: pd.DataFrame, forecast_df: pd.DataFrame) -> AnalysisSummary:
    """Build a compact summary for reporting and recommendation generation."""
    timeline = build_balance_timeline(df)
    current_balance = float(timeline["running_balance"].iloc[-1]) if not timeline.empty else 0.0
    projected_balance = float(forecast_df["predicted_balance"].iloc[-1]) if not forecast_df.empty else current_balance

    recent_daily = (
        timeline.groupby(timeline["date"].dt.date, as_index=False)["amount"]
        .sum()
        .tail(30)
    )
    avg_daily_net = float(recent_daily["amount"].mean()) if not recent_daily.empty else 0.0

    return AnalysisSummary(
        recurring_count=int(len(recurring_df)),
        monthly_recurring_cost=float(recurring_df["estimated_monthly_cost"].sum()) if not recurring_df.empty else 0.0,
        current_balance=current_balance,
        projected_balance_30d=projected_balance,
        average_daily_net=avg_daily_net,
    )


def _status_from_projection(projected_balance_30d: float) -> str:
    match projected_balance_30d:
        case value if value < 0:
            return "critical"
        case value if value < 500:
            return "warning"
        case _:
            return "healthy"


def generate_recommendations(df: pd.DataFrame, recurring_df: pd.DataFrame) -> str:
    """Generate practical financial recommendations from analyzed data."""
    forecast_df = forecast_30_day_balance(df, days=30)
    summary = summarize_analysis(df, recurring_df, forecast_df)
    projection_status = _status_from_projection(summary.projected_balance_30d)

    top_expense = (
        df.loc[df["amount"] < 0]
        .groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values(by="amount")
        .head(1)
    )
    top_category = top_expense["category"].iloc[0] if not top_expense.empty else "general"
    top_category_spend = abs(float(top_expense["amount"].iloc[0])) if not top_expense.empty else 0.0

    lines = [
        f"Detected {summary.recurring_count} recurring payments totaling €{summary.monthly_recurring_cost:,.2f}/month.",
        f"Current balance is €{summary.current_balance:,.2f}; projected 30-day balance is €{summary.projected_balance_30d:,.2f}.",
    ]

    if projection_status == "critical":
        lines.append("Balance is projected to go negative. Prioritize reducing discretionary spending immediately.")
    elif projection_status == "warning":
        lines.append("Projected balance is low. Build a short-term spending buffer over the next 30 days.")
    else:
        lines.append("Cash flow looks stable. Consider allocating part of surplus to savings or debt payoff.")

    lines.extend(
        [
            f"Highest spending category is '{top_category}' at about €{top_category_spend:,.2f}.",
            "Review recurring subscriptions and cancel any inactive services.",
            "Use a weekly budget check-in to keep spending aligned with your target balance.",
        ]
    )

    return "\n".join(lines)

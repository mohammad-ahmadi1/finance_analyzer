"""CLI entry point for the finance analyzer package."""

from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import (
    build_balance_timeline,
    forecast_30_day_balance,
    generate_recommendations,
    identify_recurring_transactions,
    load_transactions,
)
from .visualizer import plot_balance_forecast, plot_spending_categories


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(description="Analyze personal finance transactions.")
    parser.add_argument("--data", required=True, help="Path to transactions CSV file")
    parser.add_argument("--output-dir", default="outputs", help="Directory for generated artifacts")
    parser.add_argument("--forecast-days", type=int, default=30, help="Number of future days to forecast")
    return parser


def main() -> None:
    """Run the command-line application."""
    parser = build_parser()
    args = parser.parse_args()

    data_path = Path(args.data)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_transactions(str(data_path))
    recurring_df = identify_recurring_transactions(df)
    balance_df = build_balance_timeline(df)
    forecast_df = forecast_30_day_balance(df, days=args.forecast_days)
    recommendations = generate_recommendations(df, recurring_df)

    recurring_csv = output_dir / "recurring_transactions.csv"
    forecast_csv = output_dir / "forecast_30_day_balance.csv"
    recommendations_txt = output_dir / "recommendations.txt"
    spending_plot = output_dir / "spending_categories.png"
    forecast_plot = output_dir / "balance_forecast.png"

    recurring_df.to_csv(recurring_csv, index=False)
    forecast_df.to_csv(forecast_csv, index=False)
    recommendations_txt.write_text(recommendations + "\n", encoding="utf-8")

    plot_spending_categories(df, str(spending_plot))
    plot_balance_forecast(balance_df, forecast_df, str(forecast_plot))

    print("Finance analysis completed successfully.")
    print(f"Input file: {data_path}")
    print(f"Recurring payments detected: {len(recurring_df)}")
    if not forecast_df.empty:
        print(f"Projected balance in {args.forecast_days} days: €{forecast_df['predicted_balance'].iloc[-1]:,.2f}")
    print(f"Outputs saved to: {output_dir}")
    print(f"- {recurring_csv.name}")
    print(f"- {forecast_csv.name}")
    print(f"- {recommendations_txt.name}")
    print(f"- {spending_plot.name}")
    print(f"- {forecast_plot.name}")


if __name__ == "__main__":
    main()

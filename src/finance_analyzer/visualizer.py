"""Visualization utilities for the finance analyzer."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_spending_categories(df: pd.DataFrame, output_path: str) -> str:
    """Create a pie chart of total spending by category."""
    expenses = df.loc[df["amount"] < 0].copy()
    if expenses.empty:
        raise ValueError("No expense transactions available for category plot.")

    category_totals = expenses.groupby("category", as_index=False)["amount"].sum()
    category_totals["amount"] = category_totals["amount"].abs()
    category_totals = category_totals.sort_values("amount", ascending=False)

    sns.set_theme(style="whitegrid")
    # Make the figure slightly wider to accommodate the legend
    fig, ax = plt.subplots(figsize=(11, 7)) 
    colors = sns.color_palette("Set2", n_colors=len(category_totals))
    
    pie_result = ax.pie(
        category_totals["amount"],
        labels=category_totals["category"],
        autopct="%1.1f%%",
        startangle=120,
        colors=colors,
        wedgeprops={"edgecolor": "white", "linewidth": 1},
        pctdistance=0.85  
    )
    wedges = pie_result[0]

    total_spent = category_totals["amount"].sum()
    category_totals["percent"] = (category_totals["amount"] / total_spent) * 100
    legend_labels = [
        f"{p:.1f}% {c}" for p, c in zip(category_totals["percent"], category_totals["category"])
    ]
    # Add a legend
    ax.legend(
        wedges, 
        legend_labels, 
        title="Categories", 
        loc="center left", 
        bbox_to_anchor=(1, 0, 0.5, 1)
    )

    ax.set_title("Spending Distribution by Category")
    ax.axis("equal")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def plot_balance_forecast(balance_df: pd.DataFrame, forecast_df: pd.DataFrame, output_path: str) -> str:
    """Create a line chart showing actual and forecasted balances."""
    if balance_df.empty:
        raise ValueError("Balance timeline is empty.")
    if forecast_df.empty:
        raise ValueError("Forecast data is empty.")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        pd.to_datetime(balance_df["date"]),
        balance_df["running_balance"],
        label="Historical Balance",
        color="#1f77b4",
        linewidth=2.0,
    )
    ax.plot(
        pd.to_datetime(forecast_df["date"]),
        forecast_df["predicted_balance"],
        label="Forecast Balance",
        color="#ff7f0e",
        linewidth=2.0,
        linestyle="--",
    )
    ax.fill_between(
        pd.to_datetime(forecast_df["date"]),
        forecast_df["lower_bound"],
        forecast_df["upper_bound"],
        color="#ff7f0e",
        alpha=0.2,
        label="Forecast Range",
    )

    ax.set_title("Historical and Forecasted Account Balance")
    ax.set_xlabel("Date")
    ax.set_ylabel("Balance (€)")
    ax.legend()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)

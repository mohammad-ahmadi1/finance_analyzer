# Finance Analyzer

Finance Analyzer is a focused Python tool for practical personal-finance insights. It solves a meaningful problem by:

- Detecting likely recurring payments (subscriptions and monthly bills)
- Forecasting future account balance based on recent spending velocity
- Generating actionable savings recommendations
- Visualizing spending mix and projected balance trend

## Requirements

- Python 3.10+
- `uv` (for package installation and execution)
- transaction data of your account in csv format there is a [mock dataset](./data/mock_transactions_income_3000.csv) for local analyses and test

## Installation

Use the exact grading installation command:

```bash
uv pip install -e .
```

## Run

For running the app use:

```bash
uv run -m finance_analyzer --data path/to/data.csv
```

Example with included dataset:

```bash
uv run -m finance_analyzer --data data/mock_transactions_data.csv
```

Optional arguments:

- `--output-dir outputs` (default: `outputs`)
- `--forecast-days 30` (default: `30`)

## Outputs

Running the CLI creates the `outputs` folder and the below files:

- `outputs/recurring_transactions.csv`
- `outputs/forecast_30_day_balance.csv`
- `outputs/recommendations.txt`
- `outputs/spending_categories.png`
- `outputs/balance_forecast.png`

## Notebook Walkthrough

See [`notebooks/example_usage.ipynb`](./notebooks/example_usage.ipynb) for a step-by-step analysis workflow that:

- Loads data
- Detects recurring transactions
- Forecasts balance
- Generates recommendation text
- Produces visual plots

## Package

From the source file run `uv build` creates a `.whl` file which you can share the program as a package.

### Load the package and run the program

```bash
uv pip install `/path/to/finance_analyzer-0.1.0-py3-none-any.whl`
```

and then run

```bash
uv run python -m finance_analyzer --data /path/to/your/dataset.csv
```

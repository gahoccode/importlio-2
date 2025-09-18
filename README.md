# Importfolio: Vietnam Stock Portfolio Optimizer

## Overview
A Python Flask web application for mean-variance portfolio optimization using Vietnam stock data (via `vnstock`) and PyPortfolioOpt. Visualizations powered by Plotly. Responsive UI with Bootstrap.

## Features
- Input risk-free rate, number of simulations, and stock tickers
- Fetches Vietnam stock prices
- Optimizes portfolio (mean-variance) using PyPortfolioOpt with OSQP solver
- Visualizes efficient frontier and asset allocation

## Setup Instructions

### 1. Clone the repository

### 2. Create a virtual environment
```
python -m venv venv
```

### 3. Activate the virtual environment (Windows)
```
venv\Scripts\activate
```

### 4. Install dependencies
```
pip install -r requirements.txt
```

### 5. Run the app
```
python app.py
```

### Poetry/uv alternative
```
poetry install
poetry run python app.py
```

### 6. Run tests
```
pytest
```

## Project Structure
- `app.py`: Flask backend
- `templates/`: HTML templates
- `static/css/`: Custom CSS
- `static/js/`: Custom JS
- `tests/`: Unit/integration tests

## Dependencies Note
- **PyPortfolioOpt**: Core optimization library that automatically includes OSQP solver
- **OSQP**: Quadratic programming solver (bundled with PyPortfolioOpt, no explicit dependency needed)
- **Cross-platform**: Uses pre-built wheels for Mac ARM64 and Linux x86_64

## Batch Script
See `run_importfolio.bat` for automated setup and run options.

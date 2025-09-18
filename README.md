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

### UV alternative
```
uv sync
uv run python app.py
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

## Container Deployment

### Docker
```bash
# Build the Docker image
docker build -t importfolio:latest .

# Run with Docker (development)
docker run -p 8080:10000 -e PORT=10000 importfolio:latest

# Run with Docker Compose (development)
docker-compose up --build
```

### Local Build and Push
```bash
# Authentication (choose one)
export GITHUB_TOKEN=your_token
# OR
gh auth login

# Usage examples
./build-and-push.sh                    # Auto-detects branch/tag
./build-and-push.sh --tag v1.2.3       # Custom tag
./build-and-push.sh --build-only       # Build without push
```

## Batch Script
See `run_importfolio.bat` for automated setup and run options.

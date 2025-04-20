"""
Flask backend for Importfolio: Vietnam Stock Portfolio Optimizer
- / : index page with form
- /optimize : process input, fetch data, optimize, show results
"""
import os
import io
import base64
import traceback
import matplotlib
matplotlib.use("Agg")  # Use non-GUI backend for server renderings as Tkinter GUI errors
from flask import Flask, render_template, request, redirect, url_for, flash
import numpy as np
import pandas as pd
from vnstock import Quote

from pypfopt import EfficientFrontier, risk_models, expected_returns, DiscreteAllocation
from pypfopt.exceptions import OptimizationError

app = Flask(__name__)
app.secret_key = 'importfolio-secret-key'  # Replace with a secure key in production

TRADING_DAYS_PER_YEAR = 252

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    # Ensure matplotlib uses a safe default style to avoid style errors
    import matplotlib.pyplot as plt
    def safe_style_use(style):
        if style == "seaborn-deep":
            style = "default"
        return plt._original_style_use(style)
    if not hasattr(plt, "_original_style_use"):
        plt._original_style_use = plt.style.use
        plt.style.use = safe_style_use
    try:
        plt.style.use("default")
    except Exception:
        pass
    try:
        # Input validation
        risk_free_rate = float(request.form.get('risk_free_rate', 0.01))
        num_simulations = request.form.get('num_simulations', type=int)
        tickers_raw = request.form.get('tickers', type=str)
        start_date_str = request.form.get('start_date', type=str)
        end_date_str = request.form.get('end_date', type=str)
        if risk_free_rate is None or num_simulations is None or not tickers_raw or not start_date_str or not end_date_str:
            flash('All fields are required.', 'danger')
            return redirect(url_for('index'))
        # Parse dates to pandas Timestamps
        import pandas as pd
        start_date = pd.to_datetime(start_date_str)
        end_date = pd.to_datetime(end_date_str)
        try:
            start_date = pd.to_datetime(start_date_str)
            end_date = pd.to_datetime(end_date_str)
            if start_date > end_date:
                flash('Start date must be before or equal to end date.', 'danger')
                return redirect(url_for('index'))
        except Exception:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('index'))
        if num_simulations < 1 or num_simulations > 10000:
            flash('Number of simulations must be between 1 and 10,000.', 'danger')
            return redirect(url_for('index'))
        tickers = [t.strip().upper() for t in tickers_raw.split(',') if t.strip()]
        if len(tickers) < 2:
            flash('Please enter at least two stock tickers.', 'danger')
            return redirect(url_for('index'))

        # Fetch historical price data using vnstock Quote and user date range
        prices = pd.DataFrame()
        start_date_fmt = start_date.strftime('%Y-%m-%d')
        end_date_fmt = end_date.strftime('%Y-%m-%d')
        for ticker in tickers:
            try:
                quote = Quote(symbol=ticker)
                df = quote.history(
                    start=start_date_fmt,
                    end=end_date_fmt,
                    interval='1D',
                    to_df=True
                )
                if df is None or df.empty or 'close' not in df.columns:
                    flash(f"No price data found for {ticker}.", 'danger')
                    return redirect(url_for('index'))
                df = df[['time', 'close']].copy()
                df.rename(columns={'time': 'date'}, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                prices = pd.merge(prices, df[['date', 'close']].rename(columns={'close': ticker}), on='date', how='outer') if not prices.empty else df.rename(columns={'close': ticker})
            except Exception as e:
                flash(f"Error fetching data for {ticker}: {e}", 'danger')
                return redirect(url_for('index'))
        prices = prices.set_index('date').sort_index().dropna()
        if prices.shape[0] < 30:
            flash('Not enough historical data for selected tickers.', 'danger')
            return redirect(url_for('index'))

        # Calculate expected returns and sample covariance
        returns = prices.pct_change().dropna()
        exp_returns = expected_returns.mean_historical_return(prices, frequency=TRADING_DAYS_PER_YEAR)
        cov_matrix = risk_models.sample_cov(prices, frequency=TRADING_DAYS_PER_YEAR)

        # Portfolio optimization
        try:
            ef = EfficientFrontier(exp_returns, cov_matrix)
            # Add all objectives/constraints here if needed (none in this case)
            weights = ef.max_sharpe(risk_free_rate=risk_free_rate/100)
            cleaned_weights = ef.clean_weights()
            perf = ef.portfolio_performance(risk_free_rate=risk_free_rate/100)
        except OptimizationError as oe:
            import traceback
            print("OptimizationError:", oe)
            print(traceback.format_exc())
            msg = str(oe)
            if "at least one of the assets must have an expected return exceeding the risk-free rate" in msg:
                flash("No portfolio can be constructed because all selected assets have expected returns below or equal to the risk-free rate.\n\nSuggestions:\n- Lower the risk-free rate\n- Change the date range to a period with better performance\n- Choose different stocks with higher returns", 'warning')
            else:
                flash(f"Optimization failed: {oe}", 'danger')
            return redirect(url_for('index'))
        except Exception as e:
            import traceback
            print("General Exception:", e)
            print(traceback.format_exc())
            msg = str(e)
            if "at least one of the assets must have an expected return exceeding the risk-free rate" in msg:
                flash("No portfolio can be constructed because all selected assets have expected returns below or equal to the risk-free rate.\n\nSuggestions:\n- Lower the risk-free rate\n- Change the date range to a period with better performance\n- Choose different stocks with higher returns", 'warning')
            else:
                flash(f"Optimization error: {e}", 'danger')
            return redirect(url_for('index'))

        # Prepare metrics
        metrics = {
            'exp_return': round(perf[0]*100, 2),
            'volatility': round(perf[1]*100, 2),
            'sharpe_ratio': round(perf[2], 2)
        }

        # Efficient frontier simulation
        frontier_returns = []
        frontier_vols = []
        for alpha in np.linspace(0, 1, num_simulations):
            try:
                ef_sim = EfficientFrontier(exp_returns, cov_matrix)
                ef_sim.efficient_risk(target_volatility=perf[1]*alpha)
                ret, vol, _ = ef_sim.portfolio_performance(risk_free_rate=risk_free_rate/100)
                frontier_returns.append(ret*100)
                frontier_vols.append(vol*100)
            except Exception:
                continue

        # Asset allocation for pie chart
        allocation_labels = list(cleaned_weights.keys())
        allocation_values = [round(w*100, 2) for w in cleaned_weights.values()]

        # --- Custom seaborn efficient frontier plot ---
        import matplotlib.pyplot as plt
        import seaborn as sns
        import io, base64
        plt.figure(figsize=(8, 6))
        sns.set(style="whitegrid", context="notebook")
        ax = plt.gca()
        # Plot the efficient frontier using seaborn
        sns.lineplot(x=frontier_vols, y=frontier_returns, ax=ax, color="blue", label="Efficient Frontier")
        ax.scatter(frontier_vols, frontier_returns, marker=".", c="orange", label="Simulated Portfolios")
        # Mark the mean-variance (max Sharpe) portfolio on the chart
        mv_vol = perf[1]*100
        mv_ret = perf[0]*100
        ax.scatter([mv_vol], [mv_ret], marker="*", s=200, c="red", label="Max Sharpe Portfolio")
        ax.set_xlabel("Volatility (%)")
        ax.set_ylabel("Expected Return (%)")
        ax.set_title("Efficient Frontier with Simulated Portfolios")
        ax.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        efficient_frontier_img = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()

        # Pass data to results template
        return render_template(
            'results.html',
            metrics=metrics,
            frontier_data={
                'returns': frontier_returns,
                'vols': frontier_vols
            },
            allocation_data={
                'labels': allocation_labels,
                'values': allocation_values
            },
            efficient_frontier_img=efficient_frontier_img
        )
    except Exception as e:
        flash(f"Unexpected error: {e}", 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

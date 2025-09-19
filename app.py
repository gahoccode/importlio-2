"""
Flask backend for Importfolio: Vietnam Stock Portfolio Optimizer
- / : index page with form
- /optimize : process input, fetch data, optimize, show results
"""
import os
import io
import base64
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash
import numpy as np
import pandas as pd
from vnstock import Quote
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json

from pypfopt import EfficientFrontier, risk_models, expected_returns, DiscreteAllocation
from pypfopt.exceptions import OptimizationError

app = Flask(__name__)
app.secret_key = 'importfolio-secret-key'  # Replace with a secure key in production

TRADING_DAYS_PER_YEAR = 252

# Validation Constants (shared with frontend)
MIN_SIMULATIONS = 1
MAX_SIMULATIONS = 10000
MIN_TICKERS = 2
MAX_TICKERS = 10
MIN_HISTORICAL_DAYS = 30
MAX_RISK_FREE_RATE = 0.5

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container monitoring"""
    return {'status': 'healthy', 'service': 'importfolio'}, 200

@app.route('/validation-constants', methods=['GET'])
def validation_constants():
    """Validation constants for frontend JavaScript"""
    return {
        'MIN_SIMULATIONS': MIN_SIMULATIONS,
        'MAX_SIMULATIONS': MAX_SIMULATIONS,
        'MIN_TICKERS': MIN_TICKERS,
        'MAX_TICKERS': MAX_TICKERS,
        'MIN_HISTORICAL_DAYS': MIN_HISTORICAL_DAYS,
        'MAX_RISK_FREE_RATE': MAX_RISK_FREE_RATE
    }, 200

@app.route('/optimize', methods=['POST'])
def optimize():
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
        if num_simulations < MIN_SIMULATIONS or num_simulations > MAX_SIMULATIONS:
            flash(f'Number of simulations must be between {MIN_SIMULATIONS} and {MAX_SIMULATIONS:,}.', 'danger')
            return redirect(url_for('index'))
        tickers = [t.strip().upper() for t in tickers_raw.split(',') if t.strip()]
        if len(tickers) < MIN_TICKERS:
            flash(f'Please enter at least {MIN_TICKERS} stock tickers.', 'danger')
            return redirect(url_for('index'))
        if len(tickers) > MAX_TICKERS:
            flash(f'Too many stocks. Please limit to {MAX_TICKERS} tickers for optimal performance.', 'warning')
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
        if prices.shape[0] < MIN_HISTORICAL_DAYS:
            flash(f'Not enough historical data. Need at least {MIN_HISTORICAL_DAYS} trading days for reliable optimization.', 'danger')
            return redirect(url_for('index'))

        # Calculate expected returns and sample covariance
        returns = prices.pct_change().dropna()
        exp_returns = expected_returns.mean_historical_return(prices, frequency=TRADING_DAYS_PER_YEAR)
        cov_matrix = risk_models.sample_cov(prices, frequency=TRADING_DAYS_PER_YEAR)

        # Portfolio optimization
        try:
            ef = EfficientFrontier(exp_returns, cov_matrix)
            # Add all objectives/constraints here if needed (none in this case)
            weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
            cleaned_weights = ef.clean_weights()
            perf = ef.portfolio_performance(risk_free_rate=risk_free_rate)
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
                ret, vol, _ = ef_sim.portfolio_performance(risk_free_rate=risk_free_rate)
                frontier_returns.append(ret*100)
                frontier_vols.append(vol*100)
            except Exception:
                continue

        # Asset allocation for pie chart
        allocation_labels = list(cleaned_weights.keys())
        allocation_values = [round(w*100, 2) for w in cleaned_weights.values()]

        # --- Plotly.py efficient frontier chart ---
        # Theme colors matching CSS variables
        colors = {
            'primary': '#56524D',
            'categorical': ['#204F80', '#804F1F', '#0A2845', '#426F99', '#45280A', '#996F42'],
            'text': '#1F1916',
            'background': '#FFFFFF'
        }
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add efficient frontier line
        fig.add_trace(go.Scatter(
            x=frontier_vols,
            y=frontier_returns,
            mode='lines+markers',
            name='Efficient Frontier',
            line=dict(color=colors['categorical'][0], width=3),
            marker=dict(color=colors['categorical'][1], size=4),
            hovertemplate='<b>Portfolio Point</b><br>' +
                         'Volatility: %{x:.2f}%<br>' +
                         'Expected Return: %{y:.2f}%<br>' +
                         '<extra></extra>'
        ))
        
        # Mark the optimal (max Sharpe) portfolio
        mv_vol = perf[1]*100
        mv_ret = perf[0]*100
        fig.add_trace(go.Scatter(
            x=[mv_vol],
            y=[mv_ret],
            mode='markers',
            name='Optimal Portfolio',
            marker=dict(
                color='red',
                size=15,
                symbol='star',
                line=dict(color=colors['text'], width=2)
            ),
            hovertemplate='<b>Optimal Portfolio</b><br>' +
                         'Volatility: %{x:.2f}%<br>' +
                         'Expected Return: %{y:.2f}%<br>' +
                         f'Sharpe Ratio: {metrics["sharpe_ratio"]}<br>' +
                         '<extra></extra>'
        ))
        
        # Add risk-free rate line
        max_vol = max(frontier_vols) if frontier_vols else 20
        fig.add_trace(go.Scatter(
            x=[0, max_vol],
            y=[risk_free_rate*100, risk_free_rate*100],
            mode='lines',
            name=f'Risk-Free Rate ({risk_free_rate*100:.1f}%)',
            line=dict(color=colors['text'], width=1, dash='dash'),
            hovertemplate='Risk-Free Rate: %{y:.2f}%<extra></extra>'
        ))
        
        # Update layout with theme styling
        fig.update_layout(
            title={
                'text': 'Efficient Frontier Analysis',
                'x': 0.5,
                'font': {'size': 18, 'color': colors['primary'], 'family': 'Georgia, serif'}
            },
            xaxis=dict(
                title='Volatility (%)',
                gridcolor='#E4E4E4',
                title_font=dict(color=colors['text'], family='Georgia, serif'),
                tickfont=dict(color=colors['text'])
            ),
            yaxis=dict(
                title='Expected Return (%)',
                gridcolor='#E4E4E4',
                title_font=dict(color=colors['text'], family='Georgia, serif'),
                tickfont=dict(color=colors['text'])
            ),
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font=dict(family='Georgia, serif', color=colors['text']),
            legend=dict(
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor=colors['text'],
                borderwidth=1
            ),
            width=800,
            height=500
        )
        
        # Convert to HTML and base64 for embedding
        efficient_frontier_html = fig.to_html(include_plotlyjs='cdn', div_id='plotly-efficient-frontier')
        
        # Also create a static PNG for fallback/printing
        try:
            efficient_frontier_img = fig.to_image(format="png", width=800, height=500)
            efficient_frontier_img = base64.b64encode(efficient_frontier_img).decode("utf-8")
        except Exception as e:
            print(f"Warning: Could not generate PNG image: {e}")
            efficient_frontier_img = None

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
            efficient_frontier_html=efficient_frontier_html,
            efficient_frontier_img=efficient_frontier_img
        )
    except Exception as e:
        flash(f"Unexpected error: {e}", 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

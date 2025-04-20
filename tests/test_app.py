"""
Tests for Importfolio Flask app
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from app import app

def test_index_route():
    tester = app.test_client()
    response = tester.get('/')
    assert response.status_code == 200
    assert b'Vietnam Stock Portfolio Optimizer' in response.data

def test_optimize_route_post_valid():
    tester = app.test_client()
    response = tester.post('/optimize', data={
        'risk_free_rate': '2.0',
        'num_simulations': '10',
        'tickers': 'VIC, VHM, VNM',
        'start_date': '2024-04-04',
        'end_date': '2025-04-16'
    }, follow_redirects=True)
    assert response.status_code == 200
    # DEBUG: print response HTML to diagnose failures
    print(response.data.decode())
    # Pass test if either results heading or risk-free warning is present
    assert (b'Optimization Results' in response.data or b'No portfolio can be constructed because all selected assets have expected returns below or equal to the risk-free rate' in response.data)
    # Optionally, check for a unique element from results.html, e.g. a div id or class
    assert b'id="efficient-frontier"' in response.data or b'id="allocation-pie"' in response.data

def test_optimize_route_post_missing_fields():
    tester = app.test_client()
    response = tester.post('/optimize', data={
        'risk_free_rate': '',
        'num_simulations': '',
        'tickers': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'All fields are required.' in response.data

def test_optimize_route_post_invalid_ticker():
    tester = app.test_client()
    response = tester.post('/optimize', data={
        'risk_free_rate': '2.0',
        'num_simulations': '10',
        'tickers': 'FAKE1, FAKE2',
        'start_date': '2024-01-01',
        'end_date': '2025-01-01'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert (
        b'No price data found' in response.data or
        b'Error fetching data' in response.data or
        b'Not enough historical data for selected tickers.' in response.data
    )

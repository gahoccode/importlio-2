Create a Python-based web application with the following specifications:

**Framework & Libraries:**
- Backend: Flask
- Frontend: HTML, CSS, Bootstrap
- Data Loader: `vnstock` (for fetching Vietnam stock prices)
- Optimization: `PyPortfolioOpt` (for mean-variance portfolio optimization)

**Frontend Structure:**

1. **HTML Templates (in `templates/` folder):**
   - `index.html`:
     - Contains a form for user input:
       - Risk-free rate (float input)
       - Number of simulations (integer input)
       - List of stock tickers (textarea or tag input)
     - Uses Bootstrap for responsive layout
     - Sends POST request to `/optimize` on submission
   - `results.html`:
     - Displays optimized portfolio metrics (e.g., expected return, volatility, Sharpe ratio)
     - Includes charts: efficient frontier, asset allocation pie chart
     - Uses Bootstrap and Chart.js or Plotly for visualizations

2. **Static Assets (in `static/` folder):**
   - `css/style.css`: Custom styling for layout, buttons, forms
   - `js/script.js`: Client-side validation for input fields and enhanced UX (e.g., loading spinner)

**Backend Structure (`app.py`):**
- `/`: Renders `index.html`
- `/optimize`: Accepts form data via POST, fetches stock price data using `vnstock`, runs optimization using `PyPortfolioOpt`, then renders `results.html` with output charts and stats
- Includes error handling and form validation

**Testing (`tests/test_app.py`):**
- Unit tests for:
  - Data fetching with `vnstock`
  - Portfolio optimization logic with edge case inputs
- Integration tests for Flask routes:
  - GET `/` returns 200 and loads `index.html`
  - POST `/optimize` with valid/invalid inputs behaves as expected
- Frontend tests (via Selenium or similar optional):
  - Form field validation
  - UI responsiveness checks

**User Experience:**
- Responsive design using Bootstrap grid
- Accessible color schemes and font sizes
- Clear input guidance and error feedback
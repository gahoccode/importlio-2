// Client-side validation and UX enhancements

document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('portfolio-form');
    if (form) {
        form.addEventListener('submit', function (e) {
            var riskFree = document.getElementById('risk_free_rate');
            var numSims = document.getElementById('num_simulations');
            var tickers = document.getElementById('tickers');
            var feedback = document.getElementById('form-feedback');
            var valid = true;
            feedback.innerHTML = '';

            if (!riskFree.value || isNaN(riskFree.value)) {
                valid = false;
                feedback.innerHTML += '<div class="alert alert-danger">Risk-free rate is required and must be a number.</div>';
            }
            if (!numSims.value || isNaN(numSims.value) || numSims.value < 1 || numSims.value > 10000) {
                valid = false;
                feedback.innerHTML += '<div class="alert alert-danger">Number of simulations must be between 1 and 10,000.</div>';
            }
            if (!tickers.value || tickers.value.split(',').filter(t => t.trim()).length < 2) {
                valid = false;
                feedback.innerHTML += '<div class="alert alert-danger">Please enter at least two stock tickers, comma-separated.</div>';
            }
            if (!valid) {
                e.preventDefault();
                return false;
            }
            // Show loading spinner
            var btn = form.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Optimizing...';
        });
    }
});

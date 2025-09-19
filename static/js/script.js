// Enhanced client-side validation and UX interactions

// Validation constants (loaded from backend)
let validationConstants = {
    MIN_SIMULATIONS: 1,
    MAX_SIMULATIONS: 10000,
    MIN_TICKERS: 2,
    MAX_TICKERS: 10,
    MIN_HISTORICAL_DAYS: 30,
    MAX_RISK_FREE_RATE: 0.5
};

// Load validation constants from backend
fetch('/validation-constants')
    .then(response => response.json())
    .then(data => {
        validationConstants = data;
    })
    .catch(error => {
        console.warn('Could not load validation constants:', error);
    });

document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('portfolio-form');
    if (form) {
        
        // Enhanced form validation and submission
        form.addEventListener('submit', function (e) {
            var riskFree = document.getElementById('risk_free_rate');
            var numSims = document.getElementById('num_simulations');
            var tickers = document.getElementById('tickers');
            var startDate = document.getElementById('start_date');
            var endDate = document.getElementById('end_date');
            var feedback = document.getElementById('form-feedback');
            var valid = true;
            feedback.innerHTML = '';

            // Validate risk-free rate
            if (!riskFree.value || isNaN(riskFree.value)) {
                valid = false;
                feedback.innerHTML += '<div class="alert alert-danger"><strong>Risk-free Rate:</strong> Please enter a valid number (e.g., 0.02 for 2%).</div>';
            } else if (parseFloat(riskFree.value) < 0 || parseFloat(riskFree.value) > validationConstants.MAX_RISK_FREE_RATE) {
                valid = false;
                feedback.innerHTML += `<div class="alert alert-warning"><strong>Risk-free Rate:</strong> Use decimal format (e.g., 0.02 for 2%). Values above ${validationConstants.MAX_RISK_FREE_RATE * 100}% seem unrealistic.</div>`;
            }

            // Validate simulations
            if (!numSims.value || isNaN(numSims.value) || numSims.value < validationConstants.MIN_SIMULATIONS || numSims.value > validationConstants.MAX_SIMULATIONS) {
                valid = false;
                feedback.innerHTML += `<div class="alert alert-danger"><strong>Simulations:</strong> Must be between ${validationConstants.MIN_SIMULATIONS} and ${validationConstants.MAX_SIMULATIONS:,}. Recommended: 1000-5000 for good results.</div>`;
            }

            // Validate tickers
            var tickerList = tickers.value.split(',').map(t => t.trim()).filter(t => t);
            if (tickerList.length < validationConstants.MIN_TICKERS) {
                valid = false;
                feedback.innerHTML += `<div class="alert alert-danger"><strong>Stock Tickers:</strong> Please enter at least ${validationConstants.MIN_TICKERS} Vietnamese stock symbols.</div>`;
            } else if (tickerList.length > validationConstants.MAX_TICKERS) {
                valid = false;
                feedback.innerHTML += `<div class="alert alert-warning"><strong>Stock Tickers:</strong> Too many stocks may slow optimization. Consider using ${validationConstants.MIN_TICKERS}-${validationConstants.MAX_TICKERS} stocks.</div>`;
            }

            // Validate dates
            if (startDate.value && endDate.value) {
                var start = new Date(startDate.value);
                var end = new Date(endDate.value);
                var daysDiff = (end - start) / (1000 * 60 * 60 * 24);
                
                if (start >= end) {
                    valid = false;
                    feedback.innerHTML += '<div class="alert alert-danger"><strong>Dates:</strong> End date must be after start date.</div>';
                } else if (daysDiff < validationConstants.MIN_HISTORICAL_DAYS) {
                    feedback.innerHTML += `<div class="alert alert-warning"><strong>Dates:</strong> Short time period (${Math.ceil(daysDiff)} days) may not provide reliable optimization results. Recommended: ${validationConstants.MIN_HISTORICAL_DAYS}+ days.</div>`;
                }
            }

            if (!valid) {
                e.preventDefault();
                // Scroll to feedback
                feedback.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return false;
            }

            // Enhanced loading state
            showLoadingState();
        });

        // Real-time input enhancements
        addInputEnhancements();
    }

    // Add print optimization for results page
    if (window.location.pathname.includes('results') || document.querySelector('#efficient-frontier')) {
        optimizeForPrint();
    }
});

function showLoadingState() {
    var btn = document.querySelector('button[type="submit"]');
    var btnText = btn.querySelector('.btn-text');
    var btnLoading = btn.querySelector('.btn-loading');
    
    if (btnText && btnLoading) {
        btnText.classList.add('d-none');
        btnLoading.classList.remove('d-none');
    } else {
        // Fallback for existing button structure
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Analyzing Portfolio...';
    }
    
    btn.disabled = true;
    
    // Add progress indication
    var progressContainer = document.createElement('div');
    progressContainer.id = 'optimization-progress';
    progressContainer.className = 'alert alert-info mt-3';
    progressContainer.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>
                <strong>Optimizing your portfolio...</strong><br>
                <small class="text-muted">This may take 10-30 seconds depending on the number of simulations.</small>
            </div>
        </div>
    `;
    
    var feedback = document.getElementById('form-feedback');
    feedback.appendChild(progressContainer);
}

function addInputEnhancements() {
    // Auto-format tickers
    var tickersInput = document.getElementById('tickers');
    if (tickersInput) {
        tickersInput.addEventListener('blur', function() {
            var cleaned = this.value
                .split(',')
                .map(ticker => ticker.trim().toUpperCase())
                .filter(ticker => ticker)
                .join(', ');
            this.value = cleaned;
        });

        // Add character counter for tickers
        tickersInput.addEventListener('input', function() {
            var tickerCount = this.value.split(',').map(t => t.trim()).filter(t => t).length;
            var counter = document.getElementById('ticker-counter');
            if (!counter) {
                counter = document.createElement('div');
                counter.id = 'ticker-counter';
                counter.className = 'form-text';
                this.parentNode.appendChild(counter);
            }
            counter.textContent = `${tickerCount} stock${tickerCount !== 1 ? 's' : ''} selected`;
            
            if (tickerCount < validationConstants.MIN_TICKERS) {
                counter.className = 'form-text text-danger';
            } else if (tickerCount > validationConstants.MAX_TICKERS) {
                counter.className = 'form-text text-warning';
            } else {
                counter.className = 'form-text text-success';
            }
        });
    }

    // Risk-free rate helper
    var riskFreeInput = document.getElementById('risk_free_rate');
    if (riskFreeInput) {
        riskFreeInput.addEventListener('focus', function() {
            var helper = document.getElementById('risk-free-helper');
            if (!helper) {
                helper = document.createElement('div');
                helper.id = 'risk-free-helper';
                helper.className = 'form-text text-info';
                helper.innerHTML = '<small>💡 Tip: Use decimal format (0.02 = 2%, 0.05 = 5%)</small>';
                this.parentNode.appendChild(helper);
            }
        });
    }

    // Date validation helper
    var startDate = document.getElementById('start_date');
    var endDate = document.getElementById('end_date');
    if (startDate && endDate) {
        function updateDateHelper() {
            var helper = document.getElementById('date-helper');
            if (startDate.value && endDate.value) {
                var start = new Date(startDate.value);
                var end = new Date(endDate.value);
                var daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
                
                if (!helper) {
                    helper = document.createElement('div');
                    helper.id = 'date-helper';
                    helper.className = 'form-text';
                    endDate.parentNode.appendChild(helper);
                }
                
                if (daysDiff > 0) {
                    helper.textContent = `Analysis period: ${daysDiff} days`;
                    helper.className = daysDiff < 30 ? 'form-text text-warning' : 'form-text text-success';
                } else {
                    helper.textContent = 'Invalid date range';
                    helper.className = 'form-text text-danger';
                }
            }
        }
        
        startDate.addEventListener('change', updateDateHelper);
        endDate.addEventListener('change', updateDateHelper);
    }
}

function optimizeForPrint() {
    // Ensure charts are properly sized for printing
    window.addEventListener('beforeprint', function() {
        if (typeof Plotly !== 'undefined') {
            var charts = ['efficient-frontier', 'allocation-pie'];
            charts.forEach(function(chartId) {
                var element = document.getElementById(chartId);
                if (element && element.data) {
                    Plotly.Plots.resize(element);
                }
            });
        }
    });
    
    // Add keyboard shortcut for printing
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            window.print();
        }
    });
}

// Utility function for smooth scrolling to elements
function scrollToElement(element, offset = 0) {
    if (element) {
        var elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }
}

// Enhanced error handling for network issues
window.addEventListener('error', function(e) {
    console.error('Application error:', e);
    var feedback = document.getElementById('form-feedback');
    if (feedback && !feedback.querySelector('.alert-danger')) {
        feedback.innerHTML += '<div class="alert alert-danger">An unexpected error occurred. Please refresh the page and try again.</div>';
    }
});

// Service worker registration for offline capability (future enhancement)
if ('serviceWorker' in navigator) {
    // Commented out - implement when PWA features are needed
    // navigator.serviceWorker.register('/sw.js');
}

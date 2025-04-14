/**
 * Investment Tracker - Main JS
 */

// Utility per formattare i numeri come valuta
function formatCurrency(value, currency = 'EUR') {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: currency
    }).format(value);
}

// Utility per formattare le percentuali
function formatPercentage(value) {
    return new Intl.NumberFormat('it-IT', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

// Utility per formattare le date
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('it-IT').format(date);
}

// Colori per i grafici
const chartColors = [
    '#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6',
    '#1abc9c', '#d35400', '#34495e', '#16a085', '#c0392b'
];

// Funzione per ottenere colori per i grafici in base al tema
function getChartColors(darkMode = false) {
    if (darkMode) {
        return [
            '#2980b9', '#27ae60', '#d35400', '#c0392b', '#8e44ad',
            '#16a085', '#e67e22', '#2c3e50', '#138d75', '#a93226'
        ];
    }
    return chartColors;
}

// Impostazioni comuni per i grafici
function getChartOptions(darkMode = false) {
    const textColor = darkMode ? '#f8f9fa' : '#333';
    const gridColor = darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    color: textColor
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            x: {
                ticks: {
                    color: textColor
                },
                grid: {
                    color: gridColor
                }
            },
            y: {
                ticks: {
                    color: textColor
                },
                grid: {
                    color: gridColor
                }
            }
        }
    };
}

// Funzione per creare un grafico a linee
function createLineChart(elementId, labels, datasets, options = {}) {
    const ctx = document.getElementById(elementId);
    
    if (!ctx) return null;
    
    const darkMode = document.body.getAttribute('data-theme') === 'dark';
    const chartColors = getChartColors(darkMode);
    
    // Imposta i colori per i dataset
    datasets.forEach((dataset, index) => {
        const colorIndex = index % chartColors.length;
        dataset.borderColor = chartColors[colorIndex];
        dataset.backgroundColor = chartColors[colorIndex] + '20'; // Con trasparenza
    });
    
    const chartOptions = {
        ...getChartOptions(darkMode),
        ...options
    };
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

// Funzione per creare un grafico a torta
function createPieChart(elementId, labels, data, options = {}) {
    const ctx = document.getElementById(elementId);
    
    if (!ctx) return null;
    
    const darkMode = document.body.getAttribute('data-theme') === 'dark';
    const chartColors = getChartColors(darkMode);
    
    // Limita i colori alla lunghezza dei dati
    const colors = chartColors.slice(0, data.length);
    
    const chartOptions = {
        ...getChartOptions(darkMode),
        ...options
    };
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors
            }]
        },
        options: chartOptions
    });
}

// Funzione per creare un grafico a barre
function createBarChart(elementId, labels, datasets, options = {}) {
    const ctx = document.getElementById(elementId);
    
    if (!ctx) return null;
    
    const darkMode = document.body.getAttribute('data-theme') === 'dark';
    const chartColors = getChartColors(darkMode);
    
    // Imposta i colori per i dataset
    datasets.forEach((dataset, index) => {
        const colorIndex = index % chartColors.length;
        dataset.backgroundColor = chartColors[colorIndex];
    });
    
    const chartOptions = {
        ...getChartOptions(darkMode),
        ...options
    };
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

// Listener per il cambio di tema (aggiorna i grafici)
document.addEventListener('DOMContentLoaded', function() {
    const toggleSwitch = document.querySelector('#darkModeToggle');
    if (toggleSwitch) {
        toggleSwitch.addEventListener('change', function() {
            // Trova tutti i grafici e li aggiorna
            Object.values(Chart.instances).forEach(chart => {
                chart.destroy();
            });
            
            // Esegue l'evento personalizzato per ricreare i grafici
            document.dispatchEvent(new CustomEvent('themeChanged'));
        });
    }
});

// Formatta automaticamente tutti gli elementi con classe 'format-currency'
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.format-currency').forEach(element => {
        const value = parseFloat(element.textContent);
        const currency = element.dataset.currency || 'EUR';
        if (!isNaN(value)) {
            element.textContent = formatCurrency(value, currency);
        }
    });
    
    document.querySelectorAll('.format-percentage').forEach(element => {
        const value = parseFloat(element.textContent);
        if (!isNaN(value)) {
            element.textContent = formatPercentage(value);
            
            // Aggiungi classi per colori in base al valore
            if (value > 0) {
                element.classList.add('performance-positive');
            } else if (value < 0) {
                element.classList.add('performance-negative');
            }
        }
    });
    
    document.querySelectorAll('.format-date').forEach(element => {
        element.textContent = formatDate(element.textContent);
    });
});

// Funzione per confermare l'eliminazione
function confirmDelete(message, formId) {
    if (confirm(message || 'Sei sicuro di voler eliminare?')) {
        document.getElementById(formId).submit();
    }
    return false;
}
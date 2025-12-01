// referrals-dashboard.js
document.addEventListener('DOMContentLoaded', function () {
  const labels = window.REF_LABELS || [];
  const data = window.REF_DATA || [];

  const ctx = document.getElementById('referralsMiniChart');
  if (!ctx) return;

  const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [{
        label: 'Conversions',
        data: data,
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 0,
        backgroundColor: 'rgba(14,165,233,0.12)',
        borderColor: 'rgba(14,165,233,0.95)'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false, // we use CSS height instead
        aspectRatio: 3,             // fallback if maintainAspectRatio becomes true
        layout: { padding: { top: 6, bottom: 6 } },
        scales: {
        x: { display: false },
        y: { display: true, beginAtZero: true, ticks: { precision: 0 } }
        },
        plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false }
        }
    }
});
});

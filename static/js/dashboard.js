// ==========================================
// INITIALIZATION & TIMEFRAME STATE TRACKING
// ==========================================
let businessChartInstance = null;
let currentSelectedRange = "today"; // Fallback default timeline state scope

document.addEventListener("DOMContentLoaded", () => {
    // Initial loading execution sequence
    fetchDashboardAnalytics(currentSelectedRange);
});

// ==========================================
// INTERACTIVE TIMEFRAME SWITCHER CAPABILITY
// ==========================================
async function changeTimeframe(selectedRangeType) {
    currentSelectedRange = selectedRangeType;
    
    // 1. Instantly update UI selection pill focus styles
    document.querySelectorAll(".time-pill").forEach(button => {
        button.className = "time-pill px-4 py-1.5 rounded-lg text-xs font-black uppercase tracking-wider transition-all duration-150 text-gray-600 hover:text-gray-900 ml-1";
    });
    
    const activeBtn = document.getElementById(`btn-${selectedRangeType}`);
    if (activeBtn) {
        activeBtn.className = "time-pill px-4 py-1.5 rounded-lg text-xs font-black uppercase tracking-wider transition-all duration-150 bg-blue-600 text-white shadow-sm";
    }

    // 2. Refresh dashboard analytics engine with chosen timeframe
    await fetchDashboardAnalytics(currentSelectedRange);
}

// ==========================================
// METRICS DATA ACQUISITION FROM BACKEND
// ==========================================
async function fetchDashboardAnalytics(rangeType) {
    try {
        const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
        
        // 🌟 CONNECTED: Directly targets your absolute endpoint /dashboard/metrics
        const response = await fetch(`${baseUrl}/dashboard/metrics?range_type=${rangeType}`); 
        const data = await response.json();

        if (response.ok) {
            updateExecutiveMetricsDOM(data);
            renderBusinessHealthChart(data);
            renderLowStockTable(data.low_stock_alerts);
        } else {
            console.error("Backend validation rejection:", data.detail);
        }
    } catch (error) {
        console.error("Dashboard engine failed to stream metric parameters:", error);
    }
}

// ==========================================
// DATA MAPPING INTO DOM NODES
// ==========================================
function updateExecutiveMetricsDOM(data) {
    document.getElementById("metric-liquid-cash").innerText = `₹${parseFloat(data.total_liquid_received || 0).toFixed(2)}`;
    document.getElementById("metric-market-debt").innerText = `₹${parseFloat(data.total_market_debt || 0).toFixed(2)}`;
    document.getElementById("metric-net-profit").innerText = `₹${parseFloat(data.overall_net_profit || 0).toFixed(2)}`;
    document.getElementById("metric-low-stock-count").innerText = data.low_stock_count || 0;
    document.getElementById("metric-sales-turnover").innerText = `Gross Sales Volume: ₹${parseFloat(data.total_sales_revenue || 0).toFixed(2)}`;
    document.getElementById("metric-purchase-spend").innerText = `₹${parseFloat(data.total_purchase_spend || 0).toFixed(2)}`;

    // Parse Top Moving Item
    const topProdDisplay = document.getElementById("top-product-display");
    const topProdUnits = document.getElementById("top-product-units");
    
    if (data.top_selling_product) {
        topProdDisplay.innerText = data.top_selling_product.name;
        topProdUnits.innerText = `${parseFloat(data.top_selling_product.total_quantity_sold).toFixed(0)} Units Distributed`;
    } else {
        topProdDisplay.innerText = "No Sales Logged Yet";
        topProdUnits.innerText = "0 Items Swiped Out";
    }
}

// ==========================================
// RENDER INTERACTIVE VISUAL CHART GENERATOR 
// ==========================================
function renderBusinessHealthChart(data) {
    const ctx = document.getElementById('business-health-chart');
    if (!ctx) return;

    // Destroy existing instance to prevent chart flicker bugs during timeframe switches
    if (businessChartInstance) {
        businessChartInstance.destroy();
    }

    businessChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Wholesale Spend', 'Liquid Cash Collected', 'Udhaar Balance Out', 'Net Clear Profits'],
            datasets: [{
                label: 'Value (₹)',
                data: [
                    parseFloat(data.total_purchase_spend || 0),
                    parseFloat(data.total_liquid_received || 0),
                    parseFloat(data.total_market_debt || 0),
                    parseFloat(data.overall_net_profit || 0)
                ],
                backgroundColor: [
                    'rgba(148, 163, 184, 0.8)',  // Slate Gray (Procurement Cost)
                    'rgba(52, 211, 153, 0.8)',   // Emerald Green (Liquid Cash)
                    'rgba(248, 113, 113, 0.8)',  // Crimson Red (Udhaar Outstanding)
                    'rgba(96, 165, 250, 0.8)'    // Bright Blue (Pure Operating Profits)
                ],
                borderColor: [
                    'rgb(148, 163, 184)',
                    'rgb(52, 211, 153)',
                    'rgb(248, 113, 113)',
                    'rgb(96, 165, 250)'
                ],
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { font: { family: 'monospace', weight: 'bold' } }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// ==========================================
// LOW STOCK ROSTER RENDER ENGINE
// ==========================================
function renderLowStockTable(alertsList) {
    const tbody = document.getElementById("low-stock-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!alertsList || alertsList.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-emerald-600 font-bold bg-emerald-50/50 text-xs"><i class="fa-solid fa-circle-check mr-1"></i> All stock balances healthy. No replenishment needed!</td></tr>`;
        return;
    }

    alertsList.forEach(item => {
        const row = document.createElement("tr");
        row.className = "border-b text-xs hover:bg-amber-50/20 transition";
        row.innerHTML = `
            <td class="p-3 font-mono font-bold text-gray-500 text-center">${item.id}</td>
            <td class="p-3 font-black text-gray-800">${item.name}</td>
            <td class="p-3 font-mono text-center text-red-600 font-black bg-red-50/50">${parseFloat(item.current_quantity).toFixed(0)} Left</td>
            <td class="p-3 text-center">
                <a href="products.html" class="inline-block bg-amber-600 hover:bg-amber-700 text-white font-black px-3 py-1 rounded-md text-[10px] uppercase tracking-wider shadow-sm transition">
                    <i class="fa-solid fa-truck-ramp-box mr-1"></i> Restock SKU
                </a>
            </td>
        `;
        tbody.appendChild(row);
    });
}
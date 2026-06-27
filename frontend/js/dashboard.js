
// ==========================================
// CORE CENTRAL RECONCILIATION STATE ENGINE
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // Format systemic regional timestamps on calendar headers
    const formatConfig = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const dateHeader = document.getElementById('current-date-display');
    if (dateHeader) {
        dateHeader.innerText = new Date().toLocaleDateString(undefined, formatConfig);
    }

    // Default system boot state queries the "today" timeline metric set
    fetchDashboardMetrics("today");

    // Dynamic dropdown range watcher activation link
    const rangeSelector = document.getElementById('dashboard-range-selector');
    if (rangeSelector) {
        rangeSelector.addEventListener('change', (e) => {
            fetchDashboardMetrics(e.target.value);
        });
    }
});

// Primary asynchronous data collection matrix wrapper
async function fetchDashboardMetrics(rangeType = "today") {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/metrics?range_type=${rangeType}`);
        if (!response.ok) {
            throw new Error(`Server returned status code: ${response.status}`);
        }

        const metricsData = await response.json();
        renderMetricCardsUI(metricsData);
        renderLowStockAlertsUI(metricsData.low_stock_alerts);
    } catch (error) {
        console.error("Dashboard engine compilation failure:", error);
    }
}

// ==========================================
// DOM UPDATE PIPELINES
// ==========================================
// ==========================================
// DOM UPDATE PIPELINES
// ==========================================
function renderMetricCardsUI(metrics) {
    if (!metrics) return;

    // ✅ TARGETS THE EXACT WORKING HTML IDs
    const salesRevenueElem = document.getElementById('sales-revenue-display');
    const liquidReceivedElem = document.getElementById('liquid-received-display');
    const outstandingUdhaarElem = document.getElementById('outstanding-udhaar-display');
    const purchaseSpendElem = document.getElementById('purchase-spend-display');
    const netProfitElem = document.getElementById('net-profit-display');

    // Parse values cleanly to safely handle the backend's string decimal representations
    if (salesRevenueElem) salesRevenueElem.innerText = `₹${parseFloat(metrics.total_sales_revenue || 0).toFixed(2)}`;
    if (liquidReceivedElem) liquidReceivedElem.innerText = `₹${parseFloat(metrics.total_liquid_received || 0).toFixed(2)}`;
    if (outstandingUdhaarElem) outstandingUdhaarElem.innerText = `₹${parseFloat(metrics.total_market_debt || 0).toFixed(2)}`;
    if (purchaseSpendElem) purchaseSpendElem.innerText = `₹${parseFloat(metrics.total_purchase_spend || 0).toFixed(2)}`;
    if (netProfitElem) netProfitElem.innerText = `₹${parseFloat(metrics.overall_net_profit || 0).toFixed(2)}`;

    // ✅ Renders Top Selling Product into the exact text element found in your html
    const topProductLabel = document.getElementById('top-selling-product-display');
    if (topProductLabel) {
        if (metrics.top_selling_product && metrics.top_selling_product.name) {
            const totalUnits = parseFloat(metrics.top_selling_product.total_quantity_sold || 0).toFixed(0);
            topProductLabel.innerText = `${metrics.top_selling_product.name} (${totalUnits} units)`;
        } else {
            topProductLabel.innerText = "No sales recorded";
        }
    }
}

function renderLowStockAlertsUI(deficitCluster) {
    const tableBodyContainer = document.getElementById('low-stock-table-body');
    if (!tableBodyContainer) return;
    
    tableBodyContainer.innerHTML = '';

    if (!deficitCluster || deficitCluster.length === 0) {
        tableBodyContainer.innerHTML = `
            <tr>
                <td colspan="3" class="p-4 text-center text-emerald-600 font-medium text-xs">
                    ✅ All inventory items are stocked safely above critical minimum thresholds.
                </td>
            </tr>`;
        return;
    }

    deficitCluster.forEach(product => {
        const quantityVal = parseFloat(product.current_quantity || 0);
        const isCriticalLevel = quantityVal <= 5.00;
        
        const tableRowHtml = `
            <tr class="hover:bg-gray-50/50 transition border-b">
                <td class="p-3">
                    <p class="font-bold text-gray-800 text-xs">${product.name}</p>
                </td>
                <td class="p-3 text-center font-mono font-bold text-xs text-gray-700">
                    ${quantityVal.toFixed(0)} units
                </td>
                <td class="p-3 text-center">
                    <span class="inline-block px-2 py-0.5 rounded text-[10px] font-black tracking-wider ${isCriticalLevel ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}">
                        ${isCriticalLevel ? 'CRITICAL LOW' : 'WARNING LIMIT'}
                    </span>
                </td>
            </tr>
        `;
        tableBodyContainer.insertAdjacentHTML('beforeend', tableRowHtml);
    });
}
requireAuth(["OWNER", "ADMIN"]);
renderShell("index.html", "Dashboard");

const content = document.getElementById("ab-page-content");
content.innerHTML = `
  <p style="font-size:0.82rem; color:var(--muted); margin-bottom:18px;">
    All-time totals across every sale, purchase and outstanding khata balance recorded so far.
  </p>
  <div id="stat-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px,1fr)); gap:14px; margin-bottom:24px;"></div>
  <div style="display:grid; grid-template-columns: 1.4fr 1fr; gap:18px;" id="lower-grid"></div>
`;

const statGrid = document.getElementById("stat-grid");
statGrid.innerHTML = Array.from({ length: 5 }).map(() => `<div class="stat-tile"><div class="skeleton" style="height:12px; width:60%; margin-bottom:10px;"></div><div class="skeleton" style="height:22px; width:80%;"></div></div>`).join("");

loadDashboard();

async function loadDashboard() {
  try {
    const d = await api("/api/dashboard/analytics");
    renderStats(d);
    renderLower(d);
  } catch (err) {
    toastError(err);
    statGrid.innerHTML = `<div class="card" style="padding:20px; grid-column:1/-1;">Could not load analytics. ${escapeHtml(err.message)}</div>`;
  }
}

function renderStats(d) {
  const tiles = [
    { label: "Total Sales Revenue", value: formatMoney(d.total_sales_revenue), icon: "fa-solid fa-receipt", accent: "var(--ink-navy)" },
    { label: "Cash / Liquid Received", value: formatMoney(d.total_liquid_received), icon: "fa-solid fa-coins", accent: "var(--settled-green)" },
    { label: "Outstanding Khata (Udhaar)", value: formatMoney(d.total_market_debt), icon: "fa-solid fa-book", accent: "var(--khata-red)" },
    { label: "Total Procurement Spend", value: formatMoney(d.total_purchase_spend), icon: "fa-solid fa-truck-ramp-box", accent: "var(--brass-gold)" },
    { label: "Net Profit", value: formatMoney(d.overall_net_profit), icon: "fa-solid fa-chart-line", accent: Number(d.overall_net_profit) >= 0 ? "var(--settled-green)" : "var(--khata-red)" },
  ];
  statGrid.innerHTML = tiles.map(t => `
    <div class="stat-tile">
      <div class="stat-label"><i class="${t.icon}" style="color:${t.accent}; margin-right:5px;"></i>${t.label}</div>
      <div class="stat-value" style="color:${t.accent}">${t.value}</div>
    </div>
  `).join("");
}

function renderLower(d) {
  const lower = document.getElementById("lower-grid");

  const alertsHtml = d.low_stock_alerts.length === 0
    ? `<div style="padding:20px; text-align:center; color:var(--muted); font-size:0.85rem;">
         <i class="fa-solid fa-circle-check" style="color:var(--settled-green); font-size:1.4rem; display:block; margin-bottom:6px;"></i>
         Every item is above the low-stock line.
       </div>`
    : `<table class="ledger-table"><thead><tr><th>Product</th><th>Brand</th><th style="text-align:right;">On hand</th></tr></thead><tbody>
        ${d.low_stock_alerts.map(a => `
          <tr>
            <td style="font-weight:600;">${escapeHtml(a.product_name)}</td>
            <td>${escapeHtml(a.brand)}</td>
            <td style="text-align:right;"><span class="badge badge-red">${formatQty(a.current_quantity)} left</span></td>
          </tr>
        `).join("")}
       </tbody></table>`;

  const top = d.top_selling_product;

  lower.innerHTML = `
    <div class="card">
      <div style="padding:16px 18px; border-bottom:1px solid #EEE9DB; display:flex; align-items:center; justify-content:space-between;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); font-size:1rem;">
          <i class="fa-solid fa-triangle-exclamation" style="color:var(--khata-red); margin-right:6px;"></i>Low Stock Alerts
        </h3>
        <span class="badge badge-red">${d.low_stock_count} item${d.low_stock_count === 1 ? "" : "s"}</span>
      </div>
      ${alertsHtml}
    </div>

    <div class="card" style="padding:18px;">
      <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); font-size:1rem; margin-bottom:12px;">
        <i class="fa-solid fa-medal" style="color:var(--brass-gold); margin-right:6px;"></i>Top Selling Product
      </h3>
      ${top ? `
        <div style="font-weight:700; font-size:1.05rem; color:var(--ink-navy);">${escapeHtml(top.name)}</div>
        <div style="font-size:0.82rem; color:var(--muted); margin:2px 0 10px;">${escapeHtml(top.brand)} · ${escapeHtml(top.unit_type)}</div>
        <div style="display:flex; justify-content:space-between; font-family:'IBM Plex Mono',monospace; font-size:0.86rem;">
          <span>Selling price</span><span>${formatMoney(top.selling_price)}</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-family:'IBM Plex Mono',monospace; font-size:0.86rem;">
          <span>In stock</span><span>${formatQty(top.current_quantity)}</span>
        </div>
      ` : `<div style="color:var(--muted); font-size:0.85rem;">No sales recorded yet.</div>`}
    </div>
  `;
}

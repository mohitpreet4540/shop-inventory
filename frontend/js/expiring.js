requireAuth(["OWNER", "ADMIN", "CASHIER"]);
renderShell("expiring.html", "Expiring Stock");

const content = document.getElementById("ab-page-content");
content.innerHTML = `
  <div style="display:flex; gap:10px; align-items:flex-end; margin-bottom:16px; flex-wrap:wrap;">
    <div style="min-width:200px;">
      <label class="field-label">Show batches expiring within</label>
      <select class="input" id="days-select">
        <option value="3">3 days</option>
        <option value="7" selected>7 days</option>
        <option value="14">14 days</option>
        <option value="30">30 days</option>
        <option value="90">90 days</option>
      </select>
    </div>
    <button class="btn btn-outline" onclick="loadExpiring()"><i class="fa-solid fa-filter"></i> Apply</button>
  </div>

  <div id="expiring-grid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px,1fr)); gap:14px;"></div>
`;

loadExpiring();

async function loadExpiring() {
  const grid = document.getElementById("expiring-grid");
  grid.innerHTML = `<div class="skeleton" style="height:100px;"></div><div class="skeleton" style="height:100px;"></div><div class="skeleton" style="height:100px;"></div>`;
  const days = document.getElementById("days-select").value;

  try {
    const alerts = await api(`/api/reports/expiring-soon?days=${days}`);
    renderExpiring(alerts);
  } catch (err) {
    toastError(err);
    grid.innerHTML = `<div class="card" style="padding:20px; text-align:center; color:var(--muted); grid-column:1/-1;">Could not load expiring stock.</div>`;
  }
}

function renderExpiring(alerts) {
  const grid = document.getElementById("expiring-grid");
  if (alerts.length === 0) {
    grid.innerHTML = `<div class="card" style="padding:30px; text-align:center; color:var(--muted); grid-column:1/-1;">
      <i class="fa-solid fa-circle-check" style="color:var(--settled-green); font-size:1.4rem; display:block; margin-bottom:6px;"></i>
      Nothing is expiring in this window.
    </div>`;
    return;
  }

  grid.innerHTML = alerts.map(a => {
    const expired = a.days_until_expiry < 0;
    const urgent = !expired && a.days_until_expiry <= 3;
    const accent = expired ? "var(--khata-red)" : urgent ? "var(--brass-gold)" : "var(--ink-navy)";
    const badgeCls = expired ? "badge-red" : urgent ? "badge-gold" : "badge-navy";
    const label = expired
      ? `Expired ${Math.abs(a.days_until_expiry)}d ago`
      : a.days_until_expiry === 0 ? "Expires today" : `${a.days_until_expiry}d left`;

    return `
      <div class="ledger-card" style="padding:16px 18px; border-left:4px solid ${accent};">
        <div style="font-family:'Roboto Slab',serif; font-weight:700; color:var(--ink-navy);">${escapeHtml(a.product_name)}</div>
        <div style="font-size:0.78rem; color:var(--muted); margin:4px 0 10px;">Batch #${a.batch_id}</div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span class="badge ${badgeCls}">${label}</span>
          <span class="font-mono" style="font-weight:600;">${formatQty(a.quantity_remaining)} left</span>
        </div>
        <div style="font-size:0.75rem; color:var(--muted); margin-top:8px;">Expires ${formatDate(a.expiry_date)}</div>
      </div>
    `;
  }).join("");
}

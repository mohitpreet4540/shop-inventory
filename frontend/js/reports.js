requireAuth(["OWNER", "ADMIN"]);
renderShell("reports.html", "Stock Ledger");

const content = document.getElementById("ab-page-content");
content.innerHTML = `
  <div style="display:flex; gap:10px; align-items:flex-end; margin-bottom:16px; flex-wrap:wrap;">
    <div style="min-width:220px;">
      <label class="field-label">Product</label>
      <select class="input" id="rp-product"><option value="">All products</option></select>
    </div>
    <div style="min-width:180px;">
      <label class="field-label">Transaction type</label>
      <select class="input" id="rp-type">
        <option value="">All types</option>
        <option value="INITIAL_STOCK">Initial stock</option>
        <option value="RESTOCK">Restock</option>
        <option value="SALE">Sale</option>
        <option value="PRICE_UPDATE">Price update</option>
      </select>
    </div>
    <button class="btn btn-outline" onclick="loadLedger()"><i class="fa-solid fa-filter"></i> Apply</button>
  </div>

  <div class="card" style="overflow-x:auto;">
    <table class="ledger-table">
      <thead><tr><th>Date</th><th>Product</th><th>Type</th><th style="text-align:right;">Qty change</th><th style="text-align:right;">Unit cost</th><th style="text-align:right;">Total cost</th><th>Notes</th></tr></thead>
      <tbody id="ledger-tbody"></tbody>
    </table>
  </div>
`;

loadProductOptions();
loadLedger();

async function loadProductOptions() {
  try {
    const products = await api("/api/products/");
    document.getElementById("rp-product").innerHTML = `<option value="">All products</option>` +
      products.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("");
  } catch (err) {
    toastError(err);
  }
}

async function loadLedger() {
  const tbody = document.getElementById("ledger-tbody");
  tbody.innerHTML = `<tr><td colspan="7"><div class="skeleton" style="height:16px; margin:8px 0;"></div></td></tr>`.repeat(5);

  const params = new URLSearchParams();
  const productId = document.getElementById("rp-product").value;
  const type = document.getElementById("rp-type").value;
  if (productId) params.set("product_id", productId);
  if (type) params.set("transaction_type", type);

  try {
    const rows = await api(`/api/reports/stock-ledger?${params.toString()}`);
    renderLedger(rows);
  } catch (err) {
    toastError(err);
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--muted); padding:20px;">Could not load the stock ledger.</td></tr>`;
  }
}

const TYPE_BADGE = {
  SALE: "badge-red",
  RESTOCK: "badge-green",
  INITIAL_STOCK: "badge-navy",
  PRICE_UPDATE: "badge-gold",
};

function renderLedger(rows) {
  const tbody = document.getElementById("ledger-tbody");
  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--muted); padding:24px;">No transactions match these filters.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(tx => `
    <tr>
      <td style="font-size:0.8rem;">${formatDateTime(tx.timestamp)}</td>
      <td style="font-weight:600;">${escapeHtml(tx.product_name)}</td>
      <td><span class="badge ${TYPE_BADGE[tx.type] || "badge-gray"}">${escapeHtml(tx.type)}</span></td>
      <td style="text-align:right;" class="font-mono">${Number(tx.quantity_changed) > 0 ? "+" : ""}${formatQty(tx.quantity_changed)}</td>
      <td style="text-align:right;" class="font-mono">${formatMoney(tx.unit_cost)}</td>
      <td style="text-align:right;" class="font-mono">${formatMoney(tx.total_cost)}</td>
      <td style="font-size:0.8rem; color:var(--muted);">${escapeHtml(tx.notes || "—")}</td>
    </tr>
  `).join("");
}

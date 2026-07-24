requireAuth(["OWNER", "ADMIN", "CASHIER"]);
renderShell("customers.html", "Customer Khata");

const canManageCredit = Session.hasRole("OWNER", "ADMIN");
const content = document.getElementById("ab-page-content");

content.innerHTML = `
  <div style="display:flex; gap:10px; align-items:flex-end; margin-bottom:16px; flex-wrap:wrap;">
    <div style="flex:1; min-width:220px;">
      <label class="field-label">Search</label>
      <input class="input" id="cust-search" placeholder="Search by name or phone…">
    </div>
    <button class="btn btn-outline" onclick="loadCustomers()"><i class="fa-solid fa-magnifying-glass"></i> Search</button>
    <button class="btn btn-primary" onclick="openNewCustomerModal()"><i class="fa-solid fa-plus"></i> New customer</button>
  </div>

  <div id="customers-grid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px,1fr)); gap:14px;"></div>

  <!-- New customer modal -->
  <div id="new-customer-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:400px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:12px;">New customer</h3>
        <form id="new-customer-form" style="display:flex; flex-direction:column; gap:10px;">
          <div><label class="field-label">Name</label><input class="input" id="nc-name" required></div>
          <div><label class="field-label">Phone (optional)</label><input class="input" id="nc-phone"></div>
          <div><label class="field-label">Credit limit (optional — leave blank for no limit)</label><input class="input" type="number" min="0" step="0.01" id="nc-limit"></div>
          <div>
            <label class="field-label">If limit is exceeded</label>
            <select class="input" id="nc-block-mode">
              <option value="WARN">Warn but still allow</option>
              <option value="BLOCK">Block the sale</option>
            </select>
          </div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="document.getElementById('new-customer-modal').style.display='none'">Cancel</button>
            <button type="submit" class="btn btn-primary" style="flex:1; justify-content:center;">Add customer</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Repay modal -->
  <div id="repay-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:380px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:4px;">Record repayment</h3>
        <p id="repay-context" style="font-size:0.8rem; color:var(--muted); margin-bottom:12px;"></p>
        <form id="repay-form" style="display:flex; flex-direction:column; gap:10px;">
          <input type="hidden" id="repay-customer-id">
          <div><label class="field-label">Amount</label><input class="input" type="number" min="0.01" step="0.01" id="repay-amount" required></div>
          <div>
            <label class="field-label">Method</label>
            <select class="input" id="repay-method"><option value="CASH">Cash</option><option value="ONLINE">Online</option></select>
          </div>
          <div><label class="field-label">Notes (optional)</label><input class="input" id="repay-notes"></div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="document.getElementById('repay-modal').style.display='none'">Cancel</button>
            <button type="submit" class="btn btn-gold" style="flex:1; justify-content:center;">Record</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Credit settings modal -->
  <div id="credit-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:380px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:12px;">Credit settings</h3>
        <form id="credit-form" style="display:flex; flex-direction:column; gap:10px;">
          <input type="hidden" id="cs-customer-id">
          <div><label class="field-label">Name</label><input class="input" id="cs-name" required></div>
          <div><label class="field-label">Phone</label><input class="input" id="cs-phone"></div>
          <div><label class="field-label">Credit limit (leave blank for no limit)</label><input class="input" type="number" min="0" step="0.01" id="cs-limit"></div>
          <div>
            <label class="field-label">If limit is exceeded</label>
            <select class="input" id="cs-block-mode">
              <option value="WARN">Warn but still allow</option>
              <option value="BLOCK">Block the sale</option>
            </select>
          </div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="document.getElementById('credit-modal').style.display='none'">Cancel</button>
            <button type="submit" class="btn btn-gold" style="flex:1; justify-content:center;">Save</button>
          </div>
        </form>
      </div>
    </div>
  </div>
`;

let customers = [];

document.getElementById("cust-search").addEventListener("keydown", e => { if (e.key === "Enter") loadCustomers(); });

loadCustomers();

async function loadCustomers() {
  const grid = document.getElementById("customers-grid");
  grid.innerHTML = `<div class="skeleton" style="height:110px;"></div><div class="skeleton" style="height:110px;"></div><div class="skeleton" style="height:110px;"></div>`;
  const q = document.getElementById("cust-search").value.trim();
  try {
    customers = await api(`/api/customers/?${q ? `search=${encodeURIComponent(q)}` : ""}`);
    renderCustomers();
  } catch (err) {
    toastError(err);
    grid.innerHTML = `<div class="card" style="padding:20px; text-align:center; color:var(--muted); grid-column:1/-1;">Could not load customers.</div>`;
  }
}

function renderCustomers() {
  const grid = document.getElementById("customers-grid");
  if (customers.length === 0) {
    grid.innerHTML = `<div class="card" style="padding:30px; text-align:center; color:var(--muted); grid-column:1/-1;">No customers found.</div>`;
    return;
  }
  grid.innerHTML = customers.map(c => {
    const due = Number(c.total_credit_due);
    const overLimit = c.credit_limit !== null && due > Number(c.credit_limit);
    return `
      <div class="ledger-card" style="padding:16px 18px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <div style="font-family:'Roboto Slab',serif; font-weight:700; color:var(--ink-navy);">${escapeHtml(c.name)}</div>
            <div style="font-size:0.76rem; color:var(--muted);">${escapeHtml(c.phone || "no phone on file")}</div>
          </div>
          ${overLimit ? `<span class="stamp" style="color:var(--khata-red);">Over limit</span>` : ""}
        </div>
        <div style="margin-top:12px; display:flex; justify-content:space-between; align-items:baseline;">
          <span style="font-size:0.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.06em;">Balance due</span>
          <span class="font-mono" style="font-weight:700; font-size:1.1rem; color:${due > 0 ? "var(--khata-red)" : "var(--settled-green)"};">${formatMoney(due)}</span>
        </div>
        ${c.credit_limit !== null ? `<div style="font-size:0.74rem; color:var(--muted); margin-top:2px;">Limit ${formatMoney(c.credit_limit)} · ${c.credit_block_mode === "BLOCK" ? "hard stop" : "warns only"}</div>` : `<div style="font-size:0.74rem; color:var(--muted); margin-top:2px;">No credit limit set</div>`}
        <div style="display:flex; gap:6px; margin-top:12px;">
          <button class="btn btn-outline btn-sm" style="flex:1; justify-content:center;" onclick="openRepayModal(${c.id})" ${due <= 0 ? "disabled" : ""}>
            <i class="fa-solid fa-hand-holding-dollar"></i> Repay
          </button>
          ${canManageCredit ? `<button class="btn btn-outline btn-sm" style="flex:1; justify-content:center;" onclick="openCreditModal(${c.id})">
            <i class="fa-solid fa-sliders"></i> Settings
          </button>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function openNewCustomerModal() {
  document.getElementById("new-customer-form").reset();
  document.getElementById("new-customer-modal").style.display = "flex";
}

document.getElementById("new-customer-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/customers/", {
      method: "POST",
      body: {
        name: document.getElementById("nc-name").value.trim(),
        phone: document.getElementById("nc-phone").value.trim() || null,
        credit_limit: document.getElementById("nc-limit").value ? Number(document.getElementById("nc-limit").value) : null,
        credit_block_mode: document.getElementById("nc-block-mode").value,
      },
    });
    toast("Customer added.", "success");
    document.getElementById("new-customer-modal").style.display = "none";
    loadCustomers();
  } catch (err) {
    toastError(err);
  }
});

function openRepayModal(id) {
  const c = customers.find(x => x.id === id);
  document.getElementById("repay-form").reset();
  document.getElementById("repay-customer-id").value = id;
  document.getElementById("repay-context").textContent = `${c.name} owes ${formatMoney(c.total_credit_due)}.`;
  document.getElementById("repay-modal").style.display = "flex";
}

document.getElementById("repay-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("repay-customer-id").value;
  try {
    const result = await api(`/api/customers/${id}/repay`, {
      method: "POST",
      body: {
        amount_paid: Number(document.getElementById("repay-amount").value),
        payment_method: document.getElementById("repay-method").value,
        notes: document.getElementById("repay-notes").value.trim() || null,
      },
    });
    toast(`Repayment recorded — remaining due ${formatMoney(result.remaining_credit_due)}.`, "success");
    document.getElementById("repay-modal").style.display = "none";
    loadCustomers();
  } catch (err) {
    toastError(err);
  }
});

function openCreditModal(id) {
  const c = customers.find(x => x.id === id);
  document.getElementById("cs-customer-id").value = id;
  document.getElementById("cs-name").value = c.name;
  document.getElementById("cs-phone").value = c.phone || "";
  document.getElementById("cs-limit").value = c.credit_limit !== null ? c.credit_limit : "";
  document.getElementById("cs-block-mode").value = c.credit_block_mode;
  document.getElementById("credit-modal").style.display = "flex";
}

document.getElementById("credit-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("cs-customer-id").value;
  try {
    await api(`/api/customers/${id}/credit-settings`, {
      method: "PATCH",
      body: {
        name: document.getElementById("cs-name").value.trim(),
        phone: document.getElementById("cs-phone").value.trim() || null,
        credit_limit: document.getElementById("cs-limit").value ? Number(document.getElementById("cs-limit").value) : null,
        credit_block_mode: document.getElementById("cs-block-mode").value,
      },
    });
    toast("Credit settings saved.", "success");
    document.getElementById("credit-modal").style.display = "none";
    loadCustomers();
  } catch (err) {
    toastError(err);
  }
});

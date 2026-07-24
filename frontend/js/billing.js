requireAuth(["OWNER", "ADMIN", "CASHIER"]);
renderShell("billing.html", "Billing Counter");

const content = document.getElementById("ab-page-content");
content.innerHTML = `
  <div style="display:grid; grid-template-columns: 1.5fr 1fr; gap:18px; align-items:start;">

    <div class="card" style="padding:18px;">
      <label class="field-label">Scan barcode or search by name / brand</label>
      <div style="position:relative;">
        <input class="input" id="search-box" placeholder="Type a product name, brand, or scan a barcode…" autofocus autocomplete="off">
        <div id="search-results" style="display:none; position:absolute; top:100%; left:0; right:0; background:#fff; border:1px solid #E7E3D8; border-radius:10px; margin-top:6px; box-shadow:0 12px 28px rgba(0,0,0,0.1); max-height:340px; overflow-y:auto; z-index:20;"></div>
      </div>
      <p style="font-size:0.72rem; color:var(--muted); margin-top:6px;">Press Enter after a full barcode to add it straight to the cart.</p>

      <div class="divider" style="margin:16px 0;"></div>
      <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); font-size:0.95rem; margin-bottom:10px;">Cart</h3>
      <div id="cart-table-wrap"></div>
    </div>

    <div>
      <div class="receipt">
        <div class="receipt-perf"></div>
        <div class="receipt-body">
          <div style="text-align:center; margin:6px 0 10px;">
            <div class="font-slab" style="font-weight:700; color:var(--ink-navy);">APNA BAZAR</div>
            <div style="font-size:0.7rem; color:var(--muted);">Counter Receipt</div>
          </div>
          <div id="receipt-lines"></div>
          <div style="display:flex; justify-content:space-between; margin-top:10px;">
            <span class="receipt-total">Total</span>
            <span class="receipt-total" id="receipt-total">₹0.00</span>
          </div>
        </div>
      </div>

      <div class="card" style="padding:16px; margin-top:14px;">
        <label class="field-label">Payment method</label>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;" id="payment-method-group">
          <button type="button" class="btn btn-outline pm-btn" data-pm="CASH">Cash</button>
          <button type="button" class="btn btn-outline pm-btn" data-pm="ONLINE">Online</button>
          <button type="button" class="btn btn-outline pm-btn" data-pm="CREDIT">Credit (Udhaar)</button>
          <button type="button" class="btn btn-outline pm-btn" data-pm="PARTIAL">Partial</button>
        </div>

        <label class="field-label">Amount paid now</label>
        <input class="input" type="number" id="amount-paid" min="0" step="0.01" value="0">

        <div id="customer-block" style="display:none; margin-top:12px;">
          <label class="field-label">Customer (required for khata / partial dues)</label>
          <div style="position:relative;">
            <input class="input" id="customer-search" placeholder="Search customer by name or phone…" autocomplete="off">
            <div id="customer-results" style="display:none; position:absolute; top:100%; left:0; right:0; background:#fff; border:1px solid #E7E3D8; border-radius:10px; margin-top:6px; box-shadow:0 12px 28px rgba(0,0,0,0.1); max-height:220px; overflow-y:auto; z-index:20;"></div>
          </div>
          <div id="selected-customer" style="display:none; margin-top:8px; padding:8px 10px; background:var(--ledger-cream); border-radius:8px; font-size:0.82rem;"></div>
          <button type="button" class="btn btn-outline btn-sm" style="margin-top:8px;" onclick="openQuickAddCustomer()"><i class="fa-solid fa-plus"></i> New customer</button>
        </div>

        <button class="btn btn-primary" style="width:100%; justify-content:center; margin-top:16px; padding:11px;" id="checkout-btn" onclick="submitOrder()">
          <i class="fa-solid fa-receipt"></i> Complete Sale
        </button>
      </div>
    </div>
  </div>

  <!-- quick add customer modal -->
  <div id="quick-customer-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:400px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:12px;">New customer</h3>
        <form id="quick-customer-form" style="display:flex; flex-direction:column; gap:10px;">
          <div><label class="field-label">Name</label><input class="input" id="qc-name" required></div>
          <div><label class="field-label">Phone (optional)</label><input class="input" id="qc-phone"></div>
          <div><label class="field-label">Credit limit (optional — leave blank for no limit)</label><input class="input" type="number" min="0" step="0.01" id="qc-limit"></div>
          <div>
            <label class="field-label">If limit is exceeded</label>
            <select class="input" id="qc-block-mode">
              <option value="WARN">Warn but still allow</option>
              <option value="BLOCK">Block the sale</option>
            </select>
          </div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="document.getElementById('quick-customer-modal').style.display='none'">Cancel</button>
            <button type="submit" class="btn btn-gold" style="flex:1; justify-content:center;">Add &amp; select</button>
          </div>
        </form>
      </div>
    </div>
  </div>
`;

// ---------- State ----------
let cart = []; // { product_id, name, brand, unit_type, unit_price, quantity, available_qty }
let paymentMethod = "CASH";
let selectedCustomer = null; // { id, name, phone, total_credit_due, credit_limit, credit_block_mode }

const searchBox = document.getElementById("search-box");
const searchResults = document.getElementById("search-results");
const customerSearch = document.getElementById("customer-search");
const customerResults = document.getElementById("customer-results");

setPaymentMethod("CASH");
renderCart();

// ---------- Product search ----------
let searchTimer = null;
searchBox.addEventListener("input", () => {
  clearTimeout(searchTimer);
  const q = searchBox.value.trim();
  if (!q) { searchResults.style.display = "none"; return; }
  searchTimer = setTimeout(() => runProductSearch(q), 220);
});

searchBox.addEventListener("keydown", async (e) => {
  if (e.key !== "Enter") return;
  const q = searchBox.value.trim();
  if (!q) return;
  e.preventDefault();
  try {
    const product = await api(`/api/products/lookup/${encodeURIComponent(q)}`);
    addToCart(product);
    searchBox.value = "";
    searchResults.style.display = "none";
  } catch (err) {
    // Not an exact barcode match — fall back to a name search
    runProductSearch(q);
  }
});

document.addEventListener("click", (e) => {
  if (!searchResults.contains(e.target) && e.target !== searchBox) searchResults.style.display = "none";
  if (!customerResults.contains(e.target) && e.target !== customerSearch) customerResults.style.display = "none";
});

async function runProductSearch(q) {
  try {
    const results = await api(`/api/search/products?q=${encodeURIComponent(q)}`);
    if (results.length === 0) {
      searchResults.innerHTML = `<div style="padding:14px; font-size:0.82rem; color:var(--muted);">No matching products.</div>`;
    } else {
      searchResults.innerHTML = results.map(p => `
        <div class="search-item" data-id="${p.id}" style="padding:10px 14px; cursor:pointer; border-bottom:1px solid #F0EDE3; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:600; font-size:0.87rem;">${escapeHtml(p.name)}</div>
            <div style="font-size:0.74rem; color:var(--muted);">${escapeHtml(p.brand)} · ${formatQty(p.current_quantity)} ${escapeHtml(p.unit_type)} in stock</div>
          </div>
          <div class="font-mono" style="font-weight:600;">${formatMoney(p.selling_price)}</div>
        </div>
      `).join("");
      searchResults.querySelectorAll(".search-item").forEach(el => {
        el.addEventListener("mouseenter", () => el.style.background = "#FAF8F2");
        el.addEventListener("mouseleave", () => el.style.background = "#fff");
        el.addEventListener("click", () => {
          const product = results.find(r => r.id === Number(el.dataset.id));
          addToCart(product);
          searchBox.value = "";
          searchResults.style.display = "none";
          searchBox.focus();
        });
      });
    }
    searchResults.style.display = "block";
  } catch (err) {
    toastError(err);
  }
}

function addToCart(product) {
  if (Number(product.current_quantity) <= 0) {
    toast(`${product.name} is out of stock.`, "error");
    return;
  }
  const existing = cart.find(c => c.product_id === product.id);
  if (existing) {
    if (existing.quantity + 1 > Number(product.current_quantity)) {
      toast(`Only ${formatQty(product.current_quantity)} of ${product.name} available.`, "error");
      return;
    }
    existing.quantity += 1;
  } else {
    cart.push({
      product_id: product.id,
      name: product.name,
      brand: product.brand,
      unit_type: product.unit_type,
      unit_price: Number(product.selling_price),
      quantity: 1,
      available_qty: Number(product.current_quantity),
    });
  }
  renderCart();
}

function updateQty(productId, qty) {
  const line = cart.find(c => c.product_id === productId);
  if (!line) return;
  const n = Number(qty);
  if (!n || n <= 0) { removeLine(productId); return; }
  if (n > line.available_qty) {
    toast(`Only ${formatQty(line.available_qty)} of ${line.name} available.`, "error");
    line.quantity = line.available_qty;
  } else {
    line.quantity = n;
  }
  renderCart();
}

function removeLine(productId) {
  cart = cart.filter(c => c.product_id !== productId);
  renderCart();
}

function cartTotal() {
  return cart.reduce((sum, c) => sum + c.unit_price * c.quantity, 0);
}

function renderCart() {
  const wrap = document.getElementById("cart-table-wrap");
  if (cart.length === 0) {
    wrap.innerHTML = `<div style="text-align:center; padding:30px 10px; color:var(--muted); font-size:0.85rem;">
      <i class="fa-solid fa-cart-shopping" style="font-size:1.6rem; display:block; margin-bottom:8px; color:#D9D3C2;"></i>
      Cart is empty — search or scan a product to begin.
    </div>`;
  } else {
    wrap.innerHTML = `
      <table class="ledger-table">
        <thead><tr><th>Item</th><th style="width:90px;">Qty</th><th style="text-align:right;">Price</th><th style="text-align:right;">Line total</th><th></th></tr></thead>
        <tbody>
          ${cart.map(c => `
            <tr>
              <td><div style="font-weight:600;">${escapeHtml(c.name)}</div><div style="font-size:0.72rem; color:var(--muted);">${escapeHtml(c.brand)}</div></td>
              <td><input class="input" type="number" min="0.01" step="0.01" value="${c.quantity}" style="padding:5px 8px;" onchange="updateQty(${c.product_id}, this.value)"></td>
              <td style="text-align:right;" class="font-mono">${formatMoney(c.unit_price)}</td>
              <td style="text-align:right;" class="font-mono">${formatMoney(c.unit_price * c.quantity)}</td>
              <td style="text-align:right;"><button class="btn btn-outline btn-sm" onclick="removeLine(${c.product_id})"><i class="fa-solid fa-trash"></i></button></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  const receiptLines = document.getElementById("receipt-lines");
  receiptLines.innerHTML = cart.length === 0
    ? `<div style="text-align:center; color:var(--muted); font-size:0.78rem; padding:10px 0;">No items yet</div>`
    : cart.map(c => `
        <div class="receipt-row">
          <span>${escapeHtml(c.name).slice(0, 18)} × ${formatQty(c.quantity)}</span>
          <span>${formatMoney(c.unit_price * c.quantity)}</span>
        </div>
      `).join("");

  document.getElementById("receipt-total").textContent = formatMoney(cartTotal());

  const paidInput = document.getElementById("amount-paid");
  if (paymentMethod === "CASH" || paymentMethod === "ONLINE") {
    paidInput.value = cartTotal().toFixed(2);
  }
  syncCustomerVisibility();
}

// ---------- Payment method ----------
document.querySelectorAll(".pm-btn").forEach(btn => {
  btn.addEventListener("click", () => setPaymentMethod(btn.dataset.pm));
});

function setPaymentMethod(pm) {
  paymentMethod = pm;
  document.querySelectorAll(".pm-btn").forEach(b => {
    const active = b.dataset.pm === pm;
    b.classList.toggle("btn-primary", active);
    b.classList.toggle("btn-outline", !active);
  });
  const paidInput = document.getElementById("amount-paid");
  if (pm === "CREDIT") paidInput.value = "0";
  if (pm === "CASH" || pm === "ONLINE") paidInput.value = cartTotal().toFixed(2);
  syncCustomerVisibility();
}

document.getElementById("amount-paid").addEventListener("input", syncCustomerVisibility);

function syncCustomerVisibility() {
  const paid = Number(document.getElementById("amount-paid").value || 0);
  const pending = cartTotal() - paid;
  document.getElementById("customer-block").style.display = pending > 0.004 ? "block" : "none";
}

// ---------- Customer search ----------
let custTimer = null;
customerSearch.addEventListener("input", () => {
  clearTimeout(custTimer);
  const q = customerSearch.value.trim();
  if (!q) { customerResults.style.display = "none"; return; }
  custTimer = setTimeout(() => runCustomerSearch(q), 220);
});

async function runCustomerSearch(q) {
  try {
    const results = await api(`/api/customers/?search=${encodeURIComponent(q)}`);
    customerResults.innerHTML = results.length === 0
      ? `<div style="padding:12px; font-size:0.82rem; color:var(--muted);">No matching customers.</div>`
      : results.map(c => `
          <div class="cust-item" data-id="${c.id}" style="padding:9px 12px; cursor:pointer; border-bottom:1px solid #F0EDE3;">
            <div style="font-weight:600; font-size:0.85rem;">${escapeHtml(c.name)}</div>
            <div style="font-size:0.72rem; color:var(--muted);">${escapeHtml(c.phone || "no phone")} · Due ${formatMoney(c.total_credit_due)}</div>
          </div>
        `).join("");
    customerResults.querySelectorAll(".cust-item").forEach(el => {
      el.addEventListener("click", () => {
        const c = results.find(r => r.id === Number(el.dataset.id));
        selectCustomer(c);
        customerSearch.value = "";
        customerResults.style.display = "none";
      });
    });
    customerResults.style.display = "block";
  } catch (err) {
    toastError(err);
  }
}

function selectCustomer(c) {
  selectedCustomer = c;
  const box = document.getElementById("selected-customer");
  box.style.display = "block";
  box.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <div>
        <div style="font-weight:700;">${escapeHtml(c.name)}</div>
        <div style="font-size:0.74rem; color:var(--muted);">${escapeHtml(c.phone || "no phone")} · Existing due ${formatMoney(c.total_credit_due)}${c.credit_limit ? ` / limit ${formatMoney(c.credit_limit)}` : ""}</div>
      </div>
      <button type="button" onclick="selectedCustomer=null; document.getElementById('selected-customer').style.display='none';" style="background:none; border:none; color:var(--khata-red); cursor:pointer;"><i class="fa-solid fa-xmark"></i></button>
    </div>
  `;
}

// ---------- Quick add customer ----------
function openQuickAddCustomer() {
  document.getElementById("quick-customer-form").reset();
  document.getElementById("quick-customer-modal").style.display = "flex";
}

document.getElementById("quick-customer-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("qc-name").value.trim();
  const phone = document.getElementById("qc-phone").value.trim();
  const limit = document.getElementById("qc-limit").value;
  const blockMode = document.getElementById("qc-block-mode").value;

  try {
    const c = await api("/api/customers/", {
      method: "POST",
      body: {
        name,
        phone: phone || null,
        credit_limit: limit ? Number(limit) : null,
        credit_block_mode: blockMode,
      },
    });
    selectCustomer(c);
    document.getElementById("quick-customer-modal").style.display = "none";
    toast("Customer added.", "success");
  } catch (err) {
    toastError(err);
  }
});

// ---------- Checkout ----------
async function submitOrder() {
  if (cart.length === 0) { toast("Cart is empty.", "error"); return; }

  const amountPaid = Number(document.getElementById("amount-paid").value || 0);
  const pending = cartTotal() - amountPaid;

  if (pending > 0.004 && !selectedCustomer) {
    toast("A customer is required for credit or partial payments.", "error");
    return;
  }

  const btn = document.getElementById("checkout-btn");
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing…';

  const total = cartTotal();
  const paymentStatus = pending <= 0.004 ? "PAID" : (amountPaid <= 0.004 ? "UNPAID" : "PARTIAL");

  try {
    const result = await api("/api/orders/", {
      method: "POST",
      body: {
        items: cart.map(c => ({ product_id: c.product_id, quantity: c.quantity })),
        amount_paid: amountPaid,
        payment_method: paymentMethod,
        payment_status: paymentStatus,
        customer_id: selectedCustomer ? selectedCustomer.id : null,
      },
    });

    let msg = `Sale #${result.order_id} complete — ${formatMoney(result.total_bill)}.`;
    if (result.change_due > 0) msg += ` Change due: ${formatMoney(result.change_due)}.`;
    toast(msg, "success");
    if (result.credit_warning) toast(result.credit_warning, "error");

    cart = [];
    selectedCustomer = null;
    document.getElementById("selected-customer").style.display = "none";
    setPaymentMethod("CASH");
    renderCart();
  } catch (err) {
    toastError(err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-receipt"></i> Complete Sale';
  }
}

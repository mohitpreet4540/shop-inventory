requireAuth(["OWNER", "ADMIN", "CASHIER"]);
renderShell("products.html", "Inventory");

const canManage = Session.hasRole("OWNER", "ADMIN");
const content = document.getElementById("ab-page-content");

content.innerHTML = `
  <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:flex-end; margin-bottom:16px;">
    <div style="flex:1; min-width:220px;">
      <label class="field-label">Search</label>
      <input class="input" id="filter-search" placeholder="Name or barcode…">
    </div>
    <div style="min-width:160px;">
      <label class="field-label">Brand</label>
      <input class="input" id="filter-brand" placeholder="Any brand">
    </div>
    <div style="min-width:180px;">
      <label class="field-label">Category</label>
      <select class="input" id="filter-category"><option value="">All categories</option></select>
    </div>
    <button class="btn btn-outline" onclick="applyFilters()"><i class="fa-solid fa-filter"></i> Filter</button>
    ${canManage ? `
      <button class="btn btn-outline" onclick="openImportModal()"><i class="fa-solid fa-file-csv"></i> Bulk import</button>
      <button class="btn btn-primary" onclick="openProductModal()"><i class="fa-solid fa-plus"></i> Add product</button>
    ` : ""}
  </div>

  <div class="card" style="overflow-x:auto;">
    <table class="ledger-table" id="products-table">
      <thead><tr>
        <th>Product</th><th>Brand</th><th>Barcode</th>
        <th style="text-align:right;">Cost</th><th style="text-align:right;">Sell</th>
        <th style="text-align:right;">Stock</th><th>Categories</th><th>Expiry</th>
        <th></th>
      </tr></thead>
      <tbody id="products-tbody"></tbody>
    </table>
  </div>

  <!-- Product create / edit modal -->
  <div id="product-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel">
      <div style="padding:22px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:14px;" id="product-modal-title">Add product</h3>
        <form id="product-form" style="display:flex; flex-direction:column; gap:12px;">
          <input type="hidden" id="pf-id">
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div><label class="field-label">Name</label><input class="input" id="pf-name" required></div>
            <div><label class="field-label">Brand</label><input class="input" id="pf-brand" value="Local"></div>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div><label class="field-label">Barcode (optional)</label><input class="input" id="pf-barcode"></div>
            <div><label class="field-label">Unit type</label>
              <select class="input" id="pf-unit">
                <option>PIECE</option><option>KG</option><option>GRAM</option><option>LITRE</option><option>ML</option><option>PACK</option><option>DOZEN</option><option>BOX</option>
              </select>
            </div>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr;gap:10px;">
            <div><label class="field-label">Cost price</label><input class="input" type="number" min="0.01" step="0.01" id="pf-cost" required></div>
            <div><label class="field-label">Selling price</label><input class="input" type="number" min="0.01" step="0.01" id="pf-sell" required></div>
          </div>
          <div id="pf-initial-stock-wrap">
            <label class="field-label">Initial stock</label>
            <input class="input" type="number" min="0" step="0.01" id="pf-initial-stock" value="0">
          </div>
          <div>
            <label class="field-label">Categories (at least one)</label>
            <div id="pf-categories" style="max-height:150px; overflow-y:auto; border:1px solid #D9D3C2; border-radius:8px; padding:8px 10px; display:flex; flex-direction:column; gap:4px; font-size:0.85rem;"></div>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div><label class="field-label">Image URL (optional)</label><input class="input" id="pf-image"></div>
            <div><label class="field-label">Expiry date (optional)</label><input class="input" type="date" id="pf-expiry"></div>
          </div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="closeModal('product-modal')">Cancel</button>
            <button type="submit" class="btn btn-primary" style="flex:1; justify-content:center;">Save product</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Price update modal -->
  <div id="price-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:380px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:12px;">Update pricing</h3>
        <form id="price-form" style="display:flex; flex-direction:column; gap:10px;">
          <input type="hidden" id="price-product-id">
          <div><label class="field-label">Cost price</label><input class="input" type="number" min="0.01" step="0.01" id="price-cost"></div>
          <div><label class="field-label">Selling price</label><input class="input" type="number" min="0.01" step="0.01" id="price-sell" required></div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="closeModal('price-modal')">Cancel</button>
            <button type="submit" class="btn btn-gold" style="flex:1; justify-content:center;">Update</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Restock modal -->
  <div id="restock-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:380px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:12px;">Restock</h3>
        <form id="restock-form" style="display:flex; flex-direction:column; gap:10px;">
          <input type="hidden" id="restock-product-id">
          <div><label class="field-label">Incoming quantity</label><input class="input" type="number" min="0.01" step="0.01" id="restock-qty" required></div>
          <div><label class="field-label">Supplier unit cost</label><input class="input" type="number" min="0" step="0.01" id="restock-cost" required></div>
          <div><label class="field-label">Batch expiry date (optional — leave blank if it doesn't expire)</label><input class="input" type="date" id="restock-expiry"></div>
          <div><label class="field-label">Notes (optional)</label><input class="input" id="restock-notes" placeholder="Invoice number, delivery note…"></div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="closeModal('restock-modal')">Cancel</button>
            <button type="submit" class="btn btn-gold" style="flex:1; justify-content:center;">Log restock</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Stock batches modal (FEFO breakdown) -->
  <div id="batches-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:520px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:2px;" id="batches-modal-title">Stock batches</h3>
        <p style="font-size:0.78rem; color:var(--muted); margin-bottom:12px;">
          Oldest-expiring batches are sold first (FEFO). Non-expiring batches are drawn from last.
        </p>
        <div id="batches-list"></div>
        <button type="button" class="btn btn-outline" style="width:100%; justify-content:center; margin-top:14px;" onclick="closeModal('batches-modal')">Close</button>
      </div>
    </div>
  </div>

  <!-- Bulk import modal -->
  <div id="import-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:460px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:8px;">Bulk import via CSV</h3>
        <p style="font-size:0.78rem; color:var(--muted); margin-bottom:12px;">
          Required columns: <code class="font-mono">name, cost_price, selling_price</code>.
          Optional: <code class="font-mono">brand, barcode, unit_type, initial_stock, category_names</code> (semicolon-separated, auto-created if missing), <code class="font-mono">image_url</code>.
        </p>
        <input type="file" id="import-file" accept=".csv" class="input" style="padding:8px;">
        <div id="import-result" style="margin-top:12px; font-size:0.82rem;"></div>
        <div style="display:flex; gap:8px; margin-top:14px;">
          <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="closeModal('import-modal')">Close</button>
          <button type="button" class="btn btn-gold" style="flex:1; justify-content:center;" onclick="submitImport()">Upload &amp; import</button>
        </div>
      </div>
    </div>
  </div>
`;

let allCategories = []; // flattened { id, name, depth }
let currentProducts = [];

function closeModal(id) { document.getElementById(id).style.display = "none"; }

loadCategoriesForFilters();
loadProducts();

async function loadCategoriesForFilters() {
  try {
    const tree = await api("/api/categories/tree");
    allCategories = [];
    flatten(tree, 0);
    function flatten(nodes, depth) {
      nodes.forEach(n => {
        allCategories.push({ id: n.id, name: n.name, depth, is_active: n.is_active });
        if (n.subcategories && n.subcategories.length) flatten(n.subcategories, depth + 1);
      });
    }
    const filterSel = document.getElementById("filter-category");
    filterSel.innerHTML = `<option value="">All categories</option>` + allCategories.map(c =>
      `<option value="${c.id}">${"— ".repeat(c.depth)}${escapeHtml(c.name)}</option>`
    ).join("");

    const pfCategories = document.getElementById("pf-categories");
    pfCategories.innerHTML = allCategories.map(c => `
      <label style="display:flex; align-items:center; gap:6px;">
        <input type="checkbox" value="${c.id}" class="pf-cat-cb">
        <span>${"— ".repeat(c.depth)}${escapeHtml(c.name)}${c.is_active ? "" : " (inactive)"}</span>
      </label>
    `).join("") || `<span style="color:var(--muted);">No categories yet — create one first on the Categories page.</span>`;
  } catch (err) {
    toastError(err);
  }
}

async function loadProducts() {
  const tbody = document.getElementById("products-tbody");
  tbody.innerHTML = `<tr><td colspan="9"><div class="skeleton" style="height:16px; margin:8px 0;"></div></td></tr>`.repeat(4);

  const params = new URLSearchParams();
  const search = document.getElementById("filter-search").value.trim();
  const brand = document.getElementById("filter-brand").value.trim();
  const categoryId = document.getElementById("filter-category").value;
  if (search) params.set("search", search);
  if (brand) params.set("brand", brand);
  if (categoryId) params.set("category_id", categoryId);

  try {
    const products = await api(`/api/products/?${params.toString()}`);
    currentProducts = products;
    renderProducts(products);
  } catch (err) {
    toastError(err);
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--muted); padding:20px;">Could not load products.</td></tr>`;
  }
}

function applyFilters() { loadProducts(); }

function renderProducts(products) {
  const tbody = document.getElementById("products-tbody");
  if (products.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--muted); padding:24px;">No products match these filters.</td></tr>`;
    return;
  }
  tbody.innerHTML = products.map(p => {
    const low = Number(p.current_quantity) <= 5;
    return `
      <tr>
        <td style="font-weight:600;">${escapeHtml(p.name)}</td>
        <td>${escapeHtml(p.brand)}</td>
        <td class="font-mono" style="font-size:0.78rem;">${escapeHtml(p.barcode || "—")}</td>
        <td style="text-align:right;" class="font-mono">${formatMoney(p.cost_price)}</td>
        <td style="text-align:right;" class="font-mono">${formatMoney(p.selling_price)}</td>
        <td style="text-align:right;"><span class="badge ${low ? "badge-red" : "badge-green"}">${formatQty(p.current_quantity)} ${escapeHtml(p.unit_type)}</span></td>
        <td>${p.categories.map(c => `<span class="badge badge-navy" style="margin:1px;">${escapeHtml(c.name)}</span>`).join(" ") || "—"}</td>
        <td style="font-size:0.78rem;">${p.expiry_date ? formatDate(p.expiry_date) : "—"}</td>
        <td style="white-space:nowrap;">
          <button class="btn btn-outline btn-sm" onclick="openBatchesModal(${p.id}, '${escapeHtml(p.name).replace(/'/g, "\\'")}')" title="View batches"><i class="fa-solid fa-layer-group"></i></button>
          ${canManage ? `
          <button class="btn btn-outline btn-sm" onclick="openProductModal(${p.id})" title="Edit"><i class="fa-solid fa-pen"></i></button>
          <button class="btn btn-outline btn-sm" onclick="openPriceModal(${p.id})" title="Price"><i class="fa-solid fa-tag"></i></button>
          <button class="btn btn-outline btn-sm" onclick="openRestockModal(${p.id})" title="Restock"><i class="fa-solid fa-truck-ramp-box"></i></button>
          ` : ""}
        </td>
      </tr>
    `;
  }).join("");
}

// ---------- Create / edit product ----------
function openProductModal(productId) {
  const form = document.getElementById("product-form");
  form.reset();
  document.querySelectorAll(".pf-cat-cb").forEach(cb => cb.checked = false);
  document.getElementById("pf-id").value = "";
  document.getElementById("pf-initial-stock-wrap").style.display = "block";

  if (productId) {
    const p = currentProducts.find(x => x.id === productId);
    document.getElementById("product-modal-title").textContent = "Edit product";
    document.getElementById("pf-id").value = p.id;
    document.getElementById("pf-name").value = p.name;
    document.getElementById("pf-brand").value = p.brand;
    document.getElementById("pf-barcode").value = p.barcode || "";
    document.getElementById("pf-unit").value = p.unit_type;
    document.getElementById("pf-cost").value = p.cost_price;
    document.getElementById("pf-sell").value = p.selling_price;
    document.getElementById("pf-image").value = p.image_url || "";
    document.getElementById("pf-expiry").value = p.expiry_date || "";
    document.getElementById("pf-initial-stock-wrap").style.display = "none";
    const catIds = new Set(p.categories.map(c => c.id));
    document.querySelectorAll(".pf-cat-cb").forEach(cb => cb.checked = catIds.has(Number(cb.value)));
  } else {
    document.getElementById("product-modal-title").textContent = "Add product";
  }
  document.getElementById("product-modal").style.display = "flex";
}

document.addEventListener("submit", async (e) => {
  if (e.target.id !== "product-form") return;
  e.preventDefault();

  const id = document.getElementById("pf-id").value;
  const categoryIds = Array.from(document.querySelectorAll(".pf-cat-cb:checked")).map(cb => Number(cb.value));
  if (categoryIds.length === 0) { toast("Select at least one category.", "error"); return; }

  const base = {
    name: document.getElementById("pf-name").value.trim(),
    brand: document.getElementById("pf-brand").value.trim() || "Local",
    barcode: document.getElementById("pf-barcode").value.trim() || null,
    unit_type: document.getElementById("pf-unit").value,
    cost_price: Number(document.getElementById("pf-cost").value),
    selling_price: Number(document.getElementById("pf-sell").value),
    image_url: document.getElementById("pf-image").value.trim() || null,
    expiry_date: document.getElementById("pf-expiry").value || null,
    category_ids: categoryIds,
  };

  try {
    if (id) {
      await api(`/api/products/${id}`, { method: "PATCH", body: base });
      toast("Product updated.", "success");
    } else {
      base.initial_stock = Number(document.getElementById("pf-initial-stock").value || 0);
      await api("/api/products/", { method: "POST", body: base });
      toast("Product added.", "success");
    }
    closeModal("product-modal");
    loadProducts();
  } catch (err) {
    toastError(err);
  }
});

// ---------- Price update ----------
function openPriceModal(productId) {
  const p = currentProducts.find(x => x.id === productId);
  document.getElementById("price-product-id").value = p.id;
  document.getElementById("price-cost").value = p.cost_price;
  document.getElementById("price-sell").value = p.selling_price;
  document.getElementById("price-modal").style.display = "flex";
}

document.addEventListener("submit", async (e) => {
  if (e.target.id !== "price-form") return;
  e.preventDefault();
  const id = document.getElementById("price-product-id").value;
  try {
    await api(`/api/products/${id}/price`, {
      method: "PATCH",
      body: {
        selling_price: Number(document.getElementById("price-sell").value),
        cost_price: document.getElementById("price-cost").value ? Number(document.getElementById("price-cost").value) : null,
      },
    });
    toast("Pricing updated.", "success");
    closeModal("price-modal");
    loadProducts();
  } catch (err) {
    toastError(err);
  }
});

// ---------- Restock ----------
function openRestockModal(productId) {
  document.getElementById("restock-form").reset();
  document.getElementById("restock-product-id").value = productId;
  document.getElementById("restock-modal").style.display = "flex";
}

document.addEventListener("submit", async (e) => {
  if (e.target.id !== "restock-form") return;
  e.preventDefault();
  const id = document.getElementById("restock-product-id").value;
  try {
    const result = await api(`/api/products/${id}/restock`, {
      method: "POST",
      body: {
        quantity: Number(document.getElementById("restock-qty").value),
        unit_cost: Number(document.getElementById("restock-cost").value),
        expiry_date: document.getElementById("restock-expiry").value || null,
        notes: document.getElementById("restock-notes").value.trim() || null,
      },
    });
    toast(`Restocked — new on-hand: ${formatQty(result.new_on_hand_quantity)}.`, "success");
    closeModal("restock-modal");
    loadProducts();
  } catch (err) {
    toastError(err);
  }
});

// ---------- Stock batches (FEFO) ----------
async function openBatchesModal(productId, productName) {
  document.getElementById("batches-modal-title").textContent = `Stock batches — ${productName}`;
  const list = document.getElementById("batches-list");
  list.innerHTML = `<div class="skeleton" style="height:50px; margin-bottom:8px;"></div><div class="skeleton" style="height:50px;"></div>`;
  document.getElementById("batches-modal").style.display = "flex";

  try {
    const batches = await api(`/api/products/${productId}/batches`);
    renderBatches(batches);
  } catch (err) {
    list.innerHTML = `<div style="color:var(--khata-red); font-size:0.85rem;">${escapeHtml(err.message)}</div>`;
  }
}

function renderBatches(batches) {
  const list = document.getElementById("batches-list");
  if (batches.length === 0) {
    list.innerHTML = `<div style="text-align:center; color:var(--muted); padding:20px; font-size:0.85rem;">No batches recorded for this product yet.</div>`;
    return;
  }

  const today = new Date();
  list.innerHTML = `
    <table class="ledger-table">
      <thead><tr><th>Received</th><th style="text-align:right;">Remaining / Received</th><th style="text-align:right;">Unit cost</th><th>Expiry</th></tr></thead>
      <tbody>
        ${batches.map(b => {
          let expiryBadge = `<span class="badge badge-gray">No expiry</span>`;
          if (b.expiry_date) {
            const daysLeft = Math.ceil((new Date(b.expiry_date) - today) / 86400000);
            const cls = daysLeft < 0 ? "badge-red" : daysLeft <= 7 ? "badge-gold" : "badge-green";
            const label = daysLeft < 0 ? "Expired" : `${daysLeft}d left`;
            expiryBadge = `<span class="badge ${cls}">${formatDate(b.expiry_date)} · ${label}</span>`;
          }
          const depleted = Number(b.quantity_remaining) <= 0;
          return `
            <tr style="${depleted ? "opacity:0.5;" : ""}">
              <td style="font-size:0.78rem;">${formatDate(b.received_date)}</td>
              <td style="text-align:right;" class="font-mono">${formatQty(b.quantity_remaining)} / ${formatQty(b.quantity_received)}</td>
              <td style="text-align:right;" class="font-mono">${formatMoney(b.unit_cost)}</td>
              <td>${expiryBadge}</td>
            </tr>
          `;
        }).join("")}
      </tbody>
    </table>
  `;
}

// ---------- Bulk import ----------
function openImportModal() {
  document.getElementById("import-file").value = "";
  document.getElementById("import-result").innerHTML = "";
  document.getElementById("import-modal").style.display = "flex";
}

async function submitImport() {
  const fileInput = document.getElementById("import-file");
  const resultBox = document.getElementById("import-result");
  if (!fileInput.files.length) { toast("Choose a CSV file first.", "error"); return; }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  resultBox.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Importing…`;
  try {
    const result = await api("/api/products/bulk-import", { method: "POST", body: formData, isForm: true });
    resultBox.innerHTML = `
      <div class="badge badge-green">Created ${result.created_count}</div>
      <div class="badge badge-gray" style="margin-left:6px;">Skipped ${result.skipped_count}</div>
      <div class="badge badge-red" style="margin-left:6px;">Errors ${result.error_count}</div>
      ${result.errors.length ? `<div style="margin-top:8px; max-height:120px; overflow-y:auto; font-size:0.76rem; color:var(--khata-red);">
        ${result.errors.map(e => `Row ${e.row}: ${escapeHtml(e.reason)}`).join("<br>")}
      </div>` : ""}
    `;
    loadProducts();
    loadCategoriesForFilters();
  } catch (err) {
    resultBox.innerHTML = `<span style="color:var(--khata-red);">${escapeHtml(err.message)}</span>`;
  }
}

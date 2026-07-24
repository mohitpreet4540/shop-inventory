requireAuth(["OWNER", "ADMIN", "CASHIER"]);
renderShell("categories.html", "Categories");

const canManage = Session.hasRole("OWNER", "ADMIN");
const content = document.getElementById("ab-page-content");

content.innerHTML = `
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
    <p style="font-size:0.82rem; color:var(--muted); max-width:520px;">
      Two levels deep: a main category, and subcategories underneath it. Turning off a main category also turns off everything nested inside it.
    </p>
    ${canManage ? `<button class="btn btn-primary" onclick="openCategoryModal()"><i class="fa-solid fa-plus"></i> Add category</button>` : ""}
  </div>

  <div id="tree-wrap" style="display:flex; flex-direction:column; gap:12px;"></div>

  <div id="category-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:400px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:12px;">Add category</h3>
        <form id="category-form" style="display:flex; flex-direction:column; gap:10px;">
          <div><label class="field-label">Name</label><input class="input" id="cat-name" required></div>
          <div>
            <label class="field-label">Parent category (leave blank for a main category)</label>
            <select class="input" id="cat-parent"><option value="">— None, this is a main category —</option></select>
          </div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="document.getElementById('category-modal').style.display='none'">Cancel</button>
            <button type="submit" class="btn btn-primary" style="flex:1; justify-content:center;">Save</button>
          </div>
        </form>
      </div>
    </div>
  </div>
`;

loadTree();

async function loadTree() {
  const wrap = document.getElementById("tree-wrap");
  wrap.innerHTML = `<div class="skeleton" style="height:70px;"></div><div class="skeleton" style="height:70px;"></div>`;
  try {
    const tree = await api("/api/categories/tree");
    renderTree(tree);
    fillParentSelect(tree);
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="card" style="padding:20px; text-align:center; color:var(--muted);">Could not load categories.</div>`;
  }
}

function fillParentSelect(tree) {
  const sel = document.getElementById("cat-parent");
  sel.innerHTML = `<option value="">— None, this is a main category —</option>` +
    tree.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
}

function renderTree(tree) {
  const wrap = document.getElementById("tree-wrap");
  if (tree.length === 0) {
    wrap.innerHTML = `<div class="card" style="padding:30px; text-align:center; color:var(--muted);">No categories yet. Add your first main category to get started.</div>`;
    return;
  }
  wrap.innerHTML = tree.map(node => `
    <div class="card" style="padding:16px 18px; ${node.is_active ? "" : "opacity:0.55;"}">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap:10px;">
          <i class="fa-solid fa-folder-tree" style="color:var(--brass-gold);"></i>
          <span style="font-weight:700; font-family:'Roboto Slab',serif; color:var(--ink-navy);">${escapeHtml(node.name)}</span>
          <span class="badge badge-navy">${node.product_count} product${node.product_count === 1 ? "" : "s"}</span>
          <span class="badge ${node.is_active ? "badge-green" : "badge-gray"}">${node.is_active ? "Active" : "Inactive"}</span>
        </div>
        ${canManage ? `<button class="btn btn-outline btn-sm" onclick="toggleCategory(${node.id})">
          <i class="fa-solid fa-power-off"></i> ${node.is_active ? "Deactivate" : "Activate"}
        </button>` : ""}
      </div>
      ${node.subcategories.length ? `
        <div style="margin-top:10px; padding-left:28px; display:flex; flex-direction:column; gap:8px;">
          ${node.subcategories.map(sub => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:var(--ledger-cream); border-radius:8px; ${sub.is_active ? "" : "opacity:0.6;"}">
              <div style="display:flex; align-items:center; gap:8px;">
                <i class="fa-solid fa-angles-right" style="color:var(--muted); font-size:0.75rem;"></i>
                <span style="font-weight:600;">${escapeHtml(sub.name)}</span>
                <span class="badge badge-navy">${sub.product_count}</span>
                <span class="badge ${sub.is_active ? "badge-green" : "badge-gray"}">${sub.is_active ? "Active" : "Inactive"}</span>
              </div>
              ${canManage ? `<button class="btn btn-outline btn-sm" onclick="toggleCategory(${sub.id})">
                <i class="fa-solid fa-power-off"></i> ${sub.is_active ? "Deactivate" : "Activate"}
              </button>` : ""}
            </div>
          `).join("")}
        </div>
      ` : ""}
    </div>
  `).join("");
}

function openCategoryModal() {
  document.getElementById("category-form").reset();
  document.getElementById("category-modal").style.display = "flex";
}

document.getElementById("category-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("cat-name").value.trim();
  const parentId = document.getElementById("cat-parent").value;
  try {
    await api("/api/categories/", { method: "POST", body: { name, parent_id: parentId ? Number(parentId) : null } });
    toast("Category added.", "success");
    document.getElementById("category-modal").style.display = "none";
    loadTree();
  } catch (err) {
    toastError(err);
  }
});

async function toggleCategory(id) {
  try {
    await api(`/api/categories/${id}/toggle`, { method: "PATCH" });
    loadTree();
  } catch (err) {
    toastError(err);
  }
}

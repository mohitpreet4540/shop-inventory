requireAuth(["OWNER"]);
renderShell("users.html", "Staff Accounts");

const content = document.getElementById("ab-page-content");
content.innerHTML = `
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
    <p style="font-size:0.82rem; color:var(--muted); max-width:520px;">
      Admins can manage inventory, categories, and finance. Cashiers can bill and manage khata but can't see the dashboard, reports, or finance.
    </p>
    <button class="btn btn-primary" onclick="openUserModal()"><i class="fa-solid fa-user-plus"></i> Add staff account</button>
  </div>

  <div class="card" style="overflow-x:auto;">
    <table class="ledger-table">
      <thead><tr><th>Username</th><th>Role</th><th>Status</th><th>Created</th><th></th></tr></thead>
      <tbody id="users-tbody"></tbody>
    </table>
  </div>

  <div id="user-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:380px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:12px;">Add staff account</h3>
        <form id="user-form" style="display:flex; flex-direction:column; gap:10px;">
          <div><label class="field-label">Username</label><input class="input" id="uf-username" minlength="3" required></div>
          <div><label class="field-label">Password (min. 6 characters)</label><input class="input" type="password" id="uf-password" minlength="6" required></div>
          <div>
            <label class="field-label">Role</label>
            <select class="input" id="uf-role"><option value="CASHIER">Cashier</option><option value="ADMIN">Admin</option></select>
          </div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="document.getElementById('user-modal').style.display='none'">Cancel</button>
            <button type="submit" class="btn btn-primary" style="flex:1; justify-content:center;">Create account</button>
          </div>
        </form>
      </div>
    </div>
  </div>
`;

loadUsers();

async function loadUsers() {
  const tbody = document.getElementById("users-tbody");
  tbody.innerHTML = `<tr><td colspan="5"><div class="skeleton" style="height:16px; margin:8px 0;"></div></td></tr>`.repeat(3);
  try {
    const users = await api("/api/auth/users");
    renderUsers(users);
  } catch (err) {
    toastError(err);
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--muted); padding:20px;">Could not load staff accounts.</td></tr>`;
  }
}

function renderUsers(users) {
  const tbody = document.getElementById("users-tbody");
  tbody.innerHTML = users.map(u => `
    <tr>
      <td style="font-weight:600;">${escapeHtml(u.username)}</td>
      <td><span class="badge badge-navy">${escapeHtml(u.role)}</span></td>
      <td><span class="badge ${u.is_active ? "badge-green" : "badge-gray"}">${u.is_active ? "Active" : "Deactivated"}</span></td>
      <td style="font-size:0.8rem; color:var(--muted);">${u.date_created ? formatDate(u.date_created) : "—"}</td>
      <td>${u.role === "OWNER" ? "" : `<button class="btn btn-outline btn-sm" onclick="toggleUser(${u.id})">
        <i class="fa-solid fa-power-off"></i> ${u.is_active ? "Deactivate" : "Activate"}
      </button>`}</td>
    </tr>
  `).join("");
}

function openUserModal() {
  document.getElementById("user-form").reset();
  document.getElementById("user-modal").style.display = "flex";
}

document.getElementById("user-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/auth/users", {
      method: "POST",
      body: {
        username: document.getElementById("uf-username").value.trim(),
        password: document.getElementById("uf-password").value,
        role: document.getElementById("uf-role").value,
      },
    });
    toast("Staff account created.", "success");
    document.getElementById("user-modal").style.display = "none";
    loadUsers();
  } catch (err) {
    toastError(err);
  }
});

async function toggleUser(id) {
  try {
    await api(`/api/auth/users/${id}/toggle-active`, { method: "PATCH" });
    loadUsers();
  } catch (err) {
    toastError(err);
  }
}

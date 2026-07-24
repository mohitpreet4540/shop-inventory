requireAuth(["OWNER", "ADMIN"]);
renderShell("finance.html", "Finance");

const content = document.getElementById("ab-page-content");
content.innerHTML = `
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
    <p style="font-size:0.82rem; color:var(--muted); max-width:520px;">
      Manual out-of-pocket expenses. Restock purchases are logged automatically from the Inventory page and can't be edited here.
    </p>
    <button class="btn btn-primary" onclick="openExpenseModal()"><i class="fa-solid fa-plus"></i> Log expense</button>
  </div>

  <div class="card" style="overflow-x:auto;">
    <table class="ledger-table">
      <thead><tr><th>Date</th><th>Category</th><th style="text-align:right;">Amount</th><th>Source</th><th>Notes</th><th></th></tr></thead>
      <tbody id="expenses-tbody"></tbody>
    </table>
  </div>

  <div id="expense-modal" class="modal-backdrop" style="display:none;">
    <div class="modal-panel" style="max-width:380px;">
      <div style="padding:20px;">
        <h3 class="font-slab" style="font-weight:700; color:var(--ink-navy); margin-bottom:12px;">Log expense</h3>
        <form id="expense-form" style="display:flex; flex-direction:column; gap:10px;">
          <div><label class="field-label">Amount</label><input class="input" type="number" min="0.01" step="0.01" id="ex-amount" required></div>
          <div><label class="field-label">Category</label><input class="input" id="ex-category" placeholder="RENT, UTILITIES, WAGES, MISC…" required></div>
          <div><label class="field-label">Notes (optional)</label><input class="input" id="ex-notes"></div>
          <div style="display:flex; gap:8px; margin-top:6px;">
            <button type="button" class="btn btn-outline" style="flex:1; justify-content:center;" onclick="document.getElementById('expense-modal').style.display='none'">Cancel</button>
            <button type="submit" class="btn btn-primary" style="flex:1; justify-content:center;">Save</button>
          </div>
        </form>
      </div>
    </div>
  </div>
`;

loadExpenses();

async function loadExpenses() {
  const tbody = document.getElementById("expenses-tbody");
  tbody.innerHTML = `<tr><td colspan="6"><div class="skeleton" style="height:16px; margin:8px 0;"></div></td></tr>`.repeat(4);
  try {
    const expenses = await api("/api/finance/expenses");
    renderExpenses(expenses);
  } catch (err) {
    toastError(err);
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--muted); padding:20px;">Could not load expenses.</td></tr>`;
  }
}

function renderExpenses(expenses) {
  const tbody = document.getElementById("expenses-tbody");
  if (expenses.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--muted); padding:24px;">No expenses logged yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = expenses.map(e => `
    <tr>
      <td style="font-size:0.8rem;">${formatDateTime(e.timestamp)}</td>
      <td><span class="badge badge-navy">${escapeHtml(e.category)}</span></td>
      <td style="text-align:right;" class="font-mono">${formatMoney(e.amount)}</td>
      <td>${e.is_automated ? `<span class="badge badge-gold">Auto (restock)</span>` : `<span class="badge badge-gray">Manual</span>`}</td>
      <td style="font-size:0.8rem; color:var(--muted);">${escapeHtml(e.notes || "—")}</td>
      <td>${!e.is_automated ? `<button class="btn btn-outline btn-sm" onclick="deleteExpense(${e.id})"><i class="fa-solid fa-trash"></i></button>` : ""}</td>
    </tr>
  `).join("");
}

function openExpenseModal() {
  document.getElementById("expense-form").reset();
  document.getElementById("expense-modal").style.display = "flex";
}

document.getElementById("expense-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/finance/expenses", {
      method: "POST",
      body: {
        amount: Number(document.getElementById("ex-amount").value),
        category: document.getElementById("ex-category").value.trim(),
        notes: document.getElementById("ex-notes").value.trim() || null,
      },
    });
    toast("Expense logged.", "success");
    document.getElementById("expense-modal").style.display = "none";
    loadExpenses();
  } catch (err) {
    toastError(err);
  }
});

async function deleteExpense(id) {
  if (!confirm("Delete this expense entry?")) return;
  try {
    await api(`/api/finance/expenses/${id}`, { method: "DELETE" });
    toast("Expense deleted.", "success");
    loadExpenses();
  } catch (err) {
    toastError(err);
  }
}

// ============================================================
// Apna Bazar — Core: API access, session, shell chrome
// ============================================================

const API_BASE_URL = window.API_BASE_URL || "http://localhost:8000";

// ---------- Session ----------
const Session = {
  get token() { return localStorage.getItem("ab_token"); },
  get username() { return localStorage.getItem("ab_username"); },
  get role() { return localStorage.getItem("ab_role"); },
  set({ access_token, username, role }) {
    localStorage.setItem("ab_token", access_token);
    localStorage.setItem("ab_username", username);
    localStorage.setItem("ab_role", role);
  },
  clear() {
    localStorage.removeItem("ab_token");
    localStorage.removeItem("ab_username");
    localStorage.removeItem("ab_role");
  },
  isLoggedIn() { return !!this.token; },
  hasRole(...roles) { return roles.includes(this.role); },
};

// ---------- API wrapper ----------
async function api(path, { method = "GET", body, isForm = false, auth = true } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth && Session.token) headers["Authorization"] = `Bearer ${Session.token}`;

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: isForm ? body : (body !== undefined ? JSON.stringify(body) : undefined),
    });
  } catch (networkErr) {
    throw new Error(`Could not reach the server at ${API_BASE_URL}. Is the backend running?`);
  }

  if (response.status === 401) {
    Session.clear();
    if (!location.pathname.endsWith("login.html")) {
      location.href = "login.html";
    }
    throw new Error("Session expired. Please sign in again.");
  }

  let data = null;
  const text = await response.text();
  if (text) {
    try { data = JSON.parse(text); } catch (e) { data = null; }
  }

  if (!response.ok) {
    const detail = data && data.detail ? data.detail : `Request failed (${response.status})`;
    const message = Array.isArray(detail)
      ? detail.map(d => d.msg || JSON.stringify(d)).join("; ")
      : detail;
    throw new Error(message);
  }

  return data;
}

// ---------- Auth guard ----------
// Call at top of every protected page. Redirects to login if not authenticated,
// and to index if role isn't permitted.
function requireAuth(allowedRoles) {
  if (!Session.isLoggedIn()) {
    location.href = "login.html";
    return false;
  }
  if (allowedRoles && !Session.hasRole(...allowedRoles)) {
    location.href = "billing.html";
    return false;
  }
  return true;
}

// ---------- Toast ----------
function toast(message, type = "info") {
  const el = document.createElement("div");
  el.className = `toast ${type === "error" ? "error" : type === "success" ? "success" : ""}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

function toastError(err) {
  toast(err && err.message ? err.message : "Something went wrong.", "error");
}

// ---------- Formatting ----------
function formatMoney(value) {
  const n = Number(value || 0);
  return "₹" + n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatQty(value) {
  const n = Number(value || 0);
  return n % 1 === 0 ? n.toString() : n.toFixed(2);
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function formatDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- Sidebar / shell ----------
const NAV_ITEMS = [
  { href: "billing.html", icon: "fa-solid fa-cash-register", label: "Billing Counter", roles: ["OWNER", "ADMIN", "CASHIER"] },
  { href: "index.html", icon: "fa-solid fa-chart-line", label: "Dashboard", roles: ["OWNER", "ADMIN"] },
  { href: "products.html", icon: "fa-solid fa-boxes-stacked", label: "Inventory", roles: ["OWNER", "ADMIN", "CASHIER"] },
  { href: "expiring.html", icon: "fa-solid fa-hourglass-half", label: "Expiring Stock", roles: ["OWNER", "ADMIN", "CASHIER"] },
  { href: "categories.html", icon: "fa-solid fa-folder-tree", label: "Categories", roles: ["OWNER", "ADMIN", "CASHIER"] },
  { href: "customers.html", icon: "fa-solid fa-book", label: "Customer Khata", roles: ["OWNER", "ADMIN", "CASHIER"] },
  { href: "finance.html", icon: "fa-solid fa-sack-dollar", label: "Finance", roles: ["OWNER", "ADMIN"] },
  { href: "reports.html", icon: "fa-solid fa-clipboard-list", label: "Stock Ledger", roles: ["OWNER", "ADMIN"] },
  { href: "users.html", icon: "fa-solid fa-users-gear", label: "Staff Accounts", roles: ["OWNER"] },
];

function renderShell(activeHref, pageTitle) {
  const role = Session.role;
  const current = location.pathname.split("/").pop();

  const links = NAV_ITEMS
    .filter(item => !role || item.roles.includes(role))
    .map(item => `
      <a href="${item.href}" class="sidebar-link ${current === item.href ? "active" : ""}">
        <i class="${item.icon}"></i><span>${item.label}</span>
      </a>
    `).join("");

  const shell = `
    <aside class="sidebar" id="ab-sidebar">
      <div class="sidebar-brand">
        <div class="mark"><i class="fa-solid fa-store mr-2"></i>Apna Bazar</div>
        <div class="tagline">Shop Ledger &amp; Billing</div>
      </div>
      <nav class="sidebar-nav">${links}</nav>
      <div class="sidebar-foot">
        <div style="font-size:0.82rem; font-weight:600;">${escapeHtml(Session.username || "")}</div>
        <span class="role-badge">${escapeHtml(role || "")}</span>
        <button onclick="doLogout()" class="btn btn-outline btn-sm" style="width:100%; margin-top:12px; background:transparent; color:#C6CDE0; border-color:rgba(255,255,255,0.2);">
          <i class="fa-solid fa-right-from-bracket"></i> Sign out
        </button>
      </div>
    </aside>
    <div class="main-area">
      <header class="topbar">
        <div style="display:flex; align-items:center; justify-content:space-between;">
          <div style="display:flex; align-items:center; gap:12px;">
            <button id="ab-menu-btn" class="btn btn-outline btn-sm" style="display:none;" onclick="document.getElementById('ab-sidebar').classList.toggle('open')">
              <i class="fa-solid fa-bars"></i>
            </button>
            <h1 class="font-slab" style="font-size:1.3rem; font-weight:700; color:var(--ink-navy);">${escapeHtml(pageTitle)}</h1>
          </div>
          <div id="ab-topbar-actions"></div>
        </div>
      </header>
      <main class="page-content" id="ab-page-content"></main>
    </div>
  `;

  document.getElementById("ab-app").innerHTML = shell;

  if (window.innerWidth <= 860) {
    document.getElementById("ab-menu-btn").style.display = "inline-flex";
  }
}

function doLogout() {
  Session.clear();
  location.href = "login.html";
}

document.addEventListener("DOMContentLoaded", () => {
  const fw = document.getElementById("ab-menu-btn");
  if (fw) fw.style.display = window.innerWidth <= 860 ? "inline-flex" : "none";
});

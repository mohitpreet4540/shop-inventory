// Redirect straight through if already signed in
if (Session.isLoggedIn()) {
  location.href = Session.hasRole("OWNER", "ADMIN") ? "index.html" : "billing.html";
}

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("login-submit-btn");
  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing in…';

  try {
    const data = await api("/api/auth/login", { method: "POST", body: { username, password }, auth: false });
    Session.set(data);
    location.href = Session.hasRole("OWNER", "ADMIN") ? "index.html" : "billing.html";
  } catch (err) {
    toastError(err);
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Sign in';
  }
});

document.getElementById("bootstrap-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("bs-username").value.trim();
  const password = document.getElementById("bs-password").value;

  try {
    await api("/api/auth/bootstrap-owner", { method: "POST", body: { username, password, role: "OWNER" }, auth: false });
    toast("Owner account created. You can sign in now.", "success");
    document.getElementById("setup-modal").style.display = "none";
    document.getElementById("login-username").value = username;
    document.getElementById("login-password").focus();
  } catch (err) {
    toastError(err);
  }
});

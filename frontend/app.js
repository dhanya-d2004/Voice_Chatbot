const API = "http://localhost:8000";
console.log("app.js loaded on", window.location.pathname);

/* ---------------- AUTH FUNCTIONS ---------------- */

async function signup() {
  const emailEl = document.getElementById("email");
  const passwordEl = document.getElementById("password");
  const msgEl = document.getElementById("msg");

  if (!emailEl || !passwordEl || !msgEl) return;

  const res = await fetch(`${API}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: emailEl.value,
      password: passwordEl.value
    })
  });

  msgEl.innerText = res.ok
    ? "Signup successful. You can login now."
    : "Signup failed";
}

async function login() {
  const emailEl = document.getElementById("email");
  const passwordEl = document.getElementById("password");
  const msgEl = document.getElementById("msg");

  if (!emailEl || !passwordEl || !msgEl) return;

  const form = new URLSearchParams();
  form.append("username", emailEl.value);
  form.append("password", passwordEl.value);

  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString()
  });

  const data = await res.json();

  if (!res.ok) {
    msgEl.innerText = data.detail || "Login failed";
    return;
  }

  localStorage.setItem("token", data.access_token);
  window.location.href = "chat.html";
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "index.html";
}

/* ---------------- CHAT PAGE LOGIC ---------------- */

const chatEl = document.getElementById("chat");
const userInfoEl = document.getElementById("userInfo");

if (chatEl && userInfoEl) {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "index.html";
  }

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    userInfoEl.innerText = payload.email || payload.sub;
  } catch {
    logout();
  }
}

/* ---------------- CHAT HELPERS ---------------- */

function addMessage(text, cls) {
  if (!chatEl) return;
  const div = document.createElement("div");
  div.className = `message ${cls}`;
  div.innerText = text;
  chatEl.appendChild(div);
  div.scrollIntoView();
}

/* ---------------- TEXT CHAT ---------------- */

async function sendText() {
  const input = document.getElementById("textInput");
  const token = localStorage.getItem("token");
  if (!input || !token) return;

  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  addMessage(text, "user");

  const res = await fetch(`${API}/api/text-chat`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      conversation_id: "default",
      messages: [{ role: "user", content: text }]
    })
  });

  const data = await res.json();
  addMessage(data.reply, "bot");
}

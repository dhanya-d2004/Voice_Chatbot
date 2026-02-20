const API = "http://localhost:8000";

/* ---------------- DOM REFERENCES ---------------- */

const micBtn = document.getElementById("micBtn");
const chatEl = document.getElementById("chat");

/* ---------------- AUTH ---------------- */

async function signup() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const msg = document.getElementById("msg");

  msg.innerText = "Signing up...";

  try {
    const res = await fetch(`${API}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (!res.ok) {
      msg.innerText = data.detail || "Signup failed";
      return;
    }

    msg.innerText = "Signup successful. You can login now.";
  } catch (err) {
    console.error(err);
    msg.innerText = "Cannot connect to server";
  }
}

async function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const msg = document.getElementById("msg");

  msg.innerText = "Logging in...";

  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  try {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString()
    });

    const data = await res.json();

    if (!res.ok) {
      msg.innerText = data.detail || "Login failed";
      return;
    }

    localStorage.setItem("token", data.access_token);
    location.href = "chat.html";
  } catch (err) {
    console.error(err);
    msg.innerText = "Cannot connect to server";
  }
}

function logout() {
  localStorage.removeItem("token");
  location.href = "index.html";
}

/* ---------------- CHAT STATE ---------------- */

const token = localStorage.getItem("token");

let conversations = [];
let activeConversation = null;

/* ---------------- INIT CHAT PAGE ---------------- */

if (chatEl) {
  if (!token) location.href = "index.html";

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    document.getElementById("userInfo").innerText = payload.email;
  } catch {
    localStorage.removeItem("token");
    location.href = "index.html";
  }

  newConversation();
}

/* ---------------- CONVERSATIONS ---------------- */

function newConversation() {
  const conv = {
    id: null, // backend generates UUID
    title: "New chat",
    messages: []
  };
  conversations.push(conv);
  activeConversation = conv;
  renderConversations();
  renderChat();
}

function renderConversations() {
  const list = document.getElementById("conversations");
  if (!list) return;

  list.innerHTML = "";
  conversations.forEach(c => {
    const div = document.createElement("div");
    div.className = "conversation" + (c === activeConversation ? " active" : "");
    div.innerText = c.title;
    div.onclick = () => {
      activeConversation = c;
      renderConversations();
      renderChat();
    };
    list.appendChild(div);
  });
}

function renderChat() {
  if (!chatEl || !activeConversation) return;

  chatEl.innerHTML = "";

  activeConversation.messages.forEach(m => {
    const div = document.createElement("div");
    div.className = `message ${m.role}`;

    if (m.inputType === "voice") {
      const label = document.createElement("div");
      label.innerText = "🎙 Voice message";
      label.style.fontSize = "0.8em";
      div.appendChild(label);
    }

    const text = document.createElement("div");
    text.innerText = m.content;
    div.appendChild(text);

    chatEl.appendChild(div);
  });

  chatEl.scrollTop = chatEl.scrollHeight;
}


/* ---------------- TEXT CHAT ---------------- */

function onEnter(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendText();
  }
}

async function sendText() {
  if (!activeConversation) newConversation();

  const input = document.getElementById("textInput");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";

  activeConversation.messages.push({
    role: "user",
    content: text
  });
  renderChat();

  let res, data;
  try {
    res = await fetch(`${API}/api/text-chat`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        conversation_id: activeConversation.id,
        messages: activeConversation.messages
      })
    });

    try {
      data = await res.json();
    } catch {
      throw new Error("Invalid JSON");
    }
  } catch (err) {
    console.error(err);
    activeConversation.messages.push({
      role: "assistant",
      content: "⚠️ Server unreachable"
    });
    renderChat();
    return;
  }

  if (!res.ok) {
    activeConversation.messages.push({
      role: "assistant",
      content: data.detail || "⚠️ Request failed"
    });
    renderChat();
    return;
  }

  if (!activeConversation.id) {
    activeConversation.id = data.conversation_id;
  }

  activeConversation.messages.push({
    role: "assistant",
    content: data.reply
  });
  renderChat();
}

/* ---------------- VOICE ---------------- */

let ws, audioContext, processor, stream;
let recording = false;

function toggleMic() {
  recording ? stopMic() : startMic();
}

function startMic() {
  recording = true;
  if (micBtn) micBtn.innerText = "⏹";

  const convParam = activeConversation.id
    ? `&conversation_id=${activeConversation.id}`
    : "";

  ws = new WebSocket(
    `${API.replace("http", "ws")}/api/voice-chat/ws?token=${token}${convParam}`
  );

  ws.binaryType = "arraybuffer";

  ws.onmessage = e => {
    if (typeof e.data === "string") {
      const msg = JSON.parse(e.data);

      if (msg.type === "conversation_created") {
        activeConversation.id = msg.conversation_id;
      }

      if (msg.type === "user_message") {
        activeConversation.messages.push({
          role: "user",
          content: msg.text,
          inputType: "voice"
        });
        renderChat();
      }

      if (msg.type === "assistant_message") {
        activeConversation.messages.push({
          role: "assistant",
          content: msg.text
        });
        renderChat();
      }
    } else {
      // play assistant audio
      new Audio(URL.createObjectURL(new Blob([e.data]))).play();
    }
  };

  navigator.mediaDevices.getUserMedia({ audio: true }).then(s => {
    stream = s;
    audioContext = new AudioContext({ sampleRate: 16000 });
    processor = audioContext.createScriptProcessor(4096, 1, 1);

    audioContext.createMediaStreamSource(stream).connect(processor);
    processor.connect(audioContext.destination);

    processor.onaudioprocess = e => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(e.inputBuffer.getChannelData(0).buffer);
      }
    };
  });
}

function stopMic() {
  recording = false;
  if (micBtn) micBtn.innerText = "🎙";

  if (ws) ws.send("END");
  if (processor) processor.disconnect();
  if (stream) stream.getTracks().forEach(t => t.stop());
  if (audioContext) audioContext.close();
}


/* ---------------- GLOBAL EXPORTS ---------------- */

window.onEnter = onEnter;
window.login = login;
window.signup = signup;
window.logout = logout;
window.sendText = sendText;
window.toggleMic = toggleMic;

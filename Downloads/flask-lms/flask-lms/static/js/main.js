// Confirm destructive actions
document.addEventListener("submit", (e) => {
  const f = e.target;
  if (f.dataset.confirm && !confirm(f.dataset.confirm)) e.preventDefault();
});

// AI tutor chat widget
async function sendTutorMessage(url, csrfToken) {
  const input = document.getElementById("tutor-input");
  const win   = document.getElementById("chat-window");
  const btn   = document.getElementById("tutor-send");
  const text  = input.value.trim();
  if (!text) return;

  appendMsg(win, "user", text);
  input.value = "";
  btn.disabled = true;

  const typing = document.createElement("div");
  typing.className = "chat-msg assistant chat-typing";
  typing.textContent = "Thinking…";
  win.appendChild(typing); win.scrollTop = win.scrollHeight;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ question: text }),
    });
    const data = await res.json();
    typing.remove();
    if (!res.ok) {
      appendMsg(win, "assistant", "⚠️ " + (data.error || "AI error"));
    } else {
      appendMsg(win, "assistant", data.answer);
    }
  } catch (err) {
    typing.remove();
    appendMsg(win, "assistant", "⚠️ Network error: " + err);
  } finally {
    btn.disabled = false;
    input.focus();
  }
}

function appendMsg(win, role, text) {
  const div = document.createElement("div");
  div.className = "chat-msg " + role;
  div.textContent = text;
  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
}

/* ============ Backend API ============
   Тонкая обёртка над REST API сервера. API на том же origin,
   поэтому работает и локально, и через туннель/reverse-proxy. */

const RAG_API = "";

async function apiUpload(file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${RAG_API}/api/upload`, { method: "POST", body: fd });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || "Ошибка загрузки");
  return data; // { ok, file, chunks }
}

async function apiAsk(question) {
  const r = await fetch(`${RAG_API}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || "Ошибка запроса");
  return data; // { answer, confidence, context, sources }
}

async function apiReset() {
  await fetch(`${RAG_API}/api/reset`, { method: "DELETE" });
}

async function apiHealth() {
  try {
    const r = await fetch(`${RAG_API}/api/health`);
    if (!r.ok) return { qdrant: false, ollama: false };
    return await r.json();
  } catch {
    return { qdrant: false, ollama: false };
  }
}

async function apiStatus() {
  try {
    const r = await fetch(`${RAG_API}/api/status`);
    if (!r.ok) return null;
    return await r.json(); // { indexed, file_name, chunks }
  } catch {
    return null;
  }
}

Object.assign(window, { apiUpload, apiAsk, apiReset, apiHealth, apiStatus });

/* ============ Подсказки для пустого поля ввода ============ */
const SUGGESTIONS = ["О чём этот документ?", "Перескажи кратко", "Какие ключевые факты указаны?"];

function fileInfo(file) {
  const name = file.name || "Документ.pdf";
  const ext = (name.split(".").pop() || "pdf").toUpperCase().slice(0, 4);
  const kb = file.size ? file.size / 1024 : 2458;
  const size = kb > 1024 ? (kb / 1024).toFixed(1) + " МБ" : Math.round(kb) + " КБ";
  return { name, ext, size };
}

/* ============ App ============ */
const ACCENT = "#4cc38a";   // цвет акцента интерфейса

// Имя модели по умолчанию; реальное приходит с бэкенда (/api/health).
window.RAG_MODEL = window.RAG_MODEL || "ollama";

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [view, setView] = useState("empty");        // empty | processing | chat
  const [doc, setDoc] = useState(null);
  const [proc, setProc] = useState({ file: null, progress: 0, stepIndex: 0 });
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);
  const [toast, setToast] = useState("");
  const [health, setHealth] = useState({ qdrant: false, ollama: false });
  const [model, setModel] = useState(window.RAG_MODEL);
  const [drawerOpen, setDrawerOpen] = useState(false);   // выдвижная панель на мобильных
  const feedRef = useRef(null);

  /* apply accent */
  useEffect(() => { document.documentElement.style.setProperty("--accent", ACCENT); }, []);

  /* Лента НЕ скроллится автоматически — пользователь сам управляет прокруткой. */

  /* toast auto-hide */
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(""), 4000);
    return () => clearTimeout(id);
  }, [toast]);

  /* health-poll + подхват уже проиндексированного документа */
  useEffect(() => {
    let alive = true;
    const poll = async () => {
      const h = await apiHealth();
      if (alive) {
        setHealth(h);
        if (h.model) { window.RAG_MODEL = h.model; setModel(h.model); }
      }
    };
    poll();
    const id = setInterval(poll, 5000);

    apiStatus().then((s) => {
      if (alive && s && s.indexed) {
        setDoc({ name: s.file_name, ext: (s.file_name.split(".").pop() || "").toUpperCase().slice(0, 4),
          size: "", pages: null, chunks: s.chunks, suggestions: SUGGESTIONS });
        setView("chat");
      }
    });
    return () => { alive = false; clearInterval(id); };
  }, []);

  /* ----- upload: реальная индексация на бэкенде ----- */
  const handleUpload = useCallback((file) => {
    const fi = fileInfo(file);
    setView("processing");
    setProc({ file: fi, progress: 0, stepIndex: 0 });

    // Анимация прогресса (бэкенд не стримит этапы, поэтому идёт визуально
    // до ~90 %, а на ответ от сервера завершается до 100 %).
    let progress = 0;
    const total = PROC_STEPS.length;
    const tick = setInterval(() => {
      progress = Math.min(90, progress + 1.2 + Math.random() * 2);
      const stepIndex = Math.min(total - 1, Math.floor((progress / 100) * total));
      setProc({ file: fi, progress, stepIndex });
    }, 200);

    apiUpload(file)
      .then((data) => {
        clearInterval(tick);
        setProc({ file: fi, progress: 100, stepIndex: total });
        setTimeout(() => {
          setDoc({ ...fi, pages: null, chunks: data.chunks, suggestions: SUGGESTIONS });
          setView("chat");
        }, 400);
      })
      .catch((e) => {
        clearInterval(tick);
        setView("empty");
        setToast(e.message || "Ошибка загрузки документа");
      });
  }, []);

  const handleRemove = () => {
    apiReset().catch(() => {});
    setDoc(null); setMessages([]); setHistory([]); setView("empty"); setInput("");
  };

  /* ----- ask: реальный запрос к бэкенду + стриминг полученного ответа ----- */
  const streamMessage = useCallback((id, paragraphs, sources, confidence, model) => {
    const toks = tokenize(paragraphs);
    setMessages((m) => m.map((x) => x.id === id
      ? { ...x, paragraphs, sources, confidence, model, thinking: false, _total: toks.length }
      : x));
    const stream = setInterval(() => {
      setMessages((m) => m.map((x) => {
        if (x.id !== id) return x;
        const rev = x.revealed + (2 + Math.floor(Math.random() * 2));
        if (rev >= x._total) { clearInterval(stream); setBusy(false); return { ...x, revealed: x._total, streaming: false }; }
        return { ...x, revealed: rev };
      }));
    }, 24);
  }, []);

  const ask = useCallback((q) => {
    const text = (q ?? input).trim();
    if (!text || busy || !doc) return;
    setInput(""); setBusy(true);
    setHistory((h) => [text, ...h].slice(0, 12));

    const id = Date.now();
    // Плейсхолдер с индикатором «думает», пока ждём ответ сервера.
    setMessages((m) => [...m, { id, q: text, paragraphs: [], sources: [],
      confidence: 0, model: "", streaming: true, thinking: true, revealed: 0, _total: 0 }]);

    apiAsk(text)
      .then((data) => {
        const paragraphs = (data.answer || "Нет данных").split(/\n{2,}/).filter(Boolean);
        const sources = (data.sources || []).map((s) => ({
          id: s.id, page: null, score: s.score, text: s.text,
        }));
        const conf = Math.round((data.confidence || 0) * 100);
        streamMessage(id, paragraphs, sources, conf, window.RAG_MODEL);
      })
      .catch((e) => {
        // НИКОГДА не показываем выдуманные данные — только честную ошибку,
        // иначе модель «придумает» ответ, которого нет в документе.
        const msg = /JSON|Failed to fetch|NetworkError|aborted/i.test(e.message)
          ? "Сервер не успел ответить (долгая генерация или обрыв туннеля). Попробуйте ещё раз или задайте более короткий вопрос."
          : e.message;
        streamMessage(id, [`⚠️ Не удалось получить ответ. ${msg}`], [], 0, window.RAG_MODEL);
        setToast("Ошибка запроса к серверу");
      });
  }, [input, busy, doc, streamMessage]);

  /* ----- derived stats ----- */
  const answered = messages.filter((m) => !m.streaming);
  const stats = {
    chunks: doc ? doc.chunks : 0,
    questions: history.length,
    confidence: answered.length ? Math.round(answered.reduce((s, m) => s + m.confidence, 0) / answered.length) : 0,
    sources: answered.reduce((s, m) => s + (m.sources ? m.sources.length : 0), 0),
  };

  return (
    <div className={"app" + (collapsed ? " collapsed" : "") + (drawerOpen ? " drawer-open" : "")}>
      {/* затемнение под выдвижной панелью (только на мобильных) */}
      <div className="scrim" onClick={() => setDrawerOpen(false)} />

      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)}
        doc={doc} stats={stats} history={history}
        onUpload={(f) => { setDrawerOpen(false); handleUpload(f); }}
        onRemove={handleRemove}
        onPickHistory={(q) => { setDrawerOpen(false); ask(q); }} />

      <main className="main">
        <Topbar doc={doc} health={health} onMenu={() => setDrawerOpen(true)} />

        {view === "empty" && <EmptyState onUpload={handleUpload} />}
        {view === "processing" && <ProcessingState {...proc} />}
        {view === "chat" && (
          <div className="feed-wrap" ref={feedRef}>
            <div className="feed">
              <ReadyHero doc={doc} onChip={(s) => ask(s)} />
              {messages.map((m) => <Message key={m.id} msg={m} />)}
            </div>
          </div>
        )}

        <Composer value={input} onChange={setInput} onSend={() => ask()}
          disabled={view !== "chat"} busy={busy} model={model} />
      </main>

      {toast && <div className="toast-msg">{toast}</div>}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

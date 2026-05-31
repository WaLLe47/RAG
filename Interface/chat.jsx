/* ============ Chat: feed, message, sources, composer ============ */

/* parse inline **bold** and [[n]] citation markers -> React nodes */
function parseInline(str, onCite) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\[\[\d+\]\])/g;
  let last = 0, m, k = 0;
  while ((m = re.exec(str)) !== null) {
    if (m.index > last) out.push(str.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) {
      out.push(<strong key={k++}>{tok.slice(2, -2)}</strong>);
    } else {
      const n = tok.slice(2, -2);
      out.push(<span key={k++} className="cite" onClick={() => onCite && onCite()}>{n}</span>);
    }
    last = re.lastIndex;
  }
  if (last < str.length) out.push(str.slice(last));
  return out;
}

function parseChunk(text) {
  const re = /(<<hl>>[^]*?<<\/hl>>)/g;
  const out = []; let last = 0, m, k = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    out.push(<span key={k++} className="hl">{m[0].slice(6, -7)}</span>);
    last = re.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

/* flatten paragraphs into stream tokens (preserving spaces + para breaks) */
function tokenize(paragraphs) {
  const toks = [];
  paragraphs.forEach((p, pi) => {
    if (pi > 0) toks.push({ br: true });
    p.split(/(\s+)/).forEach((w) => { if (w !== "") toks.push({ w }); });
  });
  return toks;
}

function Sources({ sources }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="sources">
      <button className={"src-toggle" + (open ? " open" : "")} onClick={() => setOpen(!open)}>
        <span className="chev"><Icon name="chevron" size={13} /></span>
        <span><span className="src-count">{sources.length}</span> источника из документа</span>
      </button>
      <div className={"src-body" + (open ? " open" : "")}>
        <div className="src-inner">
          <div className="src-list">
            {sources.map((s, i) => (
              <div key={i} className="chunk">
                <div className="chunk-head">
                  <span className="chunk-id">{s.id}</span>
                  {s.page != null && <span className="chunk-page">стр. {s.page}</span>}
                  <span className="chunk-score">
                    {s.score.toFixed(2)}
                    <span className="score-bar"><span className="score-fill" style={{ width: (s.score * 100) + "%" }} /></span>
                  </span>
                </div>
                <div className="chunk-text">{parseChunk(s.text)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Message({ msg }) {
  const toks = tokenize(msg.paragraphs);
  const shown = msg.streaming ? toks.slice(0, msg.revealed) : toks;
  // rebuild paragraph strings from shown tokens
  const paras = [[]];
  shown.forEach((t) => { if (t.br) paras.push([]); else paras[paras.length - 1].push(t.w); });
  const done = !msg.streaming || msg.revealed >= toks.length;

  return (
    <div className="msg">
      <div className="msg-role">
        <div className="avatar user">В</div>
        <span className="msg-who">Вы</span>
      </div>
      <div className="msg-q">{msg.q}</div>

      <div className="msg-role" style={{ marginTop: 10 }}>
        <div className="avatar ai"><Icon name="diamond" size={12} /></div>
        <span className="msg-who">RAG</span>
      </div>

      {msg.thinking ? (
        <div className="typing-dots"><span /><span /><span /></div>
      ) : (
        <div className="msg-a">
          {paras.map((p, i) => (
            <p key={i}>
              {parseInline(p.join(""))}
              {msg.streaming && !done && i === paras.length - 1 && <span className="cursor-blink" />}
            </p>
          ))}
        </div>
      )}

      {!msg.thinking && done && msg.sources && (
        <>
          <Sources sources={msg.sources} />
          <div className="ans-meta">
            <span className="it conf-tag"><Icon name="target" size={12} /> Уверенность {msg.confidence}%</span>
            <span className="it"><Icon name="layers" size={12} /> {msg.sources.length} чанков</span>
            <span className="it"><Icon name="cpu" size={12} /> {msg.model}</span>
            <span className="ans-act">
              <button className="act-btn" title="Скопировать"><Icon name="copy" size={14} /></button>
              <button className="act-btn" title="Хороший ответ"><Icon name="thumb" size={14} /></button>
              <button className="act-btn" title="Переспросить"><Icon name="refresh" size={14} /></button>
            </span>
          </div>
        </>
      )}
    </div>
  );
}

function ReadyHero({ doc, onChip }) {
  return (
    <div className="msg" style={{ alignItems: "flex-start" }}>
      <div className="msg-role">
        <div className="avatar ai"><Icon name="diamond" size={12} /></div>
        <span className="msg-who">RAG</span>
      </div>
      <div className="msg-a" style={{ paddingLeft: 34 }}>
        <p>
          Документ <strong>«{doc.name}»</strong> загружен и проиндексирован —
          {" "}{doc.chunks} чанков готовы к поиску. Задайте вопрос на естественном языке,
          и я отвечу со ссылками на конкретные фрагменты текста.
        </p>
        <div className="chips">
          {doc.suggestions.map((s, i) => (
            <button key={i} className="chip" onClick={() => onChip(s)}>{s}</button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Composer({ value, onChange, onSend, disabled, busy, model }) {
  const taRef = useRef(null);
  useEffect(() => {
    const ta = taRef.current; if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }, [value]);

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); }
  };

  return (
    <div className="composer-wrap">
      <div className="composer-inner">
        <div className={"composer" + (disabled ? " disabled" : "")}>
          <span className="prompt-mark">›_</span>
          <textarea ref={taRef} rows={1} value={value}
            placeholder={disabled ? "Сначала загрузите документ…" : "Задайте вопрос по документу…"}
            onChange={(e) => onChange(e.target.value)} onKeyDown={onKey} />
          <button className="send-btn" disabled={!value.trim() || busy} onClick={onSend} title="Спросить">
            {busy ? <span className="spin"><Icon name="loader" size={17} /></span> : <Icon name="send" size={17} />}
          </button>
        </div>
        <div className="composer-foot">
          <span><span className="kbd">Enter</span> отправить</span>
          <span><span className="kbd">Shift+Enter</span> новая строка</span>
          <span className="right"><Icon name="cpu" size={12} /> {model || "ollama"}</span>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Message, ReadyHero, Composer, tokenize });

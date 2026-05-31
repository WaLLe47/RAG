/* ============ Icons + Sidebar ============ */
const { useState, useRef, useEffect, useCallback } = React;

/* --- minimal stroke icon set --- */
function Icon({ name, size = 18, stroke = 1.6 }) {
  const p = { width: size, height: size, viewBox: "0 0 24 24", fill: "none",
    stroke: "currentColor", strokeWidth: stroke, strokeLinecap: "round", strokeLinejoin: "round" };
  const paths = {
    panelLeft: <><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="9" y1="4" x2="9" y2="20"/></>,
    upload: <><path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M5 20h14"/></>,
    doc: <><path d="M14 3v4a1 1 0 0 0 1 1h4"/><path d="M5 8a2 2 0 0 1 2-2h7l5 5v9a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2Z"/></>,
    chart: <><path d="M3 3v18h18"/><rect x="7" y="11" width="3" height="6"/><rect x="13" y="7" width="3" height="10"/></>,
    history: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 4v4h4"/><path d="M12 8v4l3 2"/></>,
    x: <><path d="M18 6 6 18M6 6l12 12"/></>,
    chevron: <><path d="m9 6 6 6-6 6"/></>,
    send: <><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></>,
    sparkle: <><path d="M12 3v4M12 17v4M3 12h4M17 12h4"/><path d="M12 8a4 4 0 0 0 4 4 4 4 0 0 0-4 4 4 4 0 0 0-4-4 4 4 0 0 0 4-4Z"/></>,
    diamond: <><path d="M12 3 21 12 12 21 3 12Z"/></>,
    check: <><path d="M20 6 9 17l-5-5"/></>,
    loader: <><path d="M12 3a9 9 0 1 0 9 9"/></>,
    copy: <><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></>,
    refresh: <><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/></>,
    thumb: <><path d="M7 11v9H4a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1Z"/><path d="M7 11l4-7a2 2 0 0 1 2 1v4h5a2 2 0 0 1 2 2l-1.5 7a2 2 0 0 1-2 1.5H7"/></>,
    layers: <><path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/></>,
    target: <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></>,
    msg: <><path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2Z"/></>,
    book: <><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2Z"/><path d="M4 19a2 2 0 0 1 2-2h13"/></>,
    scan: <><path d="M3 8V5a2 2 0 0 1 2-2h3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M21 16v3a2 2 0 0 1-2 2h-3"/><path d="M7 12h10"/></>,
    cpu: <><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/></>,
    menu: <><path d="M3 6h18M3 12h18M3 18h18"/></>,
  };
  return <svg {...p}>{paths[name] || null}</svg>;
}

/* ===================== Sidebar ===================== */
function Sidebar({ collapsed, onToggle, doc, stats, history, onUpload, onRemove, onPickHistory }) {
  return (
    <aside className="side">
      <div className="side-head">
        <div className="brand">
          <div className="brand-mark" />
          <div className="brand-text fade-x">
            <span className="brand-name">RAG</span>
            <span className="brand-sub">Document Intelligence</span>
          </div>
        </div>
        <button className="collapse-btn" onClick={onToggle}
          title={collapsed ? "Развернуть панель" : "Свернуть панель"}>
          <Icon name="panelLeft" size={17} />
        </button>
      </div>

      {collapsed
        ? <RailBody doc={doc} stats={stats} onToggle={onToggle} />
        : <FullBody doc={doc} stats={stats} history={history}
            onUpload={onUpload} onRemove={onRemove} onPickHistory={onPickHistory} />}
    </aside>
  );
}

function FullBody({ doc, stats, history, onUpload, onRemove, onPickHistory }) {
  const [over, setOver] = useState(false);
  const inputRef = useRef(null);

  const handleFiles = (files) => { if (files && files.length) onUpload(files[0]); };

  return (
    <div className="side-body fade-x">
      {/* document */}
      <div className="sec">
        <div className="sec-head"><span className="label">Документ</span></div>
        {!doc && (
          <div className={"drop" + (over ? " over" : "")}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setOver(true); }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => { e.preventDefault(); setOver(false); handleFiles(e.dataTransfer.files); }}>
            <div className="drop-icon"><Icon name="upload" size={19} /></div>
            <div className="drop-title">Нажмите, чтобы выбрать файл, <br/>или перетащите его на основную область</div>
            <div className="drop-formats">PDF · DOCX · TXT</div>
            <input ref={inputRef} type="file" accept=".pdf,.docx,.txt" hidden
              onChange={(e) => handleFiles(e.target.files)} />
          </div>
        )}
        {doc && (
          <div className="doc-card">
            <div className="doc-top">
              <div className="doc-file">{doc.ext}</div>
              <div className="doc-meta">
                <div className="doc-name" title={doc.name}>{doc.name}</div>
                <div className="doc-info">{doc.size} · {doc.pages} стр.</div>
              </div>
              <button className="doc-x" onClick={onRemove} title="Убрать документ"><Icon name="x" size={15} /></button>
            </div>
            <div className="doc-status">
              <Icon name="check" size={13} /> Проиндексирован · {doc.chunks} чанков
            </div>
          </div>
        )}
      </div>

      {/* stats */}
      <div className="sec">
        <div className="sec-head"><span className="label">Статистика</span></div>
        <div className="stats-grid">
          <StatCard val={stats.chunks} label="чанков" spark={stats.chunks ? 100 : 0} />
          <StatCard val={stats.questions} label="вопросов" spark={Math.min(stats.questions * 18, 100)} />
          <StatCard val={stats.confidence ? stats.confidence + "%" : "—"} label="ср. увер." spark={stats.confidence || 0} muted={!stats.confidence} />
          <StatCard val={stats.sources || "—"} label="источников" spark={Math.min((stats.sources || 0) * 12, 100)} muted={!stats.sources} />
        </div>
      </div>

      {/* history */}
      <div className="sec">
        <div className="sec-head"><span className="label">История</span></div>
        <div className="hist-list">
          {history.length === 0 && <div className="hist-empty">Пока нет вопросов</div>}
          {history.map((h, i) => (
            <button key={i} className="hist-item" onClick={() => onPickHistory(h)}>
              <span className="hist-dot" />
              <span className="hist-q">{h}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ val, label, spark = 0, muted }) {
  return (
    <div className="stat">
      <div className={"stat-val" + (muted ? " muted" : "")}>{val}</div>
      <div className="stat-lbl">{label}</div>
      <div className="stat-spark" style={{ width: spark + "%" }} />
    </div>
  );
}

function RailBody({ doc, stats, onToggle }) {
  return (
    <div className="side-body rail">
      <button className={"rail-btn" + (doc ? " active" : "")} onClick={onToggle}>
        <Icon name={doc ? "doc" : "upload"} size={19} />
        <span className="rail-tip">{doc ? "Документ загружен" : "Загрузить документ"}</span>
      </button>
      <div className="rail-div" />
      <button className="rail-btn" onClick={onToggle}>
        <Icon name="chart" size={19} />
        {stats.chunks > 0 && <span className="badge">{stats.chunks}</span>}
        <span className="rail-tip">Статистика · {stats.chunks} чанков</span>
      </button>
      <button className="rail-btn" onClick={onToggle}>
        <Icon name="history" size={19} />
        {stats.questions > 0 && <span className="badge">{stats.questions}</span>}
        <span className="rail-tip">История · {stats.questions} вопросов</span>
      </button>
    </div>
  );
}

/* ===================== Topbar ===================== */
function Topbar({ doc, health, onMenu }) {
  const h = health || { ollama: false, qdrant: false };
  return (
    <header className="topbar">
      <button className="menu-btn" onClick={onMenu} title="Меню" aria-label="Открыть меню">
        <Icon name="menu" size={20} />
      </button>
      <div className="topbar-title">
        <span className="t">{doc ? doc.name : "Новый сеанс"}</span>
        <span className="s">{doc ? "готов к вопросам" : "документ не загружен"}</span>
      </div>
      <div className="topbar-spacer" />
      <div className="pill"><span className={"dot " + (h.ollama ? "green" : "red")} /> ollama</div>
      <div className="pill"><span className={"dot " + (h.qdrant ? "green" : "red")} /> qdrant</div>
    </header>
  );
}

Object.assign(window, { Icon, Sidebar, Topbar });

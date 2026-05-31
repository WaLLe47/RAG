/* ============ Center states: Empty + Processing ============ */

function EmptyState({ onUpload }) {
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);
  const handleFiles = (files) => { if (files && files.length) onUpload(files[0]); };
  return (
    <div className={"center-state drop-area" + (over ? " over" : "")}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={(e) => { if (e.currentTarget === e.target) setOver(false); }}
      onDrop={(e) => { e.preventDefault(); setOver(false); handleFiles(e.dataTransfer.files); }}>
      <div className="empty-mark"><Icon name="diamond" size={26} /></div>
      <div className="empty-title">Загрузите документ</div>
      <div className="empty-sub">
        Добавьте PDF, DOCX или TXT-файл — система разобьёт его на чанки,
        проиндексирует в Qdrant, и вы сможете задавать вопросы на естественном языке.
        Можно перетащить файл прямо сюда.
      </div>
      <button className="empty-cta" onClick={() => inputRef.current?.click()}>
        <Icon name="upload" size={17} /> Выбрать файл
        <input ref={inputRef} type="file" accept=".pdf,.docx,.txt" hidden
          onChange={(e) => handleFiles(e.target.files)} />
      </button>
      <div className="empty-hints">
        <div className="hint"><div className="hint-ic"><Icon name="scan" size={17} /></div>Парсинг</div>
        <div className="hint"><div className="hint-ic"><Icon name="layers" size={17} /></div>Чанкинг</div>
        <div className="hint"><div className="hint-ic"><Icon name="cpu" size={17} /></div>Эмбеддинги</div>
        <div className="hint"><div className="hint-ic"><Icon name="msg" size={17} /></div>Ответы</div>
      </div>
    </div>
  );
}

const PROC_STEPS = [
  { key: "parse", label: "Извлечение текста", meta: "pdfplumber", icon: "scan" },
  { key: "chunk", label: "Разбивка на чанки", meta: "512 токенов · overlap 64", icon: "layers" },
  { key: "embed", label: "Генерация эмбеддингов", meta: "nomic-embed-text", icon: "cpu" },
  { key: "index", label: "Индексация в Qdrant", meta: "cosine · 768d", icon: "diamond" },
];

function ProcessingState({ file, progress, stepIndex }) {
  return (
    <div className="center-state">
      <div className="proc">
        <div className="proc-file">
          <div className="doc-file">{file.ext}</div>
          <div>
            <div className="proc-fname">{file.name}</div>
            <div className="proc-fsize">{file.size}</div>
          </div>
          <div className="proc-pct">{Math.round(progress)}%</div>
        </div>

        <div className="proc-bar">
          <div className="proc-bar-fill" style={{ width: progress + "%" }} />
        </div>

        <div className="steps">
          {PROC_STEPS.map((s, i) => {
            const state = i < stepIndex ? "done" : i === stepIndex ? "active" : "pending";
            return (
              <div key={s.key} className={"step " + state}>
                <div className="step-ic">
                  {state === "done" ? <Icon name="check" size={14} />
                    : state === "active" ? <span className="spin"><Icon name="loader" size={14} /></span>
                    : <Icon name={s.icon} size={14} />}
                </div>
                <div className="step-label">{s.label}</div>
                <div className="step-meta">{s.meta}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { EmptyState, ProcessingState, PROC_STEPS });

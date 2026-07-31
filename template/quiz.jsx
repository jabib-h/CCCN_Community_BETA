/* CCCN Placement test — 15 questions across CEFR levels A1–C2.
   Calculates the highest band where the student gets ≥60% correct. */

const { useState, useMemo } = React;

const QUESTIONS = [
  // A1
  { cefr: "A1", q: "Completá la oración",  s: "Hello, my name ___ Ana.", opts: ["am", "is", "are", "be"], correct: 1 },
  { cefr: "A1", q: "Completá la oración",  s: "I ___ from Costa Rica.", opts: ["is", "be", "am", "are"], correct: 2 },
  { cefr: "A2", q: "Completá la oración",  s: "She ___ to the gym every morning.", opts: ["go", "goes", "going", "is go"], correct: 1 },
  { cefr: "A2", q: "Elegí la mejor opción", s: "Yesterday I ___ pizza for dinner.", opts: ["eat", "eated", "ate", "eaten"], correct: 2 },
  // B1
  { cefr: "B1", q: "Elegí la mejor opción", s: "If I ___ more time, I would learn another language.", opts: ["have", "had", "would have", "having"], correct: 1 },
  { cefr: "B1", q: "Completá la oración",  s: "She has ___ in San José for ten years.", opts: ["lived", "living", "lives", "live"], correct: 0 },
  { cefr: "B1", q: "Elegí la mejor opción", s: "The meeting ___ at 3 p.m. tomorrow.", opts: ["start", "is starting", "started", "starts"], correct: 1 },
  // B2
  { cefr: "B2", q: "Elegí la mejor opción", s: "She wouldn't have missed the flight if she ___ earlier.", opts: ["left", "had left", "would leave", "leaves"], correct: 1 },
  { cefr: "B2", q: "Elegí la palabra correcta", s: "The report needs to be ___ by Friday.", opts: ["submit", "submitting", "submitted", "submission"], correct: 2 },
  { cefr: "B2", q: "Elegí el mejor sinónimo de \"thorough\"", s: "We need a more ___ review.", opts: ["quick", "comprehensive", "casual", "ordinary"], correct: 1 },
  // C1
  { cefr: "C1", q: "Elegí la mejor opción", s: "Had I known about the traffic, I ___ a different route.", opts: ["would take", "took", "would have taken", "have taken"], correct: 2 },
  { cefr: "C1", q: "Elegí la mejor opción", s: "Few candidates, ___, manage to pass on the first attempt.", opts: ["whom", "if any", "of which", "however"], correct: 1 },
  { cefr: "C1", q: "Elegí el significado de \"to put off\"", s: "We had to put off the meeting.", opts: ["cancel", "postpone", "speed up", "attend"], correct: 1 },
  // C2
  { cefr: "C2", q: "Elegí la mejor opción", s: "Notwithstanding the delays, the project ___ on schedule.", opts: ["remains", "remained", "is remaining", "would remain"], correct: 0 },
  { cefr: "C2", q: "Elegí el significado de \"to bite the bullet\"", s: "He had to bite the bullet and apologize.", opts: ["lie", "endure something unpleasant", "celebrate", "refuse"], correct: 1 },
];

const TOTAL = QUESTIONS.length;
const CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"];

const BAND_INFO = {
  A1: { name: "Básico I",        starter: "Básico I",      desc: "Lo justo para presentarte y entender frases del día a día. Es un excelente punto de partida." },
  A2: { name: "Elemental",       starter: "Elemental I",   desc: "Manejás vocabulario diario y podés mantener conversaciones simples. Recomendamos comenzar en Elemental I." },
  B1: { name: "Intermedio",      starter: "Intermedio I",  desc: "Sostenés conversaciones cotidianas con confianza. Es el nivel donde el inglés deja de ser un obstáculo en viajes y trabajo." },
  B2: { name: "Intermedio Alto", starter: "Intermedio Alto I", desc: "Podés trabajar y estudiar en inglés. Ideal para iniciar preparación de pruebas internacionales." },
  C1: { name: "Avanzado",        starter: "Avanzado I",    desc: "Tu inglés es sólido y profesional. Recomendamos perfeccionar con cursos de Avanzado y especialización." },
  C2: { name: "Dominio",         starter: "Dominio I",     desc: "¡Felicidades! Hablás inglés a nivel casi nativo. Te recomendamos nuestros cursos de Dominio o de preparación TOEFL/IELTS." },
};

function computeBand(answers) {
  // For each CEFR band, % correct of that band's questions.
  const stats = {};
  for (const lvl of CEFR_ORDER) stats[lvl] = { correct: 0, total: 0 };
  QUESTIONS.forEach((q, i) => {
    stats[q.cefr].total += 1;
    if (answers[i] === q.correct) stats[q.cefr].correct += 1;
  });
  // Walk up: pick highest band where ≥60% AND all below are ≥60%.
  let placed = "A1";
  for (const lvl of CEFR_ORDER) {
    const s = stats[lvl];
    if (s.total === 0) continue;
    if (s.correct / s.total >= 0.6) placed = lvl;
    else break;
  }
  const correct = QUESTIONS.reduce((acc, q, i) => acc + (answers[i] === q.correct ? 1 : 0), 0);
  return { placed, correct, total: TOTAL, stats };
}

function Letter({ i }) {
  return <span className="opt__letter">{String.fromCharCode(65 + i)}</span>;
}

function StartScreen({ onStart }) {
  return (
    <div className="qcard">
      <div className="qstart">
        <span className="rule-acc">Prueba gratuita</span>
        <h1 className="mt-3">Descubrí <em>tu nivel</em> de inglés en 15 minutos.</h1>
        <p className="lede">Esta prueba diagnóstica mide tu comprensión gramatical y de vocabulario en una escala alineada al Marco Común Europeo (MCER). Es gratuita y sin compromiso.</p>

        <div className="qstart__meta">
          <div>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
            <div><strong>15 minutos</strong><span>{TOTAL} preguntas de opción múltiple</span></div>
          </div>
          <div>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4 12 14.01l-3-3"/></svg>
            <div><strong>Resultado al instante</strong><span>Recibís tu nivel exacto al terminar</span></div>
          </div>
          <div>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1 4 3 6 3s6-2 6-3v-5"/></svg>
            <div><strong>MCER</strong><span>Resultado de A1 a C2 internacional</span></div>
          </div>
        </div>

        <button className="btn btn-primary" onClick={onStart}>
          Comenzar la prueba
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
        </button>
        <p className="small mt-3" style={{ color: "var(--muted)" }}>No se guarda información sin tu permiso. Al final podés pedir asesoría personalizada.</p>
      </div>
    </div>
  );
}

function Question({ idx, q, picked, onPick, onNext, onPrev, canPrev }) {
  const progress = ((idx) / TOTAL) * 100;
  const showFeedback = picked != null;
  // Render sentence with blank highlighted
  const sentence = q.s.replace("___", '<span class="qcard__blank">______</span>');

  return (
    <div className="qcard">
      <div className="qcard__top">
        <div className="qcard__counter">Pregunta <strong>{idx + 1}</strong> de {TOTAL}</div>
        <span className="qcard__cefr">Nivel · {q.cefr}</span>
      </div>
      <div className="qcard__progress"><span style={{ width: progress + "%" }}></span></div>

      <div className="qcard__body">
        <p className="qcard__prompt">{q.q}</p>
        <div className="qcard__sentence" dangerouslySetInnerHTML={{ __html: sentence }} />

        <div className="opts">
          {q.opts.map((o, i) => {
            let cls = "opt";
            if (showFeedback) {
              if (i === q.correct) cls += " is-correct";
              else if (i === picked) cls += " is-wrong";
            } else if (i === picked) {
              cls += " is-selected";
            }
            return (
              <button key={i} className={cls} onClick={() => !showFeedback && onPick(i)} disabled={showFeedback}>
                <Letter i={i} />
                <span className="opt__text">{o}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="qcard__foot">
        <button
          className="btn btn-ghost"
          onClick={onPrev}
          disabled={!canPrev}
          style={{ visibility: canPrev ? "visible" : "hidden" }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m15 18-6-6 6-6"/></svg>
          Anterior
        </button>
        <div className="qcard__skip">
          <button onClick={() => onPick(-1)}>No sé esta — saltar</button>
        </div>
        <button className="btn btn-primary" onClick={onNext} disabled={picked == null}>
          {idx + 1 === TOTAL ? "Ver mi resultado" : "Siguiente"}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  );
}

function Result({ result, onRestart }) {
  const info = BAND_INFO[result.placed];
  return (
    <div className="qresult">
      <div className="qresult__top">
        <span className="rule-acc" style={{ color: "#fff" }}>Tu nivel CCCN</span>
        <div className="qresult__big">{result.placed.charAt(0)}<em>{result.placed.charAt(1)}</em></div>
        <div className="qresult__label">{info.name}</div>
        <div className="qresult__score">{result.correct} de {result.total} respuestas correctas</div>
      </div>
      <div className="qresult__body">
        <p className="qresult__lede">{info.desc}</p>

        <div className="qresult__bands">
          {CEFR_ORDER.map(lvl => {
            const here = lvl === result.placed;
            return (
              <div key={lvl} className={"qresult__band" + (here ? " is-here" : "")}>
                <strong>{lvl}</strong>
                <span>{BAND_INFO[lvl].name}</span>
                {here && <span style={{ marginLeft: "auto", fontSize: 12, letterSpacing: ".1em", textTransform: "uppercase" }}>Tu nivel</span>}
              </div>
            );
          })}
        </div>

        <div style={{ background: "var(--cream)", borderRadius: 12, padding: 24, marginTop: 8 }}>
          <strong style={{ color: "var(--cccn-blue-900)", display: "block", marginBottom: 8 }}>Recomendación: empezá en <span style={{ color: "var(--cccn-red)" }}>{info.starter}</span></strong>
          <span className="small" style={{ color: "var(--muted)" }}>Un asesor confirmará tu ubicación con una entrevista corta de 10 minutos antes de matricularte.</span>
        </div>

        <div className="qresult__cta">
          <a className="btn btn-primary" href="solicitar-informacion.html">Solicitar información</a>
          <a className="btn btn-dark" href="programa-adultos.html#horarios">Ver horarios disponibles</a>
          <button className="btn btn-ghost" onClick={onRestart}>Hacer la prueba de nuevo</button>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [phase, setPhase] = useState("start");      // start | quiz | result
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState({});       // {questionIdx: optionIdx}

  const result = useMemo(() => phase === "result" ? computeBand(answers) : null, [phase, answers]);

  const handleStart = () => { setIdx(0); setAnswers({}); setPhase("quiz"); };
  const handlePick = (optIdx) => setAnswers(prev => ({ ...prev, [idx]: optIdx }));
  const handleNext = () => {
    if (idx + 1 >= TOTAL) setPhase("result");
    else setIdx(i => i + 1);
  };
  const handlePrev = () => setIdx(i => Math.max(0, i - 1));

  if (phase === "start")  return <StartScreen onStart={handleStart} />;
  if (phase === "result") return <Result result={result} onRestart={handleStart} />;

  return (
    <Question
      idx={idx}
      q={QUESTIONS[idx]}
      picked={answers[idx] ?? null}
      onPick={handlePick}
      onNext={handleNext}
      onPrev={handlePrev}
      canPrev={idx > 0}
    />
  );
}

const root = ReactDOM.createRoot(document.getElementById("app"));
root.render(<App />);

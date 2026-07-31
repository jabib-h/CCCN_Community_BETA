/* Multi-step lead form with real validation + state.
   Steps:
   1. About you (perfil, nivel, motivación)
   2. Your details (nombre, email, teléfono)
   3. Modalidad + sede + horario
   4. Confirmación + send
*/
const { useState, useMemo } = React;

const STEPS = ["Perfil", "Datos", "Preferencias", "Confirmar"];

const PROFILES = [
  { id: "particular",   title: "Particular",      meta: "Estudio personal / desarrollo" },
  { id: "profesional",  title: "Profesional",     meta: "Para mi trabajo o carrera" },
  { id: "universitario",title: "Estudiante universitario", meta: "Apoyo académico" },
  { id: "empresa",      title: "Empresa",         meta: "Capacitación para equipos" },
];

const LEVELS = [
  { id: "ninguno",   title: "Ninguno",      meta: "Nunca lo he estudiado formalmente" },
  { id: "basico",    title: "Básico",       meta: "Lo manejo con dificultad" },
  { id: "intermedio",title: "Intermedio",   meta: "Me defiendo bien" },
  { id: "avanzado",  title: "Avanzado",     meta: "Sólido, busco perfeccionar" },
];

const MODES = [
  { id: "presencial",title: "Presencial",         meta: "Asistencia a la sede" },
  { id: "hibrida",   title: "Híbrida",            meta: "1 presencial + 1 virtual" },
  { id: "virtual",   title: "Virtual en vivo",    meta: "Por Zoom desde donde estés" },
];

const SEDES = ["San Pedro", "Sabana", "Heredia", "Cartago", "Virtual"];
const HORARIOS = [
  "Mañana (7 a.m. – 12 m.)",
  "Tarde (12 m. – 5 p.m.)",
  "Noche (5 p.m. – 9 p.m.)",
  "Sábados",
];

function StepNav({ current, total }) {
  return (
    <>
      <div className="steps">
        {Array.from({ length: total }).map((_, i) => (
          <div key={i} className={"step" + (i < current ? " is-done" : i === current ? " is-current" : "")} />
        ))}
      </div>
      <div className="step-meta">
        <span>Paso <strong>{String(current + 1).padStart(2, "0")}</strong> de {String(total).padStart(2, "0")}</span>
        <span>{STEPS[current]}</span>
      </div>
    </>
  );
}

function RCards({ items, value, onChange, multi = false }) {
  const selected = multi ? new Set(value || []) : value;
  const isSel = (id) => multi ? selected.has(id) : selected === id;
  const toggle = (id) => {
    if (multi) {
      const next = new Set(selected); if (next.has(id)) next.delete(id); else next.add(id);
      onChange([...next]);
    } else { onChange(id); }
  };
  return (
    <div className="rcards">
      {items.map(it => (
        <label key={it.id} className={"rcard" + (isSel(it.id) ? " is-selected" : "")}>
          <input type={multi ? "checkbox" : "radio"} checked={isSel(it.id)} onChange={() => toggle(it.id)} name="rc"/>
          <span className="rcard__title">{it.title}</span>
          <span className="rcard__meta">{it.meta}</span>
          <span className="rcard__check"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span>
        </label>
      ))}
    </div>
  );
}

function Step1({ data, set, errors }) {
  return (
    <>
      <h2 className="step-title">Contanos <em>quién sos</em>.</h2>
      <p className="step-sub">Esto nos ayuda a recomendarte el programa más adecuado.</p>
      <div className="fields">
        <div className="field">
          <label>¿En qué perfil te identificás?</label>
          <RCards items={PROFILES} value={data.profile} onChange={v => set({ profile: v })}/>
          {errors.profile && <span className="hint" style={{ color: "var(--cccn-red)" }}>Por favor seleccioná un perfil.</span>}
        </div>
        <div className="field">
          <label>¿Cuál es tu nivel actual de inglés?</label>
          <RCards items={LEVELS} value={data.level} onChange={v => set({ level: v })}/>
          {errors.level && <span className="hint" style={{ color: "var(--cccn-red)" }}>Indicanos tu nivel actual.</span>}
        </div>
      </div>
    </>
  );
}

function Step2({ data, set, errors }) {
  return (
    <>
      <h2 className="step-title">Tus <em>datos</em>.</h2>
      <p className="step-sub">Te contactaremos en menos de 24 horas hábiles. No compartimos tu información con terceros.</p>
      <div className="fields">
        <div className="field-row">
          <div className={"field" + (errors.firstName ? " is-error" : "")}>
            <label htmlFor="fn">Nombre</label>
            <input id="fn" value={data.firstName} onChange={e => set({ firstName: e.target.value })} placeholder="Ana"/>
            {errors.firstName && <span className="hint">Indicanos tu nombre.</span>}
          </div>
          <div className={"field" + (errors.lastName ? " is-error" : "")}>
            <label htmlFor="ln">Apellidos</label>
            <input id="ln" value={data.lastName} onChange={e => set({ lastName: e.target.value })} placeholder="Solís Vargas"/>
            {errors.lastName && <span className="hint">Indicanos tus apellidos.</span>}
          </div>
        </div>
        <div className={"field" + (errors.email ? " is-error" : "")}>
          <label htmlFor="em">Correo electrónico</label>
          <input id="em" type="email" value={data.email} onChange={e => set({ email: e.target.value })} placeholder="ana@correo.com"/>
          {errors.email && <span className="hint">{errors.email}</span>}
        </div>
        <div className={"field" + (errors.phone ? " is-error" : "")}>
          <label htmlFor="ph">Teléfono</label>
          <input id="ph" value={data.phone} onChange={e => set({ phone: e.target.value })} placeholder="8888-8888"/>
          {errors.phone && <span className="hint">{errors.phone}</span>}
        </div>
        <label className="checkbox">
          <input type="checkbox" checked={data.whatsapp} onChange={e => set({ whatsapp: e.target.checked })}/>
          <span>Prefiero que me contacten por WhatsApp.</span>
        </label>
      </div>
    </>
  );
}

function Step3({ data, set, errors }) {
  return (
    <>
      <h2 className="step-title">Tus <em>preferencias</em>.</h2>
      <p className="step-sub">No te preocupes — un asesor confirmará los detalles contigo.</p>
      <div className="fields">
        <div className="field">
          <label>¿Cuál modalidad te interesa?</label>
          <RCards items={MODES} value={data.mode} onChange={v => set({ mode: v })}/>
          {errors.mode && <span className="hint" style={{ color: "var(--cccn-red)" }}>Seleccioná una modalidad.</span>}
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="sd">Sede preferida</label>
            <select id="sd" value={data.sede} onChange={e => set({ sede: e.target.value })}>
              <option value="">Seleccioná una sede</option>
              {SEDES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="ho">Franja horaria</label>
            <select id="ho" value={data.horario} onChange={e => set({ horario: e.target.value })}>
              <option value="">Cualquier horario</option>
              {HORARIOS.map(h => <option key={h} value={h}>{h}</option>)}
            </select>
          </div>
        </div>
        <div className="field">
          <label htmlFor="nt">Notas adicionales <span style={{ color: "var(--muted)", fontWeight: 400 }}>· opcional</span></label>
          <textarea id="nt" rows="3" value={data.notes} onChange={e => set({ notes: e.target.value })} placeholder="Necesito el curso para una entrevista en marzo..."></textarea>
        </div>
      </div>
    </>
  );
}

function Step4({ data, onEdit }) {
  const label = (id, list) => list.find(x => x.id === id)?.title || "—";
  return (
    <>
      <h2 className="step-title">Revisemos <em>tus datos</em>.</h2>
      <p className="step-sub">Verificá la información antes de enviar tu solicitud.</p>

      <div className="summary">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <strong style={{ color: "var(--cccn-blue-900)", fontSize: 14, letterSpacing: ".1em", textTransform: "uppercase" }}>Sobre ti</strong>
          <button className="summary__edit" onClick={() => onEdit(0)}>Editar</button>
        </div>
        <dl>
          <dt>Perfil</dt><dd>{label(data.profile, PROFILES)}</dd>
          <dt>Nivel actual</dt><dd>{label(data.level, LEVELS)}</dd>
        </dl>
      </div>

      <div className="summary" style={{ marginTop: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <strong style={{ color: "var(--cccn-blue-900)", fontSize: 14, letterSpacing: ".1em", textTransform: "uppercase" }}>Tus datos</strong>
          <button className="summary__edit" onClick={() => onEdit(1)}>Editar</button>
        </div>
        <dl>
          <dt>Nombre</dt><dd>{data.firstName} {data.lastName}</dd>
          <dt>Correo</dt><dd>{data.email}</dd>
          <dt>Teléfono</dt><dd>{data.phone} {data.whatsapp ? "· prefiere WhatsApp" : ""}</dd>
        </dl>
      </div>

      <div className="summary" style={{ marginTop: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <strong style={{ color: "var(--cccn-blue-900)", fontSize: 14, letterSpacing: ".1em", textTransform: "uppercase" }}>Preferencias</strong>
          <button className="summary__edit" onClick={() => onEdit(2)}>Editar</button>
        </div>
        <dl>
          <dt>Modalidad</dt><dd>{label(data.mode, MODES)}</dd>
          <dt>Sede</dt><dd>{data.sede || "Sin preferencia"}</dd>
          <dt>Horario</dt><dd>{data.horario || "Cualquier horario"}</dd>
          {data.notes && <><dt>Notas</dt><dd style={{ fontWeight: 400, color: "var(--muted)" }}>{data.notes}</dd></>}
        </dl>
      </div>

      <label className="checkbox" style={{ marginTop: 16 }}>
        <input type="checkbox" id="terms" defaultChecked/>
        <span>Acepto las <a href="#" style={{ color: "var(--cccn-red)", textDecoration: "underline" }}>políticas de privacidad</a> del CCCN.</span>
      </label>
    </>
  );
}

function Success({ data }) {
  const caseNum = "CCCN-" + (Math.floor(Math.random() * 90000) + 10000);
  return (
    <div className="success">
      <div className="success__icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
      </div>
      <h2>¡Solicitud <em>enviada</em>!</h2>
      <p>Gracias, {data.firstName}. Te contactaremos al {data.email} o al {data.phone} en menos de 24 horas hábiles.</p>
      <div className="success__case">N° de caso: {caseNum}</div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center", marginTop: 12 }}>
        <a className="btn btn-primary" href="prueba-ubicacion.html">Hacer prueba de ubicación</a>
        <a className="btn btn-ghost" href="index.html">Volver al inicio</a>
      </div>
    </div>
  );
}

function validateStep(step, data) {
  const e = {};
  if (step === 0) {
    if (!data.profile) e.profile = true;
    if (!data.level)   e.level = true;
  }
  if (step === 1) {
    if (!data.firstName.trim()) e.firstName = true;
    if (!data.lastName.trim())  e.lastName = true;
    if (!data.email.trim()) e.email = "Indicanos tu correo.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) e.email = "Ingresá un correo válido.";
    if (!data.phone.trim()) e.phone = "Indicanos un teléfono.";
    else if (data.phone.replace(/\D/g, "").length < 8) e.phone = "Mínimo 8 dígitos.";
  }
  if (step === 2) {
    if (!data.mode) e.mode = true;
  }
  return e;
}

function App() {
  const [step, setStep] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState({});
  const [data, setData] = useState({
    profile: "", level: "",
    firstName: "", lastName: "", email: "", phone: "", whatsapp: false,
    mode: "", sede: "", horario: "", notes: "",
  });
  const set = (patch) => setData(d => ({ ...d, ...patch }));

  const next = () => {
    const errs = validateStep(step, data);
    setErrors(errs);
    if (Object.keys(errs).length === 0) {
      if (step < STEPS.length - 1) setStep(step + 1);
      else setSubmitted(true);
    }
  };
  const prev = () => { setErrors({}); setStep(Math.max(0, step - 1)); };
  const goTo = (s) => { setErrors({}); setStep(s); };

  if (submitted) return <Success data={data}/>;

  return (
    <>
      <StepNav current={step} total={STEPS.length}/>
      {step === 0 && <Step1 data={data} set={set} errors={errors}/>}
      {step === 1 && <Step2 data={data} set={set} errors={errors}/>}
      {step === 2 && <Step3 data={data} set={set} errors={errors}/>}
      {step === 3 && <Step4 data={data} onEdit={goTo}/>}

      <div className="foot">
        <button className="btn btn-ghost" onClick={prev} disabled={step === 0} style={{ visibility: step === 0 ? "hidden" : "visible" }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m15 18-6-6 6-6"/></svg>
          Anterior
        </button>
        <button className="btn btn-primary" onClick={next}>
          {step === STEPS.length - 1 ? "Enviar solicitud" : "Continuar"}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
        </button>
      </div>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("app")).render(<App />);

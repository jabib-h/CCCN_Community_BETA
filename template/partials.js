/* ============================================================
   Shared site shell: header (with mobile drawer) + footer.
   Each page calls CCCN.renderShell({ active }).
   Also provides:
   - CCCN.toast(msg) for confirmations
   - CCCN.heroPlaceholder(el, opts) — paints a photographic-style
     scene into a container using layered CSS gradients + SVG
   ============================================================ */
(function () {
  const NAV = [
    { id: "nosotros",  href: "nosotros.html",            label: "Nosotros" },
    { id: "programa",  href: "programa-adultos.html",    label: "Programa adultos" },
    { id: "niveles",   href: "niveles.html",             label: "Niveles" },
    { id: "sedes",     href: "sedes.html",               label: "Sedes" },
    { id: "prueba",    href: "prueba-ubicacion.html",    label: "Prueba de ubicación" },
  ];

  function svgIcon(name) {
    const icons = {
      menu:    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>',
      close:   '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
      search:  '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
      arrow:   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>',
      whatsapp:'<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163a11.867 11.867 0 0 1-1.587-5.946C.16 5.335 5.495 0 12.05 0a11.81 11.81 0 0 1 8.413 3.488 11.819 11.819 0 0 1 3.48 8.414c-.003 6.557-5.34 11.892-11.893 11.892a11.9 11.9 0 0 1-5.688-1.448L.057 24zM6.597 20.13c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.881.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.88a9.86 9.86 0 0 0 1.51 5.26l-.999 3.648 3.978-1.607zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479c0 1.462 1.065 2.875 1.213 3.074.149.198 2.095 3.2 5.076 4.487.71.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.29.173-1.414z"/></svg>',
      fb:      '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M22 12a10 10 0 1 0-11.56 9.88v-6.99H7.9V12h2.54V9.8c0-2.5 1.5-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56V12h2.77l-.44 2.89h-2.33v6.99A10 10 0 0 0 22 12z"/></svg>',
      ig:      '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.2c3.2 0 3.58 0 4.85.07 1.17.05 1.8.25 2.23.42a3.7 3.7 0 0 1 1.37.9c.42.43.7.84.9 1.36.16.42.36 1.06.42 2.23C21.96 8.42 22 8.8 22 12s0 3.58-.07 4.85c-.05 1.17-.26 1.8-.42 2.23a3.7 3.7 0 0 1-.9 1.37 3.7 3.7 0 0 1-1.37.9c-.42.16-1.06.36-2.23.42-1.27.06-1.65.07-4.85.07s-3.58 0-4.85-.07c-1.17-.06-1.8-.26-2.23-.42a3.7 3.7 0 0 1-1.37-.9 3.7 3.7 0 0 1-.9-1.37c-.16-.42-.36-1.06-.42-2.23C2.04 15.58 2 15.2 2 12s0-3.58.07-4.85c.06-1.17.26-1.81.42-2.23.21-.52.49-.93.9-1.36.43-.42.84-.7 1.37-.9.42-.17 1.06-.37 2.23-.42C8.42 2.2 8.8 2.2 12 2.2zm0 1.8c-3.15 0-3.5 0-4.74.07-1.13.05-1.74.24-2.15.4-.54.21-.93.46-1.34.86-.4.4-.65.8-.86 1.34-.16.4-.35 1.02-.4 2.15C2.43 8.5 2.4 8.85 2.4 12s0 3.5.07 4.74c.05 1.13.24 1.74.4 2.15.21.54.46.93.86 1.34.4.4.8.65 1.34.86.4.16 1.02.35 2.15.4 1.24.07 1.59.07 4.74.07s3.5 0 4.74-.07c1.13-.05 1.74-.24 2.15-.4.54-.21.93-.46 1.34-.86.4-.4.65-.8.86-1.34.16-.4.35-1.02.4-2.15.07-1.24.07-1.59.07-4.74s0-3.5-.07-4.74c-.05-1.13-.24-1.74-.4-2.15a3.6 3.6 0 0 0-.86-1.34 3.6 3.6 0 0 0-1.34-.86c-.4-.16-1.02-.35-2.15-.4C15.5 4 15.15 4 12 4zm0 3.16a4.84 4.84 0 1 1 0 9.68 4.84 4.84 0 0 1 0-9.68zm0 8a3.16 3.16 0 1 0 0-6.32 3.16 3.16 0 0 0 0 6.32zm6.16-8.19a1.13 1.13 0 1 1-2.26 0 1.13 1.13 0 0 1 2.26 0z"/></svg>',
      yt:      '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.6 3.6 12 3.6 12 3.6s-7.6 0-9.4.5A3 3 0 0 0 .5 6.2C0 8 0 12 0 12s0 4 .5 5.8a3 3 0 0 0 2.1 2.1c1.8.5 9.4.5 9.4.5s7.6 0 9.4-.5a3 3 0 0 0 2.1-2.1c.5-1.8.5-5.8.5-5.8s0-4-.5-5.8zM9.6 15.6V8.4l6.3 3.6-6.3 3.6z"/></svg>',
      ln:      '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.95v5.66H9.36V9h3.41v1.56h.05c.48-.9 1.64-1.86 3.37-1.86 3.6 0 4.27 2.37 4.27 5.45v6.3zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.55V9h3.57v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/></svg>',
      pin:     '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 1 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>',
      check:   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
      chev:    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="m9 6 6 6-6 6"/></svg>',
      chevL:   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="m15 18-6-6 6-6"/></svg>',
      star:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="m12 17.3-6.18 3.7 1.64-7.03L2 9.24l7.19-.62L12 2l2.81 6.62 7.19.62-5.46 4.73L18.18 21z"/></svg>',
    };
    return icons[name] || "";
  }

  function header(active) {
    const links = NAV.map(n => `<a href="${n.href}" class="${active === n.id ? "is-active" : ""}">${n.label}</a>`).join("");
    return `
    <header class="site-header">
      <div class="strip-flag"></div>
      <div class="container site-header__bar">
        <a class="site-header__logo" href="index.html" aria-label="CCCN inicio">
          <img src="assets/logo.png" alt="Centro Cultural Costarricense Norteamericano"/>
        </a>
        <nav class="site-header__nav" aria-label="Principal">
          ${links}
        </nav>
        <div class="site-header__cta">
          <a class="btn btn-ghost hide-mobile" href="solicitar-informacion.html">Solicitar información</a>
          <a class="btn btn-primary" href="prueba-ubicacion.html">Quiero estudiar inglés ${svgIcon("arrow")}</a>
          <button class="btn-icon site-header__menu-btn" aria-label="Abrir menú" data-mnav-open>${svgIcon("menu")}</button>
        </div>
      </div>
    </header>
    <div class="mnav" data-mnav>
      <div class="mnav__panel">
        <button class="btn-icon mnav__close" aria-label="Cerrar menú" data-mnav-close>${svgIcon("close")}</button>
        ${NAV.map(n => `<a href="${n.href}">${n.label}</a>`).join("")}
        <a href="solicitar-informacion.html">Solicitar información</a>
        <a href="nosotros.html#aula-virtual">Portal estudiantil</a>
        <div style="margin-top:auto;color:var(--muted);font-size:13px;">Call Center · 8000-INGLES</div>
      </div>
    </div>`;
  }

  function footer() {
    return `
    <footer class="site-footer">
      <div class="container">
        <div class="site-footer__grid">
          <div class="site-footer__brand">
            <img src="assets/logo-white.png" alt="CCCN"/>
            <p style="max-width: 34ch; color: #B8C2D9; font-size: 14px;">Asociación sin fines de lucro fundada en 1945, declarada de utilidad pública y avalada por el Departamento de Estado de los Estados Unidos.</p>
            <div class="site-footer__social" aria-label="Redes sociales">
              <a href="#" aria-label="Facebook">${svgIcon("fb")}</a>
              <a href="#" aria-label="Instagram">${svgIcon("ig")}</a>
              <a href="#" aria-label="LinkedIn">${svgIcon("ln")}</a>
              <a href="#" aria-label="YouTube">${svgIcon("yt")}</a>
              <a href="#" aria-label="WhatsApp">${svgIcon("whatsapp")}</a>
            </div>
          </div>
          <div>
            <h4 class="site-footer__title">Aprendé inglés</h4>
            <ul class="site-footer__list">
              <li><a href="programa-adultos.html">Programa para adultos</a></li>
              <li><a href="niveles.html">Niveles y metodología</a></li>
              <li><a href="prueba-ubicacion.html">Prueba de ubicación</a></li>
              <li><a href="programa-adultos.html#horarios">Horarios y modalidades</a></li>
              <li><a href="programa-adultos.html#precios">Precios y matrícula</a></li>
            </ul>
          </div>
          <div>
            <h4 class="site-footer__title">Institución</h4>
            <ul class="site-footer__list">
              <li><a href="nosotros.html">Nosotros</a></li>
              <li><a href="nosotros.html#historia">80 años de historia</a></li>
              <li><a href="nosotros.html#gestion">Gestión social</a></li>
              <li><a href="sedes.html">Sedes</a></li>
              <li><a href="solicitar-informacion.html">Contacto</a></li>
            </ul>
          </div>
          <div>
            <h4 class="site-footer__title">Hablemos</h4>
            <ul class="site-footer__list">
              <li><strong style="color:#fff;font-size:18px;">8000-INGLES</strong></li>
              <li>Call center · Lun a Vie · 8 a.m. – 8 p.m.</li>
              <li><a href="mailto:info@centrocultural.cr">info@centrocultural.cr</a></li>
              <li><a href="#">WhatsApp · +506 8821-8484</a></li>
            </ul>
          </div>
        </div>
        <div class="site-footer__bottom">
          <div>© 2026 Centro Cultural Costarricense Norteamericano — Asociación sin fines de lucro declarada de utilidad pública</div>
          <div style="display:flex; gap:18px; flex-wrap:wrap;">
            <a href="#">Políticas de privacidad</a>
            <a href="#">Reglamento estudiantil</a>
            <a href="#">Términos</a>
          </div>
        </div>
      </div>
    </footer>`;
  }

  function wireMobileNav() {
    const drawer = document.querySelector("[data-mnav]");
    if (!drawer) return;
    document.querySelectorAll("[data-mnav-open]").forEach(b => b.addEventListener("click", () => drawer.classList.add("is-open")));
    document.querySelectorAll("[data-mnav-close]").forEach(b => b.addEventListener("click", () => drawer.classList.remove("is-open")));
    drawer.addEventListener("click", (e) => { if (e.target === drawer) drawer.classList.remove("is-open"); });
  }

  function renderShell({ active } = {}) {
    const headerHost = document.querySelector("[data-site-header]");
    const footerHost = document.querySelector("[data-site-footer]");
    if (headerHost) headerHost.outerHTML = header(active);
    if (footerHost) footerHost.outerHTML = footer();
    wireMobileNav();
  }

  function toast(msg) {
    const el = document.createElement("div");
    el.textContent = msg;
    Object.assign(el.style, {
      position: "fixed", bottom: "24px", left: "50%", transform: "translateX(-50%) translateY(20px)",
      background: "var(--cccn-blue-900)", color: "#fff", padding: "12px 18px",
      borderRadius: "999px", fontWeight: "600", fontSize: "14px", zIndex: 9999,
      boxShadow: "0 12px 32px -8px rgba(0,0,0,.3)", opacity: "0", transition: "opacity .2s ease, transform .2s ease"
    });
    document.body.appendChild(el);
    requestAnimationFrame(() => { el.style.opacity = "1"; el.style.transform = "translateX(-50%) translateY(0)"; });
    setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(-50%) translateY(20px)"; }, 2200);
    setTimeout(() => el.remove(), 2500);
  }

  window.CCCN = { renderShell, svgIcon, toast };
})();

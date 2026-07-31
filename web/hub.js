/* Portada autenticada. Todo el contenido llega ya filtrado por el servidor
   (/hub/inicio): acá solo se dibuja. Nunca se decide acceso en el navegador. */
(() => {
  'use strict';
  const { esc, fmtDate, fmtMoney, toast } = window.ui;
  const api = window.cccn;

  const ESTADO = {
    activo: { txt: 'Disponible', cls: 'pill' },
    en_construccion: { txt: 'En construcción', cls: 'pill pill-cream' },
  };

  function tarjeta(m) {
    const disponible = m.estado === 'activo' && m.permitido;
    const badge = ESTADO[m.estado] || ESTADO.en_construccion;
    const nota = m.permitido
      ? (m.estado === 'activo' ? '' : 'Este servicio todavía no está abierto.')
      : `Requiere membresía de ${esc(m.requiere_membresia)} vigente.`;

    const cuerpo = `
      <div class="mod__bar mod__bar--${esc(m.slug)}"></div>
      <div class="card__body">
        <span class="card__tag">${badge.txt}</span>
        <h3 class="card__title">${esc(m.nombre)}</h3>
        <p class="card__desc">${esc(m.descripcion)}</p>
        ${nota ? `<p class="small mod__nota">${nota}</p>` : ''}
        ${disponible ? `<span class="card__cta">Abrir${m.externo ? ' ↗' : ' →'}</span>` : ''}
      </div>`;

    if (!disponible) return `<article class="card mod is-locked">${cuerpo}</article>`;
    // rel="noopener": una pestaña externa no debe poder tocar la nuestra vía window.opener.
    const externo = m.externo ? ' target="_blank" rel="noopener noreferrer"' : '';
    return `<a class="card mod" href="${esc(m.href)}"${externo}>${cuerpo}</a>`;
  }

  function membresia(m) {
    const vencida = m.vence_at && new Date(m.vence_at) < new Date();
    const estado = vencida ? 'vencida' : m.estado;
    const cls = estado === 'activa' ? 'pill' : 'pill pill-red';
    const cuando = m.vence_at ? `vence ${fmtDate(m.vence_at)}` : 'sin vencimiento';
    return `<li class="memb">
        <span class="${cls}">${esc(m.tipo)}</span>
        <span class="small muted">${esc(estado)} · ${cuando}</span>
      </li>`;
  }

  async function cargar() {
    const me = await api.requireAuth();
    if (!me) return;

    let data;
    try {
      data = await api.get('/hub/inicio');
    } catch (e) {
      toast(e.message, true);
      return;
    }

    const nombre = data.usuario.display_name || data.usuario.email;
    document.getElementById('saludo').textContent = `Hola, ${nombre}`;
    document.getElementById('quien').textContent = data.usuario.role;

    document.getElementById('modulos').innerHTML = data.modulos.map(tarjeta).join('');

    const membs = data.membresias;
    document.getElementById('membresias').innerHTML = membs.length
      ? `<ul class="membs">${membs.map(membresia).join('')}</ul>`
      : '<p class="muted small">No tenés membresías registradas. Consultá en tu sede para activarlas.</p>';

    const cargos = data.cargos_pendientes;
    if (cargos.length) {
      document.getElementById('avisos').hidden = false;
      document.getElementById('avisos-lista').innerHTML = cargos.map((c) => `
        <li class="aviso">
          <span>${esc(c.descripcion)}</span>
          <strong>${fmtMoney(c.monto_centimos, c.moneda)}</strong>
          ${c.vence_at ? `<span class="small muted">vence ${fmtDate(c.vence_at)}</span>` : ''}
        </li>`).join('');
    }
  }

  document.getElementById('salir').addEventListener('click', () => api.logout());
  cargar();
})();

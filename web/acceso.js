/* Ingreso y registro. La validación de acá es cortesía para la persona usuaria;
   la que cuenta (consentimiento, edad, fortaleza de clave) la hace el servidor. */
(() => {
  'use strict';
  const api = window.cccn;
  const { toast } = window.ui;

  const $ = (id) => document.getElementById(id);

  // El destino sale de ?next= pero se acepta solo si es una ruta interna:
  // un next=//sitio-externo sería un redirect abierto.
  function destino() {
    const next = new URLSearchParams(location.search).get('next') || '';
    return /^\/app\/[^/]/.test(next) ? next : '/app/hub.html';
  }

  const paneles = { login: $('panel-login'), registro: $('panel-registro') };
  const tabs = { login: $('tab-login'), registro: $('tab-registro') };

  Object.keys(tabs).forEach((k) => {
    tabs[k].addEventListener('click', () => {
      Object.keys(tabs).forEach((o) => {
        const activo = o === k;
        tabs[o].classList.toggle('is-active', activo);
        tabs[o].setAttribute('aria-selected', String(activo));
        paneles[o].hidden = !activo;
      });
    });
  });

  function bloquear(form, on) {
    form.querySelectorAll('button[type=submit]').forEach((b) => { b.disabled = on; });
  }

  paneles.login.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    bloquear(paneles.login, true);
    try {
      const { token } = await api.post('/auth/login', {
        email: $('l-email').value.trim(), password: $('l-pass').value,
      });
      api.setToken(token);
      location.href = destino();
    } catch (e) {
      toast(e.message, true);
    } finally {
      bloquear(paneles.login, false);
    }
  });

  paneles.registro.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    if (!($('r-priv').checked && $('r-tos').checked)) {
      toast('Para crear la cuenta debés aceptar ambas políticas.', true);
      return;
    }
    bloquear(paneles.registro, true);
    try {
      const { token } = await api.post('/auth/register', {
        email: $('r-email').value.trim(),
        password: $('r-pass').value,
        nombre: $('r-nombre').value.trim(),
        fecha_nacimiento: $('r-nac').value,
        accept_privacy: true,
        accept_tos: true,
      });
      api.setToken(token);
      location.href = destino();
    } catch (e) {
      toast(e.message, true);
    } finally {
      bloquear(paneles.registro, false);
    }
  });

  if (api.isAuthed()) location.href = destino();
})();

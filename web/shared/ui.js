/* Helpers de UI compartidos — sin dependencias, sin inline. */
(() => {
  'use strict';

  const ui = {
    esc(s) {
      return String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    },

    toast(msg, isError = false) {
      const el = document.getElementById('toast');
      if (!el) return;
      el.textContent = msg;
      el.classList.toggle('err', isError);
      el.classList.add('show');
      clearTimeout(ui._t);
      ui._t = setTimeout(() => el.classList.remove('show'), 3200);
    },

    fmtDate(iso) {
      if (!iso) return '';
      const d = new Date(iso);
      return d.toLocaleDateString('es-CR', { day: 'numeric', month: 'long', year: 'numeric' });
    },

    // Los montos viajan en céntimos (enteros) — ver api/db.py, tabla `cargos`.
    fmtMoney(centimos, moneda = 'CRC') {
      return new Intl.NumberFormat('es-CR', { style: 'currency', currency: moneda })
        .format((centimos || 0) / 100);
    },
  };

  window.ui = ui;
})();

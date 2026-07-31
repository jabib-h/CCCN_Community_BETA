/* Cliente de API compartido — CCCN Hub.
   Mismo origen que la API (servido por FastAPI) → fetch relativo, JWT en sessionStorage.
   Sin dependencias, sin inline (cumple CSP default-src 'none').
   sessionStorage y no localStorage: la sesión muere al cerrar la pestaña. */
(() => {
  'use strict';

  const TOKEN_KEY = 'cccn_hub_token';

  // OAuth devuelve el token en el fragment (#token=...). Lo capturamos y limpiamos la URL.
  const frag = new URLSearchParams(location.hash.slice(1));
  if (frag.get('token')) {
    sessionStorage.setItem(TOKEN_KEY, frag.get('token'));
    history.replaceState(null, '', location.pathname + location.search);
  }

  const api = {
    token: () => sessionStorage.getItem(TOKEN_KEY),
    setToken: (t) => sessionStorage.setItem(TOKEN_KEY, t),
    clear: () => sessionStorage.removeItem(TOKEN_KEY),
    isAuthed: () => !!sessionStorage.getItem(TOKEN_KEY),

    async request(method, path, { body, isForm } = {}) {
      const headers = {};
      const tok = api.token();
      if (tok) headers.Authorization = `Bearer ${tok}`;
      let payload;
      if (isForm) {
        payload = body; // FormData
      } else if (body !== undefined) {
        headers['Content-Type'] = 'application/json';
        payload = JSON.stringify(body);
      }
      const res = await fetch(`/api/v1${path}`, { method, headers, body: payload });
      if (res.status === 204) return null;
      let data = null;
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) data = await res.json();
      if (!res.ok) {
        const err = new Error((data && data.detail) || `Error ${res.status}`);
        err.status = res.status;
        err.data = data;
        throw err;
      }
      return data;
    },
    get: (p) => api.request('GET', p),
    post: (p, body) => api.request('POST', p, { body }),
    patch: (p, body) => api.request('PATCH', p, { body }),
    postForm: (p, form) => api.request('POST', p, { body: form, isForm: true }),

    logout(redirect = '/app/') {
      api.clear();
      location.href = redirect;
    },

    // Redirige a login si no hay sesión; opcionalmente exige rol.
    // Conveniencia de navegación, NO control de acceso: la puerta real es el servidor.
    async requireAuth({ roles = null } = {}) {
      if (!api.isAuthed()) { location.href = '/app/acceso.html?next=' + encodeURIComponent(location.pathname); return null; }
      try {
        const me = await api.get('/auth/me');
        if (roles && !roles.includes(me.role)) { location.href = '/app/hub.html'; return null; }
        return me;
      } catch (e) {
        if (e.status === 401) { api.clear(); location.href = '/app/acceso.html'; return null; }
        throw e;
      }
    },
  };

  window.cccn = api;
})();

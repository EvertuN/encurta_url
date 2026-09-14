/* common.js - carrega header e footer compartilhados */

async function loadPartial(selector, url) {
  try {
    const res = await fetch(url);
    if (!res.ok) return;
    document.querySelector(selector).outerHTML = await res.text();
  } catch (e) {
    console.warn(`Erro ao carregar partial ${url}:`, e);
  }
}

function markActivePage() {
  const path = window.location.pathname.replace(/^\//, '') || 'index';
  document.querySelectorAll('.nav-link[data-page]').forEach(link => {
    if (link.dataset.page === path) {
      link.setAttribute('aria-current', 'page');
    }
  });
}

(async function init() {
  await Promise.all([
    loadPartial('#header-placeholder', '/partials/header.html'),
    loadPartial('#footer-placeholder', '/partials/footer.html'),
  ]);
  markActivePage();
})();

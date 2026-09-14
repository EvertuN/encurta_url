/* stats.js — lógica da página de estatísticas */

async function handleSearch() {
    const input = document.getElementById('code-input');
    const btn = document.getElementById('search-btn');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btn-text');
    const errorEl = document.getElementById('error-msg');
    const panel = document.getElementById('stats-panel');

    let val = input.value.trim();
    if (!val) return;

    // Extrai o código da URL caso o usuário cole a URL inteira
    const match = val.match(/([a-zA-Z0-9]{4,12})\/?$/);
    const code = match ? match[1] : val;

    errorEl.style.display = 'none';
    panel.style.display = 'none';
    document.getElementById('hint').style.display = 'none';

    btn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.textContent = 'Consultando...';

    try {
        const [statsRes, infoRes] = await Promise.all([
            fetch(`/urls/${encodeURIComponent(code)}/stats`),
            fetch(`/urls/${encodeURIComponent(code)}`),
        ]);

        if (!statsRes.ok) {
            const msg = statsRes.status === 404
                ? `Código "${code}" não encontrado.`
                : 'Erro ao consultar estatísticas.';
            errorEl.textContent = msg;
            errorEl.style.display = 'block';
            return;
        }

        const stats = await statsRes.json();
        const info = infoRes.ok ? await infoRes.json() : null;

        document.getElementById('panel-code').textContent = `Código: ${stats.short_code}`;

        const urlDiv = document.getElementById('panel-url');
        if (info) {
            urlDiv.innerHTML = `Destino: <a href="${info.original_url}" target="_blank" rel="noopener noreferrer">${info.original_url}</a>`;
        } else {
            urlDiv.textContent = '';
        }

        document.getElementById('stat-clicks').textContent = stats.total_clicks;

        const lastEl = document.getElementById('stat-last');
        const lastSubEl = document.getElementById('stat-last-sub');
        if (stats.last_click) {
            const d = new Date(stats.last_click);
            lastEl.textContent = d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
            lastSubEl.textContent = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        } else {
            lastEl.textContent = '—';
            lastSubEl.textContent = 'sem acessos ainda';
        }

        panel.style.display = 'block';
    } catch (e) {
        errorEl.textContent = 'Erro de conexão com o servidor.';
        errorEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
        btnText.textContent = 'Consultar';
    }
}

document.getElementById('code-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') handleSearch();
});

// Pré-preenche o input se vier com ?code=XXX na URL
const params = new URLSearchParams(location.search);
if (params.has('code')) {
    document.getElementById('code-input').value = params.get('code');
    handleSearch();
}

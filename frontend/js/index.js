/* index.js - lógica da página principal */

async function handleShorten() {
    const input = document.getElementById('url-input');
    const btn = document.getElementById('shorten-btn');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btn-text');
    const errorEl = document.getElementById('error-msg');
    const resultEl = document.getElementById('result');

    let url = input.value.trim();
    if (!url) return;

    // Normaliza se não tiver protocolo
    if (!/^https?:\/\//i.test(url)) {
        url = 'https://' + url;
        input.value = url;
    }

    errorEl.style.display = 'none';
    resultEl.style.display = 'none';

    btn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.textContent = 'Encurtando...';

    try {
        const res = await fetch('/urls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ original_url: url }),
        });

        const data = await res.json();

        if (!res.ok) {
            let msg = 'Não foi possível encurtar a URL.';
            if (res.status === 422) msg = 'URL inválida. Verifique o endereço e tente novamente.';
            else if (data.detail && typeof data.detail === 'string') msg = data.detail;
            errorEl.textContent = msg;
            errorEl.style.display = 'block';
            return;
        }

        const shortUrl = `${window.location.origin}/${data.short_code}`;
        const urlEl = document.getElementById('result-url');
        urlEl.href = shortUrl;
        urlEl.textContent = shortUrl;
        document.getElementById('result-original').textContent = data.original_url;

        resultEl.style.display = 'block';
        resetCopy();
        input.value = '';
    } catch (e) {
        errorEl.textContent = 'Erro de conexão com o servidor.';
        errorEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
        btnText.textContent = 'Encurtar';
    }
}

async function copyLink() {
    const url = document.getElementById('result-url').textContent;
    const btn = document.getElementById('btn-copy');
    try {
        await navigator.clipboard.writeText(url);
    } catch (e) {
        const tmp = document.createElement('input');
        tmp.value = url;
        document.body.appendChild(tmp);
        tmp.select();
        document.execCommand('copy');
        document.body.removeChild(tmp);
    }
    btn.textContent = '✓ Copiado!';
    setTimeout(resetCopy, 2000);
}

function resetCopy() {
    document.getElementById('btn-copy').textContent = 'Copiar';
}

document.getElementById('url-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') handleShorten();
});

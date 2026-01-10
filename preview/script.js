const fontListContainer = document.getElementById('font-list');
const sampleTextInput = document.getElementById('sample-text');
const sizeSlider = document.getElementById('size-slider');
const sizeValue = document.getElementById('size-value');
const refreshBtn = document.getElementById('refresh-btn');
const filterStatus = document.getElementById('filter-status');
const hiddenCountSpan = document.getElementById('hidden-count');
const resetFilterBtn = document.getElementById('reset-filter-btn');

let fontsData = [];
const loadedFonts = new Set();
let hiddenFonts = new Set(JSON.parse(localStorage.getItem('ntype_hidden_fonts') || '[]'));

// LocalStorage から設定を復元
sampleTextInput.value = localStorage.getItem('ntype_sample_text') || sampleTextInput.value;
sizeSlider.value = localStorage.getItem('ntype_font_size') || sizeSlider.value;
sizeValue.textContent = sizeSlider.value + 'px';

async function loadFonts() {
    fontListContainer.innerHTML = '<div class="loading">フォントリストを取得中...</div>';
    try {
        const response = await fetch('/api/fonts');
        fontsData = await response.json();
        renderFontList();
    } catch (error) {
        fontListContainer.innerHTML = `<div class="loading">エラーが発生しました: ${error.message}</div>`;
    }
}

function updateFilterStatus() {
    if (hiddenFonts.size > 0) {
        filterStatus.style.display = 'flex';
        hiddenCountSpan.textContent = hiddenFonts.size;
    } else {
        filterStatus.style.display = 'none';
    }
}

function renderFontList() {
    fontListContainer.innerHTML = '';
    const text = sampleTextInput.value;
    const fontSize = sizeSlider.value + 'px';

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const fontId = entry.target.dataset.fontId;
                const fontUrl = entry.target.dataset.fontUrl;
                loadFont(fontId, fontUrl, entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { rootMargin: '100px' });

    fontsData.forEach((font, index) => {
        const fontId = `font-${index}`;
        const item = document.createElement('div');
        item.className = 'font-item';
        if (hiddenFonts.has(font.name)) {
            item.classList.add('hidden');
        }

        const ratio = (font.size / font.original_size * 100).toFixed(1);
        const info = document.createElement('div');
        info.className = 'font-info';
        info.innerHTML = `
            <div>
                <strong>${font.name}</strong>
                <small style="margin-left:10px; color:#666;">${(font.size / 1024 / 1024).toFixed(2)} MB (${ratio}% compressed)</small>
            </div>
            <button class="hide-btn" onclick="hideFont('${font.name}')">非表示</button>
        `;

        const preview = document.createElement('div');
        preview.className = 'font-preview loading-font';
        preview.id = fontId;
        preview.dataset.fontId = fontId;
        preview.dataset.fontUrl = font.url;
        preview.textContent = text;
        preview.style.fontSize = fontSize;

        item.appendChild(info);
        item.appendChild(preview);
        fontListContainer.appendChild(item);

        if (!hiddenFonts.has(font.name)) {
            observer.observe(preview);
        }
    });
    updateFilterStatus();
}

window.hideFont = (name) => {
    hiddenFonts.add(name);
    localStorage.setItem('ntype_hidden_fonts', JSON.stringify([...hiddenFonts]));
    renderFontList();
};

resetFilterBtn.addEventListener('click', () => {
    hiddenFonts.clear();
    localStorage.removeItem('ntype_hidden_fonts');
    renderFontList();
});

function loadFont(fontId, url, element) {
    if (loadedFonts.has(fontId)) return;

    const fontFace = new FontFace(fontId, `url(${url})`);
    fontFace.load().then((loadedFace) => {
        document.fonts.add(loadedFace);
        element.style.fontFamily = fontId;
        element.classList.remove('loading-font');
        loadedFonts.add(fontId);
    }).catch(err => {
        console.error(`Failed to load font:`, err);
        element.textContent += ' (読み込み失敗)';
    });
}

sampleTextInput.addEventListener('input', () => {
    const text = sampleTextInput.value;
    localStorage.setItem('ntype_sample_text', text);
    document.querySelectorAll('.font-preview').forEach(p => p.textContent = text);
});

sizeSlider.addEventListener('input', () => {
    const size = sizeSlider.value;
    sizeValue.textContent = size + 'px';
    localStorage.setItem('ntype_font_size', size);
    document.querySelectorAll('.font-preview').forEach(p => p.style.fontSize = size + 'px');
});

refreshBtn.addEventListener('click', () => {
    loadedFonts.clear();
    loadFonts();
});

loadFonts();

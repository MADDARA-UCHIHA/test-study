
let modalTextBuffer = "";

// 1. Yangiliklarni yuklash
async function loadNews() {
    const grid = document.getElementById("grid");
    const res = await fetch("/api/feed");
    const data = await res.json();

    grid.innerHTML = "";

    data.articles.forEach((a) => {
        const card = document.createElement("div");
        card.className = "news-card";
        
        // Har bir card ichiga logotip va tugmalarni joylash
        card.innerHTML = `
            <img src="${a.image}" class="card-img">
            <div class="card-content">
                <div class="card-logo" style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">
                    <img src="/static/logo.svg" alt="logo" style="width:20px; height:20px;">
                    <span style="font-size:0.7rem; color:var(--accent); font-weight:900;">DARKLINE•NEWS</span>
                </div>
                <h3 style="margin:10px 0; font-size:1.1rem;">${a.title}</h3>
                <p style="font-size:0.9rem; color:#ccc;">${a.summary}</p>
                <div style="display:flex; justify-content:space-between; margin-top:15px; gap:10px;">
                    <button onclick="speak('${a.summary.replace(/'/g, "\\'")}')" class="action-btn" style="flex:1;">Listen</button>
                    <button onclick="openFull('${a.url}', '${a.title.replace(/'/g, "\\'")}')" class="action-btn" style="flex:1; border-color:var(--accent)">Read Full</button>
                </div>
            </div>`;
        grid.appendChild(card);
    });
}

// 2. To'liq matnni ochish funksiyasi
async function openFull(url, title) {
    const modal = document.getElementById("newsModal");
    const body = document.getElementById("fullContentBody");
    const modalTitle = document.getElementById("modalTitle");

    // Modalni ko'rsatish
    modal.style.display = "flex"; 
    if (modalTitle) modalTitle.innerText = title;
    body.innerHTML = "<div class='loader'>DECRYPTING INTELLIGENCE...</div>";

    try {
        const res = await fetch(`/api/content?url=${encodeURIComponent(url)}`);
        const data = await res.json();

        if (data.content) {
            // Ovozli o'qish uchun bufferga matnni olish
            modalTextBuffer = data.content.replace(/<[^>]*>/g, ''); 

            const listenBtn = `
                <button onclick="speakModal()" class="action-btn" style="width:100%; margin-bottom:20px; border-color:var(--accent); background:rgba(0,255,0,0.1)">
                    <i class="fa-solid fa-volume-high"></i> Listen Full Intelligence Report
                </button>`;
            
            body.innerHTML = listenBtn + `<div class="content-text">${data.content}</div>`;
        } else {
            body.innerHTML = "<p style='color:orange;'>Content protection active. Failed to decrypt.</p>";
        }
    } catch (error) {
        body.innerHTML = "<p style='color:red;'>System Error: Connection lost.</p>";
    }
}

// 3. Ovozli funksiyalar
function speak(text) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
}

function speakModal() { 
    if(modalTextBuffer) speak(modalTextBuffer); 
}

function closeModal() { 
    window.speechSynthesis.cancel();
    document.getElementById("newsModal").style.display = "none"; 
}

// Esc tugmasi bilan yopish
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

document.addEventListener("DOMContentLoaded", loadNews);

async function openFullIntel(url, title) {
    const modal = document.getElementById('modal');
    const aiBox = document.getElementById('aiResponse');
    modal.style.display = 'block';
    aiBox.innerHTML = ">> DECRYPTING FULL DATA STREAMS...";

    try {
        const res = await fetch('/api/full-intel', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': "{{ csrf_token() }}"},
            body: JSON.stringify({url: url})
        });
        const data = await res.json();
        
        // Matnni modalga chiqarish va LISTEN tugmasini qo'shish
        aiBox.innerHTML = `<h3>${title}</h3><hr><p>${data.content}</p><br>
            <button class="action-btn" onclick="listenIntel('${data.content.replace(/'/g, "\\'")}')">
                <i class="fa-solid fa-volume-high"></i> LISTEN INTEL
            </button>`;
    } catch (e) {
        aiBox.innerHTML = "!! FAILED TO REACH TARGET !!";
    }
}

function listenIntel(text) {
    window.speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(text);
    speech.lang = 'en-US';
    speech.rate = 0.95;
    window.speechSynthesis.speak(speech);
}
<<<<<<< HEAD
const grid = document.getElementById("grid");
const statusEl = document.getElementById("status");

async function loadNews() {
  try {
    const res = await fetch("/api/feed?limit=1000");
    const data = await res.json();

    statusEl.textContent = `Loaded ${data.count} articles`;
    grid.innerHTML = "";

    data.articles.forEach(a => {
      const card = document.createElement("div");
      card.className = "card";
localStorage.setItem("termsAccepted", "yes");

      let imgHtml = "";
      if (a.image) {
        imgHtml = `<img src="${a.image}" class="card-img">`;
      }

      card.innerHTML = 
        `${imgHtml}
        <h3>${a.title}</h3>
        <small>${a.source} • ${a.published}</small>
        <p>${a.summary}</p>
        <a href="${a.link}" target="_blank">Read full →</a>`;

      grid.appendChild(card);
    });

  } catch (e) {
    statusEl.textContent = "Failed to load news";
  }
}


loadNews();


=======
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
>>>>>>> 96c68e9c0ee2b576c8b1afd6811b2b5591ceb0fe

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

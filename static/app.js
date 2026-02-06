const API_URL = "/api/feed";

const grid = document.getElementById("grid");
const statusEl = document.getElementById("status");

let allItems = [];

function stripHtml(html) {
  return (html || "").replace(/<[^>]+>/g, "");
}

function render(items) {
  grid.innerHTML = "";

  items.forEach(it => {
    const card = document.createElement("div");
    card.className = "card";

    if (it.image) {
      const img = document.createElement("img");
      img.src = it.image;
      card.appendChild(img);
    }

    const h = document.createElement("h2");
    h.textContent = it.title;

    const meta = document.createElement("small");
    meta.textContent = `${it.source} • ${it.published}`;

    const p = document.createElement("p");
    p.textContent = stripHtml(it.summary).slice(0, 300);

    const btn = document.createElement("button");
    btn.textContent = "Read full";
    btn.onclick = () => {
      window.open(it.link, "_blank");
    };

    card.appendChild(h);
    card.appendChild(meta);
    card.appendChild(p);
    card.appendChild(btn);

    grid.appendChild(card);
  });
}

async function loadFeed() {
  statusEl.textContent = "Loading news...";
  try {
    const res = await fetch(`${API_URL}?limit=50`);
    const data = await res.json();
    allItems = data.articles || [];
    statusEl.textContent = `Loaded ${allItems.length} articles`;
    render(allItems);
  } catch (e) {
    console.error(e);
    statusEl.textContent = "Failed to load news";
  }
}

loadFeed();
(function () {
  "use strict";

  const form = document.getElementById("gallery-filters");
  if (!form) return;
  const search = document.getElementById("gallery-search");
  const storySelect = document.getElementById("gallery-story");
  const typeSelect = document.getElementById("gallery-type");
  const reset = document.getElementById("gallery-reset");
  const count = document.getElementById("gallery-count");
  const empty = document.getElementById("gallery-empty");
  const groups = Array.from(document.querySelectorAll(".gallery-story"));
  const links = Array.from(document.querySelectorAll("[data-gallery-image]"));
  const cards = links.map(link => ({link, card: link.closest(".landscape-card")}));
  const normalize = value => value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
  cards.forEach(item => { item.search = normalize(item.card.dataset.search); });
  let visibleLinks = links.slice();
  if (!links.length) return;
  form.hidden = false;

  function readFilters() {
    const parameters = new URL(window.location.href).searchParams;
    search.value = parameters.get("q") || "";
    const story = parameters.get("story") || "";
    storySelect.value = Array.from(storySelect.options).some(option => option.value === story) ? story : "";
    const type = parameters.get("type") || "";
    typeSelect.value = Array.from(typeSelect.options).some(option => option.value === type) ? type : "";
  }

  function filter(writeUrl) {
    const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    const story = storySelect.value;
    const type = typeSelect.value;
    visibleLinks = [];
    cards.forEach(item => {
      const matches = (!story || item.link.dataset.storySlug === story)
        && (!type || item.link.dataset.collection === type) && words.every(word => item.search.includes(word));
      item.card.hidden = !matches;
      if (matches) visibleLinks.push(item.link);
    });
    let storyCount = 0;
    groups.forEach(group => {
      group.hidden = !Array.from(group.querySelectorAll(".landscape-card")).some(card => !card.hidden);
      if (!group.hidden) storyCount += 1;
    });
    count.textContent = visibleLinks.length.toLocaleString() + (visibleLinks.length === 1 ? " painting across " : " paintings across ")
      + storyCount.toLocaleString() + (storyCount === 1 ? " story" : " stories");
    empty.hidden = visibleLinks.length !== 0;
    reset.disabled = !search.value && !story && !type;
    if (writeUrl) {
      const url = new URL(window.location.href);
      search.value.trim() ? url.searchParams.set("q", search.value.trim()) : url.searchParams.delete("q");
      story ? url.searchParams.set("story", story) : url.searchParams.delete("story");
      type ? url.searchParams.set("type", type) : url.searchParams.delete("type");
      try { window.history.replaceState(null, "", url); } catch (_) { /* Filtering still works in a local file preview. */ }
    }
  }

  form.addEventListener("submit", event => { event.preventDefault(); filter(true); });
  search.addEventListener("input", () => filter(true));
  storySelect.addEventListener("change", () => filter(true));
  typeSelect.addEventListener("change", () => filter(true));
  reset.addEventListener("click", () => {
    search.value = "";
    storySelect.value = "";
    typeSelect.value = "";
    filter(true);
    search.focus();
  });
  readFilters();
  filter(false);

  const viewer = document.getElementById("gallery-viewer");
  const image = document.getElementById("viewer-image");
  const previous = document.getElementById("viewer-prev");
  const next = document.getElementById("viewer-next");
  const error = document.getElementById("viewer-error");
  let index = 0;
  let opener = null;
  let touchStart = null;

  function showImage() {
    const link = visibleLinks[index];
    if (!link) return;
    document.getElementById("viewer-story").textContent = link.dataset.storyTitle;
    document.getElementById("viewer-title").textContent = link.dataset.title;
    document.getElementById("viewer-position").textContent = (index + 1).toLocaleString() + " of " + visibleLinks.length.toLocaleString();
    document.getElementById("viewer-full").href = link.dataset.full;
    const reader = document.getElementById("viewer-read-story");
    reader.hidden = !link.dataset.reader;
    if (link.dataset.reader) reader.href = link.dataset.reader;
    error.hidden = true;
    image.hidden = true;
    image.alt = link.querySelector("img").alt;
    image.src = link.dataset.full;
    previous.disabled = next.disabled = visibleLinks.length < 2;
  }

  function step(direction) {
    if (!viewer.open || visibleLinks.length < 2) return;
    index = (index + direction + visibleLinks.length) % visibleLinks.length;
    showImage();
  }

  image.addEventListener("load", () => { image.hidden = false; });
  image.addEventListener("error", () => { image.hidden = true; error.hidden = false; });
  document.querySelector(".gallery-collection").addEventListener("click", event => {
    const link = event.target.closest("[data-gallery-image]");
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey
      || typeof viewer.showModal !== "function") return;
    index = visibleLinks.indexOf(link);
    if (index < 0) return;
    opener = link;
    showImage();
    try {
      viewer.showModal();
      document.documentElement.classList.add("gallery-modal-open");
      document.getElementById("viewer-close").focus();
      event.preventDefault();
    } catch (_) { /* The anchor remains a direct full-image fallback. */ }
  });
  document.getElementById("viewer-close").addEventListener("click", () => viewer.close());
  previous.addEventListener("click", () => step(-1));
  next.addEventListener("click", () => step(1));
  viewer.addEventListener("keydown", event => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      step(event.key === "ArrowLeft" ? -1 : 1);
    }
  });
  viewer.addEventListener("click", event => {
    if (event.target !== viewer) return;
    const bounds = viewer.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) viewer.close();
  });
  viewer.addEventListener("close", () => {
    document.documentElement.classList.remove("gallery-modal-open");
    if (opener && opener.isConnected && !opener.closest(".landscape-card").hidden) opener.focus({preventScroll: true});
    else search.focus({preventScroll: true});
    image.removeAttribute("src");
    opener = null;
  });
  const stage = viewer.querySelector(".viewer-stage");
  stage.addEventListener("touchstart", event => {
    touchStart = event.touches.length === 1 ? {x: event.touches[0].clientX, y: event.touches[0].clientY} : null;
  }, {passive: true});
  stage.addEventListener("touchend", event => {
    if (!touchStart || !event.changedTouches.length) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    touchStart = null;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.5) step(dx < 0 ? 1 : -1);
  }, {passive: true});
  window.addEventListener("popstate", () => {
    if (viewer.open) viewer.close();
    readFilters();
    filter(false);
  });
}());

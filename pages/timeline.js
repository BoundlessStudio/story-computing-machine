(() => {
  const atlas = document.querySelector('[data-timeline]');
  if (!atlas) return;
  atlas.querySelectorAll('.atlas-controls, .thread-controls').forEach((controls) => { controls.hidden = false; });

  const stories = [...atlas.querySelectorAll('.atlas-story')];
  const eras = [...atlas.querySelectorAll('[data-era-stop]')];
  const cycles = [...atlas.querySelectorAll('[data-cycle-section]')];
  const search = atlas.querySelector('[data-atlas-search]');
  const state = atlas.querySelector('[data-atlas-state]');
  const count = atlas.querySelector('[data-atlas-count]');
  const fold = atlas.querySelector('[data-collapse-eras]');
  const threads = [...atlas.querySelectorAll('[data-thread-kind]')];
  const threadButtons = [...atlas.querySelectorAll('[data-thread-filter]')];
  const normalize = (value) => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[’‘]/g, "'");

  atlas.querySelectorAll('[data-orbit-title]').forEach((link) => {
    const describe = () => {
      atlas.querySelector('[data-orbit-readout]').textContent = link.dataset.orbitTitle;
      atlas.querySelector('[data-orbit-context]').textContent = link.dataset.orbitState;
    };
    link.addEventListener('pointerenter', describe);
    link.addEventListener('focus', describe);
  });

  const updateFoldLabel = () => {
    const visible = eras.filter((era) => !era.hidden);
    fold.textContent = visible.some((era) => era.open) ? 'Fold all eras' : 'Unfold all eras';
    fold.disabled = !visible.length;
  };

  function filterStories() {
    const query = normalize(search.value.trim());
    const terms = query.split(/\s+/).filter(Boolean);
    const filtering = Boolean(query || state.value !== 'all');
    stories.forEach((story) => {
      const cycle = story.closest('[data-cycle-section]');
      story.hidden = !terms.every((term) => normalize(story.dataset.search).includes(term)) ||
        (state.value !== 'all' && state.value !== cycle.dataset.magicState);
    });
    eras.forEach((era) => {
      era.hidden = filtering && ![...era.querySelectorAll('.atlas-story')].some((story) => !story.hidden);
      if (filtering && !era.hidden) era.open = true;
    });
    cycles.forEach((cycle) => {
      cycle.hidden = ![...cycle.querySelectorAll('[data-era-stop]')].some((era) => !era.hidden);
    });
    const total = stories.filter((story) => !story.hidden).length;
    const totalCycles = cycles.filter((cycle) => !cycle.hidden).length;
    count.textContent = `${total} ${total === 1 ? 'story' : 'stories'} across ${totalCycles} reading ${totalCycles === 1 ? 'cycle' : 'cycles'}`;
    atlas.querySelector('[data-atlas-empty]').hidden = total > 0;
    updateFoldLabel();
  }

  function resetStories() {
    search.value = '';
    state.value = 'all';
    filterStories();
  }

  function filterThreads(kind) {
    threads.forEach((thread) => { thread.hidden = kind !== 'all' && thread.dataset.threadKind !== kind; });
    threadButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.threadFilter === kind)));
    const total = threads.filter((thread) => !thread.hidden).length;
    atlas.querySelector('[data-thread-count]').textContent = `${total} ${total === 1 ? 'thread' : 'threads'}`;
  }

  function revealFragment(hash, moveFocus = false) {
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target) return;
    if (target.closest('[data-cycle-section]')) {
      resetStories();
      const era = target.closest('[data-era-stop]');
      if (era) era.open = true;
    }
    if (target.matches('[data-thread-kind]')) filterThreads('all');
    if (moveFocus) requestAnimationFrame(() => {
      target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
      target.scrollIntoView({ block: 'start' });
    });
  }

  search.addEventListener('input', filterStories);
  state.addEventListener('change', filterStories);
  atlas.querySelector('[data-atlas-reset]').addEventListener('click', () => { resetStories(); search.focus(); });
  fold.addEventListener('click', () => {
    const visible = eras.filter((era) => !era.hidden);
    const shouldOpen = !visible.some((era) => era.open);
    visible.forEach((era) => { era.open = shouldOpen; });
    updateFoldLabel();
  });
  eras.forEach((era) => era.addEventListener('toggle', updateFoldLabel));
  threadButtons.forEach((button) => button.addEventListener('click', () => filterThreads(button.dataset.threadFilter)));

  atlas.addEventListener('click', (event) => {
    const link = event.target.closest('a[href^="#"]');
    if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
      revealFragment(link.getAttribute('href'), true);
    }
  });
  window.addEventListener('hashchange', () => revealFragment(location.hash, true));
  revealFragment(location.hash, Boolean(location.hash));

  if ('IntersectionObserver' in window) {
    const links = [...atlas.querySelectorAll('[data-cycle-link]')];
    const observer = new IntersectionObserver((entries) => {
      const active = entries.find((entry) => entry.isIntersecting);
      if (!active) return;
      atlas.querySelector('[data-atlas-location]').textContent = active.target.querySelector('h2').textContent;
      links.forEach((link) => {
        if (link.dataset.cycleLink === active.target.dataset.cycleSection) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }, { rootMargin: '-10% 0px -75% 0px', threshold: 0 });
    cycles.forEach((cycle) => observer.observe(cycle));
  }
})();

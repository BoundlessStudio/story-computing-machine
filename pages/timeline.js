(() => {
  const atlas = document.querySelector('[data-timeline]');
  if (!atlas) return;
  atlas.querySelectorAll('.atlas-controls, .thread-controls').forEach((controls) => { controls.hidden = false; });

  const stories = [...atlas.querySelectorAll('.worldline-event')];
  const details = [...atlas.querySelectorAll('[data-event-details]')];
  const cycles = [...atlas.querySelectorAll('[data-cycle-section]')];
  const eras = [...atlas.querySelectorAll('[data-era-section]')];
  const search = atlas.querySelector('[data-atlas-search]');
  const state = atlas.querySelector('[data-atlas-state]');
  const cyclePicker = atlas.querySelector('[data-atlas-cycle]');
  const count = atlas.querySelector('[data-atlas-count]');
  const fold = atlas.querySelector('[data-toggle-details]');
  const threads = [...atlas.querySelectorAll('[data-thread-kind]')];
  const threadButtons = [...atlas.querySelectorAll('[data-thread-filter]')];
  const weave = atlas.querySelector('[data-weave]');
  const routes = weave.querySelector('.weave-routes');
  const bands = [...atlas.querySelectorAll('[data-horizon-era]')];
  const overviewBands = [...weave.querySelectorAll('[data-horizon-era]')];
  const readout = atlas.querySelector('[data-weave-readout]');
  const defaultReadout = readout.textContent;
  let threadKind = 'direct';
  let highlightedEra = null;
  let drawFrame;
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
    const visible = details.filter((detail) => !detail.closest('.worldline-event').hidden);
    fold.textContent = visible.some((detail) => detail.open) ? 'Collapse story details' : 'Expand story details';
    fold.disabled = !visible.length;
  };

  function filterStories() {
    [...cyclePicker.options].forEach((option) => {
      option.disabled = option.value !== 'all' && state.value !== 'all' && option.dataset.magicState !== state.value;
    });
    if (cyclePicker.selectedOptions[0]?.disabled) cyclePicker.value = 'all';
    const query = normalize(search.value.trim());
    const terms = query.split(/\s+/).filter(Boolean);
    stories.forEach((story) => {
      const cycle = story.closest('[data-cycle-section]');
      story.hidden = !terms.every((term) => normalize(story.dataset.search).includes(term)) ||
        (state.value !== 'all' && state.value !== cycle.dataset.magicState) ||
        (cyclePicker.value !== 'all' && cyclePicker.value !== cycle.dataset.cycleSection);
    });
    if (query) details.forEach((detail) => {
      if (!detail.closest('.worldline-event').hidden) detail.open = true;
    });
    eras.forEach((era) => {
      era.hidden = ![...era.querySelectorAll('.worldline-event')].some((story) => !story.hidden);
    });
    const visibleEras = new Set(eras.filter((era) => !era.hidden).map((era) => era.dataset.eraSection));
    bands.forEach((band) => band.classList.toggle('is-muted', !visibleEras.has(band.dataset.horizonEra)));
    cycles.forEach((cycle) => {
      cycle.hidden = ![...cycle.querySelectorAll('.worldline-event')].some((story) => !story.hidden);
    });
    const total = stories.filter((story) => !story.hidden).length;
    const totalCycles = cycles.filter((cycle) => !cycle.hidden).length;
    const totalEras = eras.filter((era) => !era.hidden).length;
    count.textContent = `${total} ${total === 1 ? 'story' : 'stories'} in ${totalEras} ${totalEras === 1 ? 'era' : 'eras'} across ${totalCycles} ${totalCycles === 1 ? 'cycle' : 'cycles'}`;
    atlas.querySelector('[data-atlas-empty]').hidden = total > 0;
    updateFoldLabel();
  }

  function resetStories() {
    search.value = '';
    state.value = 'all';
    cyclePicker.value = 'all';
    filterStories();
  }

  function filterThreads(kind) {
    threadKind = kind;
    threads.forEach((thread) => { thread.hidden = kind !== 'all' && thread.dataset.threadKind !== kind; });
    threadButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.threadFilter === kind)));
    const total = threads.filter((thread) => !thread.hidden).length;
    atlas.querySelector('[data-thread-count]').textContent = `${total} ${total === 1 ? 'thread' : 'threads'}`;
    const local = threads.filter((thread) => !thread.hidden && thread.dataset.fromEra === thread.dataset.toEra).length;
    atlas.querySelector('[data-map-count]').textContent = `${total - local} connections between eras · ${local} local connections inside eras`;
    scheduleRoutes();
  }

  function highlightEra(eraId) {
    highlightedEra = eraId;
    const connected = new Set(eraId ? [eraId] : []);
    threads.filter((thread) => !thread.hidden).forEach((thread) => {
      if (eraId && [thread.dataset.fromEra, thread.dataset.toEra].includes(eraId)) {
        connected.add(thread.dataset.fromEra);
        connected.add(thread.dataset.toEra);
      }
    });
    bands.forEach((band) => band.classList.toggle('is-connected', connected.has(band.dataset.horizonEra)));
    routes.classList.toggle('has-selection', Boolean(eraId));
    [...routes.querySelectorAll('a')].forEach((link) => {
      link.classList.toggle('is-connected', Boolean(eraId && [link.dataset.fromEra, link.dataset.toEra].includes(eraId)));
    });
  }

  function drawRoutes() {
    const surface = weave.getBoundingClientRect();
    if (!surface.width || !surface.height) return;
    routes.setAttribute('viewBox', `0 0 ${surface.width} ${surface.height}`);
    const boxes = new Map(overviewBands.map((band) => [band.dataset.horizonEra, band.getBoundingClientRect()]));
    routes.replaceChildren();
    threads.forEach((thread, index) => {
      const from = thread.dataset.fromEra;
      const to = thread.dataset.toEra;
      if (from === to || (threadKind !== 'all' && thread.dataset.threadKind !== threadKind)) return;
      const source = boxes.get(from);
      const target = boxes.get(to);
      if (!source || !target) return;
      const x1 = source.left - surface.left + Math.min(12, source.width / 2);
      const y1 = source.top - surface.top + source.height / 2;
      const x2 = target.left - surface.left + Math.min(12, target.width / 2);
      const y2 = target.top - surface.top + target.height / 2;
      const bend = Math.max(4, Math.min(x1, x2) - 28 - (index % 4) * 8);
      const link = document.createElementNS('http://www.w3.org/2000/svg', 'a');
      link.setAttribute('href', `#${thread.id}`);
      link.setAttribute('aria-label', `${thread.dataset.threadLabel}: read connection notes`);
      link.setAttribute('class', thread.dataset.threadKind);
      link.dataset.fromEra = from;
      link.dataset.toEra = to;
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', `M${x1},${y1} C${bend},${y1} ${bend},${y2} ${x2},${y2}`);
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      title.textContent = thread.dataset.threadLabel;
      link.append(title, path);
      link.addEventListener('pointerenter', () => { readout.textContent = thread.dataset.threadLabel; });
      link.addEventListener('focus', () => { readout.textContent = thread.dataset.threadLabel; });
      routes.append(link);
    });
    highlightEra(highlightedEra);
  }

  function scheduleRoutes() {
    cancelAnimationFrame(drawFrame);
    drawFrame = requestAnimationFrame(drawRoutes);
  }

  bands.forEach((band) => {
    const describe = () => {
      readout.textContent = `${band.dataset.eraTitle}. ${band.dataset.eraDescription}`;
      highlightEra(band.dataset.horizonEra);
    };
    const clear = () => { highlightEra(null); readout.textContent = defaultReadout; };
    band.addEventListener('pointerenter', describe);
    band.addEventListener('focus', describe);
    band.addEventListener('pointerleave', clear);
    band.addEventListener('blur', clear);
  });
  if ('ResizeObserver' in window) new ResizeObserver(scheduleRoutes).observe(weave);
  window.addEventListener('resize', scheduleRoutes);
  document.fonts?.ready.then(scheduleRoutes);

  const depthPicker = atlas.querySelector('[data-depth-picker]');
  const depthHistories = [...atlas.querySelectorAll('[data-depth-history]')];
  function selectDepth(id) {
    if (!depthPicker || !depthHistories.some((panel) => panel.id === id)) return;
    depthPicker.value = id;
    depthHistories.forEach((panel) => {
      panel.hidden = panel.id !== id;
      panel.classList.toggle('is-selected', panel.id === id);
      panel.open = panel.id === id;
    });
  }
  if (depthPicker) {
    depthPicker.closest('label').hidden = false;
    depthPicker.addEventListener('change', () => {
      selectDepth(depthPicker.value);
      history.replaceState(null, '', `#${depthPicker.value}`);
    });
    selectDepth(depthPicker.value);
  }

  function revealFragment(hash, moveFocus = false) {
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target) return;
    if (target.matches('[data-depth-history]')) selectDepth(id);
    if (target.closest('[data-cycle-section]')) {
      resetStories();
      const detail = target.closest('.worldline-event')?.querySelector('[data-event-details]');
      if (detail) detail.open = true;
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
  cyclePicker.addEventListener('change', filterStories);
  atlas.querySelector('[data-atlas-reset]').addEventListener('click', () => { resetStories(); search.focus(); });
  fold.addEventListener('click', () => {
    const visible = details.filter((detail) => !detail.closest('.worldline-event').hidden);
    const shouldOpen = !visible.some((detail) => detail.open);
    visible.forEach((detail) => { detail.open = shouldOpen; });
    updateFoldLabel();
  });
  details.forEach((detail) => detail.addEventListener('toggle', updateFoldLabel));
  threadButtons.forEach((button) => button.addEventListener('click', () => filterThreads(button.dataset.threadFilter)));

  atlas.addEventListener('click', (event) => {
    const link = event.target.closest('a[href^="#"]');
    if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
      revealFragment(link.getAttribute('href'), true);
    }
  });
  window.addEventListener('hashchange', () => revealFragment(location.hash, true));
  revealFragment(location.hash, Boolean(location.hash));
  filterThreads(location.hash.startsWith('#thread-') ? 'all' : 'direct');

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

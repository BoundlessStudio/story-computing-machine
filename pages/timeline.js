(() => {
  const atlas = document.querySelector('[data-timeline]');
  if (!atlas) return;
  atlas.querySelectorAll('.atlas-controls, .thread-controls').forEach((controls) => { controls.hidden = false; });

  const stories = [...atlas.querySelectorAll('.worldline-event')];
  const details = [...atlas.querySelectorAll('[data-event-details]')];
  const cycles = [...atlas.querySelectorAll('[data-cycle-section]')];
  const search = atlas.querySelector('[data-atlas-search]');
  const state = atlas.querySelector('[data-atlas-state]');
  const cyclePicker = atlas.querySelector('[data-atlas-cycle]');
  const count = atlas.querySelector('[data-atlas-count]');
  const fold = atlas.querySelector('[data-toggle-details]');
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
    cycles.forEach((cycle) => {
      cycle.hidden = ![...cycle.querySelectorAll('.worldline-event')].some((story) => !story.hidden);
    });
    const total = stories.filter((story) => !story.hidden).length;
    const totalCycles = cycles.filter((cycle) => !cycle.hidden).length;
    count.textContent = `${total} ${total === 1 ? 'story' : 'stories'} across ${totalCycles} ${totalCycles === 1 ? 'cycle' : 'cycles'}`;
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

(() => {
  const atlas = document.querySelector('[data-timeline]');
  if (!atlas || typeof HTMLDialogElement === 'undefined' || typeof HTMLDialogElement.prototype.showModal !== 'function') return;
  atlas.classList.add('is-interactive');
  const search = atlas.querySelector('[data-atlas-search]');
  const feedback = atlas.querySelector('[data-search-feedback]');
  const count = atlas.querySelector('[data-atlas-count]');
  const cycles = [...atlas.querySelectorAll('[data-cycle-section]')];
  const eras = [...atlas.querySelectorAll('[data-era-section]')];
  const stories = [...atlas.querySelectorAll('[data-story-slug]')];
  const threads = [...atlas.querySelectorAll('[data-thread-kind]')];
  const connections = atlas.querySelector('[data-connections-dialog]');
  const depths = atlas.querySelector('[data-depth-dialog]');
  const threadFilters = [...atlas.querySelectorAll('[data-thread-filter]')];
  let activeDialog = null;
  let returnFocus = null;
  let previousOverflow = '';
  let connectionOrigin = null;
  const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[’‘]/g, "'");

  search.closest('label').hidden = false;
  function filterStories() {
    const terms = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    stories.forEach(story => { story.hidden = !terms.every(term => normalize(story.dataset.search).includes(term)); });
    eras.forEach(era => {
      const matches = [...era.querySelectorAll('[data-story-slug]')].filter(story => !story.hidden);
      era.hidden = !matches.length;
      const titles = era.querySelector('[data-era-matches]');
      titles.hidden = !terms.length;
      titles.textContent = matches.map(story => story.querySelector('h4').textContent.replace('↗', '').trim()).join(' · ');
      era.querySelector('[data-era-count]').textContent = matches.length;
      era.querySelector('[data-era-noun]').textContent = matches.length === 1 ? 'story' : 'stories';
    });
    cycles.forEach(cycle => { cycle.hidden = ![...cycle.querySelectorAll('[data-era-section]')].some(era => !era.hidden); });
    atlas.querySelectorAll('[data-phase]').forEach(phase => {
      phase.hidden = !eras.some(era => !era.hidden && era.dataset.magicState === phase.dataset.phase);
    });
    atlas.querySelector('.history-braid').hidden = Boolean(terms.length);
    feedback.hidden = !terms.length;
    const total = stories.filter(story => !story.hidden).length;
    const eraCount = eras.filter(era => !era.hidden).length;
    count.textContent = total + (total === 1 ? ' story in ' : ' stories in ') + eraCount + (eraCount === 1 ? ' era' : ' eras');
    atlas.querySelector('[data-atlas-empty]').hidden = total > 0;
  }
  function clearSearch() { search.value = ''; filterStories(); }
  function setHash(hash, replace = false) {
    if (location.hash !== hash) history[replace ? 'replaceState' : 'pushState'](null, '', hash || location.pathname + location.search);
  }
  function closeDialog(restoreFocus = true) {
    if (!activeDialog) return;
    const closing = activeDialog;
    activeDialog = null;
    closing.close();
    closing.closest('details').open = false;
    document.body.style.overflow = previousOverflow;
    if (restoreFocus && returnFocus?.isConnected) returnFocus.focus({preventScroll: true});
  }
  function showDialog(dialog, trigger) {
    if (activeDialog === dialog) return;
    closeDialog(false);
    returnFocus = trigger || dialog.closest('details').querySelector('summary');
    dialog.closest('details').open = true;
    previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    activeDialog = dialog;
    dialog.showModal();
    dialog.scrollTop = 0;
    dialog.querySelector('[data-dialog-close]').focus({preventScroll: true});
  }
  function showEra(era, trigger) {
    const dialog = era.querySelector('[data-era-dialog]');
    showDialog(dialog, trigger);
    const available = eras.filter(item => !item.hidden);
    const index = available.indexOf(era);
    dialog.querySelector('[data-era-prev]').disabled = index <= 0;
    dialog.querySelector('[data-era-next]').disabled = index >= available.length - 1;
  }
  function filterThreads(kind = 'all', id = null) {
    threads.forEach(thread => { thread.hidden = id ? thread.id !== id : kind !== 'all' && thread.dataset.threadKind !== kind; });
    threadFilters.forEach(button => button.setAttribute('aria-pressed', String(!id && button.dataset.threadFilter === kind)));
    connections.querySelector('.thread-controls').hidden = Boolean(id);
    connections.querySelector('[data-all-connections]').hidden = !id;
  }
  function reveal(hash, focus = true, trigger = null) {
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target) { closeDialog(); return; }
    const era = target.closest('[data-era-section]');
    if (era) {
      if (era.hidden || target.closest('[data-story-slug]')?.hidden) clearSearch();
      showEra(era, trigger);
      const story = target.closest('[data-story-slug]');
      if (story) {
        story.querySelector('[data-event-details]').open = true;
        requestAnimationFrame(() => {
          story.setAttribute('tabindex', '-1');
          story.focus({preventScroll: true});
          story.scrollIntoView({block: 'start'});
        });
      }
      return;
    }
    if (target.matches('[data-thread-kind]') || target.id === 'atlas-threads') {
      if (activeDialog !== connections) {
        connectionOrigin = activeDialog?.matches('[data-era-dialog]')
          ? document.activeElement.closest('[data-story-slug]') || activeDialog.closest('[data-era-section]') : null;
      }
      filterThreads('all', target.matches('[data-thread-kind]') ? target.id : null);
      showDialog(connections, trigger);
      connections.querySelector('[data-dialog-close]').textContent = connectionOrigin ? '← Back to the era' : '← Back to the timeline';
      return;
    }
    if (target.id === 'atlas-depths' && depths) {
      showDialog(depths, trigger);
      return;
    }
    closeDialog(false);
    if (target.closest('[data-cycle-section]') || target.matches('[data-phase]')) clearSearch();
    if (focus) {
      target.setAttribute('tabindex', '-1');
      target.focus({preventScroll: true});
      target.scrollIntoView({block: 'start'});
    }
  }
  eras.forEach(era => {
    const summary = era.querySelector('.era-stop');
    summary.addEventListener('click', event => {
      event.preventDefault();
      setHash('#' + era.id);
      showEra(era, summary);
    });
    ['prev', 'next'].forEach(direction => {
      era.querySelector('[data-era-' + direction + ']').addEventListener('click', () => {
        const available = eras.filter(item => !item.hidden);
        const next = available[available.indexOf(era) + (direction === 'prev' ? -1 : 1)];
        if (next) { setHash('#' + next.id); showEra(next); }
      });
    });
  });
  atlas.querySelector('.connections-library > summary').addEventListener('click', event => {
    event.preventDefault(); setHash('#atlas-threads'); reveal('#atlas-threads');
  });
  if (depths) {
    atlas.querySelector('.depth-library > summary').addEventListener('click', event => {
      event.preventDefault(); setHash('#atlas-depths'); reveal('#atlas-depths');
    });
    const historySearch = depths.querySelector('[data-history-search]');
    const histories = [...depths.querySelectorAll('[data-time-fold]')];
    historySearch.closest('label').hidden = false;
    historySearch.addEventListener('input', () => {
      const terms = normalize(historySearch.value.trim()).split(/\s+/).filter(Boolean);
      histories.forEach(item => { item.hidden = !terms.every(term => normalize(item.dataset.search).includes(term)); });
      const total = histories.filter(item => !item.hidden).length;
      depths.querySelector('[data-history-count]').textContent = total + (total === 1 ? ' history' : ' histories');
      depths.querySelector('[data-history-empty]').hidden = total > 0;
    });
  }
  atlas.querySelectorAll('dialog').forEach(dialog => {
    const leave = () => {
      if (dialog === connections && connectionOrigin) {
        const origin = connectionOrigin;
        connectionOrigin = null;
        closeDialog(false);
        setHash('#' + origin.id, true);
        reveal('#' + origin.id);
        return;
      }
      const era = dialog.closest('[data-era-section]');
      closeDialog();
      setHash(era ? '#' + era.closest('[data-cycle-section]').id : '#atlas-explore', true);
    };
    dialog.querySelector('[data-dialog-close]').addEventListener('click', leave);
    dialog.addEventListener('cancel', event => { event.preventDefault(); leave(); });
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) leave();
    });
  });
  connections.querySelector('[data-all-connections]').addEventListener('click', () => { filterThreads(); setHash('#atlas-threads', true); connections.scrollTop = 0; });
  threadFilters.forEach(button => button.addEventListener('click', () => filterThreads(button.dataset.threadFilter)));
  atlas.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    setHash(link.hash);
    reveal(link.hash, true, link);
  });
  search.addEventListener('input', filterStories);
  atlas.querySelector('[data-atlas-reset]').addEventListener('click', () => { clearSearch(); search.focus(); });
  window.addEventListener('popstate', () => reveal(location.hash));
  window.addEventListener('hashchange', () => reveal(location.hash));
  reveal(location.hash, Boolean(location.hash));
})();

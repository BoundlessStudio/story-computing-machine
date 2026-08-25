(() => {
  const timeline = document.querySelector("[data-timeline]");
  if (!timeline) return;

  const filterButtons = [...timeline.querySelectorAll("[data-timeline-filter]")];
  const storyLinks = [...timeline.querySelectorAll("[data-story-link]")];
  const storyMarkers = [...timeline.querySelectorAll("[data-story-marker]")];
  const eraStops = [...timeline.querySelectorAll("[data-era-stop]")];
  const search = timeline.querySelector("[data-timeline-search]");
  const result = timeline.querySelector("[data-visible-total]");
  const collapseButton = timeline.querySelector("[data-collapse-eras]");
  let activeFilter = "all";

  const normalize = (value) =>
    (value || "")
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase();

  const refresh = () => {
    const query = normalize(search?.value.trim());
    const visibleSlugs = new Set();

    storyLinks.forEach((link) => {
      const confidenceMatch =
        activeFilter === "all" ||
        link.dataset.placementConfidence === activeFilter;
      const titleMatch = !query || normalize(link.dataset.title).includes(query);
      const visible = confidenceMatch && titleMatch;
      link.hidden = !visible;
      if (visible) visibleSlugs.add(link.dataset.storySlug);
    });

    storyMarkers.forEach((marker) => {
      marker.hidden = !visibleSlugs.has(marker.dataset.storySlug);
    });

    eraStops.forEach((era) => {
      const eraLinks = [...era.querySelectorAll("[data-story-link]")];
      const visible = eraLinks.filter((link) => !link.hidden).length;
      era.querySelectorAll("[data-era-visible]").forEach((count) => {
        count.textContent = String(visible);
      });
      era.classList.toggle(
        "is-filter-empty",
        era.dataset.eraHasStories === "true" && visible === 0,
      );
    });

    filterButtons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.timelineFilter === activeFilter),
      );
    });
    if (result) result.textContent = String(visibleSlugs.size);
  };

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.timelineFilter || "all";
      refresh();
    });
  });

  search?.addEventListener("input", refresh);

  eraStops.forEach((era) => {
    era.addEventListener("toggle", () => {
      if (!era.open) return;
      era.closest("[data-epoch-section]")
        ?.querySelectorAll("[data-era-stop][open]")
        .forEach((other) => {
          if (other !== era) other.open = false;
        });
    });
  });

  collapseButton?.addEventListener("click", () => {
    eraStops.forEach((era) => {
      era.open = false;
    });
  });

  const cycleLinks = [...timeline.querySelectorAll("[data-cycle-link]")];
  const epochSections = [...timeline.querySelectorAll("[data-epoch-section]")];
  if ("IntersectionObserver" in window) {
    const visible = new Map();
    const updateCurrent = () => {
      const currentSection = [...visible.entries()]
        .filter(([, ratio]) => ratio > 0)
        .sort((a, b) => b[1] - a[1])[0]?.[0];
      const currentCycle = currentSection?.dataset.cycleSection;
      cycleLinks.forEach((link) => {
        if (link.dataset.cycleLink === currentCycle) {
          link.setAttribute("aria-current", "location");
        } else {
          link.removeAttribute("aria-current");
        }
      });
    };
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          visible.set(entry.target, entry.intersectionRatio);
        });
        updateCurrent();
      },
      { rootMargin: "-20% 0px -62% 0px", threshold: [0, 0.12, 0.35, 0.7] },
    );
    epochSections.forEach((section) => observer.observe(section));
  }

  refresh();
})();

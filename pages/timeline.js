(() => {
  const timeline = document.querySelector("[data-timeline]");
  if (!timeline) return;

  const eraStops = [...timeline.querySelectorAll("[data-era-stop]")];
  const collapseButton = timeline.querySelector("[data-collapse-eras]");

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

})();

(() => {
  const timeline = document.querySelector("[data-timeline]");
  if (!timeline) return;

  const buttons = [...timeline.querySelectorAll("[data-timeline-filter]")];
  const stories = [...timeline.querySelectorAll("[data-placement-confidence]")];
  const result = timeline.querySelector("[data-visible-total]");

  const applyFilter = (filter) => {
    let visibleTotal = 0;

    stories.forEach((story) => {
      const visible =
        filter === "all" || story.dataset.placementConfidence === filter;
      story.hidden = !visible;
      if (visible) visibleTotal += 1;
    });

    timeline.querySelectorAll("[data-story-group]").forEach((group) => {
      const visible = [...group.querySelectorAll("[data-placement-confidence]")].filter(
        (story) => !story.hidden,
      ).length;
      const count = group.querySelector("[data-group-visible]");
      if (count) count.textContent = String(visible);
      group.hidden = visible === 0;
    });

    timeline.querySelectorAll("[data-timeline-chapter]").forEach((chapter) => {
      const groups = [...chapter.querySelectorAll("[data-story-group]")];
      const hidden = groups.length > 0 && groups.every((group) => group.hidden);
      chapter.hidden = hidden;
      const stop = timeline.querySelector(`.timeline-orbit a[href="#${chapter.id}"]`);
      if (stop) stop.closest("li").hidden = hidden;
    });

    buttons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.timelineFilter === filter),
      );
    });
    if (result) result.textContent = String(visibleTotal);
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      applyFilter(button.dataset.timelineFilter || "all");
    });
  });
})();

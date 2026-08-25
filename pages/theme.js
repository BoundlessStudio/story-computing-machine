(function () {
  "use strict";

  var STORAGE_KEY = "story-computing-machine-theme";
  var DARK_QUERY = "(prefers-color-scheme: dark)";
  var root = document.documentElement;
  var toggle = document.querySelector("[data-theme-toggle]");
  var themeColor = document.querySelector('meta[name="theme-color"]');
  var mediaQuery = null;
  var hasExplicitPreference = false;
  var currentTheme = null;

  function validTheme(value) {
    return value === "light" || value === "dark" ? value : null;
  }

  function readPreference() {
    try {
      return validTheme(window.localStorage.getItem(STORAGE_KEY));
    } catch (error) {
      return null;
    }
  }

  function savePreference(theme) {
    if (!validTheme(theme)) {
      return;
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      // The selected theme still applies for this page when storage is unavailable.
    }
  }

  function preferredTheme() {
    if (!mediaQuery) {
      return "light";
    }

    try {
      return mediaQuery.matches ? "dark" : "light";
    } catch (error) {
      return "light";
    }
  }

  function updateThemeColor() {
    if (!themeColor) {
      return;
    }

    try {
      var paper = window.getComputedStyle(root).getPropertyValue("--paper").trim();
      if (paper) {
        themeColor.setAttribute("content", paper);
      }
    } catch (error) {
      // A theme-color fallback remains in the document when styles are unavailable.
    }
  }

  function updateToggle(theme) {
    if (!toggle) {
      return;
    }

    var nextTheme = theme === "dark" ? "light" : "dark";
    var action = "Switch to " + nextTheme + " mode";
    toggle.setAttribute("aria-label", action);
    toggle.setAttribute("title", action);
  }

  function applyTheme(theme) {
    var nextTheme = validTheme(theme) || "light";
    currentTheme = nextTheme;
    root.setAttribute("data-theme", nextTheme);
    root.style.colorScheme = nextTheme;
    updateToggle(nextTheme);
    updateThemeColor();
  }

  try {
    if (typeof window.matchMedia === "function") {
      mediaQuery = window.matchMedia(DARK_QUERY);
    }
  } catch (error) {
    mediaQuery = null;
  }

  var savedTheme = readPreference();
  hasExplicitPreference = savedTheme !== null;
  applyTheme(validTheme(root.getAttribute("data-theme")) || savedTheme || preferredTheme());

  if (toggle) {
    toggle.addEventListener("click", function () {
      var nextTheme = currentTheme === "dark" ? "light" : "dark";
      hasExplicitPreference = true;
      savePreference(nextTheme);
      applyTheme(nextTheme);
    });
  }

  function followSystemPreference(event) {
    if (!hasExplicitPreference) {
      applyTheme(event && typeof event.matches === "boolean"
        ? (event.matches ? "dark" : "light")
        : preferredTheme());
    }
  }

  if (mediaQuery) {
    try {
      if (typeof mediaQuery.addEventListener === "function") {
        mediaQuery.addEventListener("change", followSystemPreference);
      } else if (typeof mediaQuery.addListener === "function") {
        mediaQuery.addListener(followSystemPreference);
      }
    } catch (error) {
      // The initial theme and manual toggle remain usable without a media listener.
    }
  }
}());

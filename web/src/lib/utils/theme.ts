export type Theme = "light" | "dark";

// Get the system preference
function getSystemTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  return prefersDark ? "dark" : "light";
}

// Get the current theme override from localStorage, or null for auto
export function getThemeOverride(): Theme | null {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem("theme-override") as Theme | null;
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return null;
}

// Get effective theme (override or system)
export function getEffectiveTheme(): Theme {
  const override = getThemeOverride();
  return override || getSystemTheme();
}

// Apply theme to page
export function applyTheme() {
  if (typeof window === "undefined") return;
  const theme = getEffectiveTheme();
  document.documentElement.classList.toggle("dark", theme === "dark");
}

// Toggle theme override (cycle: auto -> dark -> light -> auto)
export function toggleTheme(): Theme | null {
  if (typeof window === "undefined") return null;

  const current = getThemeOverride();
  const system = getSystemTheme();

  let next: Theme | null;

  if (current === null) {
    // Currently auto, switch to opposite of system
    next = system === "dark" ? "light" : "dark";
  } else {
    // Currently overridden, go back to auto
    next = null;
  }

  if (next === null) {
    localStorage.removeItem("theme-override");
  } else {
    localStorage.setItem("theme-override", next);
  }

  applyTheme();
  return next;
}

// Initialize theme on app load
export function initializeTheme(): Theme | null {
  applyTheme();
  return getThemeOverride();
}

// Setup listener for system theme changes
export function setupThemeListener(onChange: () => void) {
  if (typeof window === "undefined") return () => {};

  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

  const handler = () => {
    // Only react if we're in auto mode (no override)
    if (getThemeOverride() === null) {
      applyTheme();
      onChange();
    }
  };

  mediaQuery.addEventListener("change", handler);

  return () => mediaQuery.removeEventListener("change", handler);
}

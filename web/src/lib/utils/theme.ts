export type Theme = "light" | "dark";

// Get the current theme from localStorage or system preference
export function getInitialTheme(): Theme {
  if (typeof window === "undefined") {
    return "dark";
  }

  // Check localStorage first
  const stored = localStorage.getItem("theme") as Theme | null;
  if (stored === "light" || stored === "dark") {
    return stored;
  }

  // Fall back to system preference
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  return prefersDark ? "dark" : "light";
}

// Apply theme to page
export function applyTheme(theme: Theme) {
  if (typeof window === "undefined") return;

  document.documentElement.classList.toggle("dark", theme === "dark");
  localStorage.setItem("theme", theme);
}

// Toggle between light and dark theme
export function toggleTheme(currentTheme: Theme): Theme {
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  applyTheme(newTheme);
  return newTheme;
}

// Initialize theme on app load
export function initializeTheme() {
  const theme = getInitialTheme();
  applyTheme(theme);
  return theme;
}

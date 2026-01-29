import { goto } from "$app/navigation";
import { browser } from "$app/environment";

export const ssr = false; // Disable SSR for SPA mode
export const prerender = true; // Enable prerendering for static export

export async function load({ url }) {
  if (browser) {
    const token = localStorage.getItem("auth_token");
    const isLoginPage = url.pathname === "/login";

    // Redirect to login if not authenticated and not on login page
    if (!token && !isLoginPage) {
      goto("/login");
      return {};
    }

    // Redirect to home if authenticated and on login page
    if (token && isLoginPage) {
      goto("/");
      return {};
    }
  }

  return {};
}

import createClient from "openapi-fetch";
import type { paths } from "./v1";

const client = createClient<paths>({});

// Add auth token to all requests
client.use({
  onRequest({ request }) {
    const token = localStorage.getItem("auth_token");
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  },
  onResponse({ response }) {
    // Handle 401 Unauthorized - auto logout
    if (response.status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("username");

      // Only redirect if not already on login page
      if (
        typeof window !== "undefined" &&
        !window.location.pathname.includes("/login")
      ) {
        window.location.href = "/login";
      }
    }
    return response;
  },
});

export default client;

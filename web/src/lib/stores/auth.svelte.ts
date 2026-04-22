import { goto } from "$app/navigation";
import client from "$lib/api/client";

interface AuthState {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

class AuthStore {
  private state = $state<AuthState>({
    token: null,
    username: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  });

  constructor() {
    if (typeof window !== "undefined") {
      this.initialize();
    }
  }

  get token() {
    return this.state.token;
  }

  get username() {
    return this.state.username;
  }

  get isAuthenticated() {
    return this.state.isAuthenticated;
  }

  get isLoading() {
    return this.state.isLoading;
  }

  get error() {
    return this.state.error;
  }

  private initialize() {
    const token = localStorage.getItem("auth_token");
    const username = localStorage.getItem("username");

    if (token && username) {
      this.state.token = token;
      this.state.username = username;
      this.state.isAuthenticated = true;
    }
  }

  async register(username: string, password: string): Promise<boolean> {
    this.state.isLoading = true;
    this.state.error = null;

    try {
      const { data, error } = await client.POST("/api/v1/auth/register", {
        body: { username, password },
      });

      if (error || !data) {
        this.state.error =
          (error as { detail?: string })?.detail === "Username already taken"
            ? "Username already taken"
            : "Registration failed. Please try again.";
        return false;
      }

      this.state.token = data.token;
      this.state.username = username;
      this.state.isAuthenticated = true;

      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("username", username);

      return true;
    } catch (err) {
      this.state.error = "Registration failed. Please try again.";
      console.error("Register error:", err);
      return false;
    } finally {
      this.state.isLoading = false;
    }
  }

  async login(username: string, password: string): Promise<boolean> {
    this.state.isLoading = true;
    this.state.error = null;

    try {
      const { data, error } = await client.POST("/api/v1/auth/login", {
        body: { username, password },
      });

      if (error || !data) {
        this.state.error = "Invalid credentials";
        return false;
      }

      this.state.token = data.token;
      this.state.username = username;
      this.state.isAuthenticated = true;

      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("username", username);

      return true;
    } catch (err) {
      this.state.error = "Login failed. Please try again.";
      console.error("Login error:", err);
      return false;
    } finally {
      this.state.isLoading = false;
    }
  }

  async logout() {
    if (this.state.token) {
      try {
        await client.POST("/api/v1/auth/logout", {});
      } catch {
        // ignore — token will expire on its own
      }
    }

    this.state.token = null;
    this.state.username = null;
    this.state.isAuthenticated = false;
    this.state.error = null;

    localStorage.removeItem("auth_token");
    localStorage.removeItem("username");

    goto("/login");
  }

  clearError() {
    this.state.error = null;
  }
}

export const authStore = new AuthStore();

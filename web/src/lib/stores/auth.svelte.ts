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
    // Initialize from localStorage on client side
    if (typeof window !== "undefined") {
      this.initialize();
    }
  }

  // Getters using $derived
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

  // Initialize auth state from localStorage
  private initialize() {
    const token = localStorage.getItem("auth_token");
    const username = localStorage.getItem("username");

    if (token && username) {
      this.state.token = token;
      this.state.username = username;
      this.state.isAuthenticated = true;
    }
  }

  // Login user
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

      // Update state
      this.state.token = data.token;
      this.state.username = username;
      this.state.isAuthenticated = true;

      // Persist to localStorage
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

  // Logout user
  logout() {
    this.state.token = null;
    this.state.username = null;
    this.state.isAuthenticated = false;
    this.state.error = null;

    localStorage.removeItem("auth_token");
    localStorage.removeItem("username");

    goto("/login");
  }

  // Clear error message
  clearError() {
    this.state.error = null;
  }
}

// Export singleton instance
export const authStore = new AuthStore();

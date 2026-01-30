<script lang="ts">
  import { goto } from "$app/navigation";
  import { Button } from "$lib/elements/button/index.js";
  import * as Card from "$lib/elements/card/index.js";
  import { Input } from "$lib/elements/input/index.js";
  import { Label } from "$lib/elements/label/index.js";
  import { authStore } from "$lib/stores/auth.svelte";
  import {
    getEffectiveTheme,
    initializeTheme,
    setupThemeListener,
    toggleTheme,
    type Theme,
  } from "$lib/utils/theme";
  import { MoonIcon, SunIcon } from "@lucide/svelte/icons";
  import { onMount } from "svelte";

  let username = $state("");
  let password = $state("");
  let themeOverride = $state<Theme | null>(null);
  let currentTheme = $state<Theme>("dark");

  onMount(() => {
    themeOverride = initializeTheme();
    currentTheme = getEffectiveTheme();

    const cleanup = setupThemeListener(() => {
      themeOverride = themeOverride;
      currentTheme = getEffectiveTheme();
    });

    if (authStore.isAuthenticated) {
      goto("/");
    }

    return cleanup;
  });

  async function handleLogin(e: SubmitEvent) {
    e.preventDefault();
    const success = await authStore.login(username, password);
    if (success) {
      goto("/");
    }
  }

  function handleToggleTheme() {
    themeOverride = toggleTheme();
    currentTheme = getEffectiveTheme();
  }
</script>

<div class="flex items-center justify-center min-h-screen bg-background px-4">
  <div class="fixed absolute top-4 right-4 pt-[env(safe-area-inset-top)]">
    <Button size="icon" variant="ghost" onclick={handleToggleTheme}>
      {#if currentTheme === "dark"}
        <SunIcon class="size-5" />
      {:else}
        <MoonIcon class="size-5" />
      {/if}
    </Button>
  </div>

  <Card.Root class="fixed w-full max-w-sm">
    <Card.Header>
      <Card.Title>Welcome to Grindboard</Card.Title>
      <Card.Description>Sign in to manage your tasks</Card.Description>
    </Card.Header>
    <form onsubmit={handleLogin}>
      <Card.Content class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <Label for="username">Username</Label>
          <Input
            id="username"
            type="text"
            bind:value={username}
            placeholder="Enter username"
            required
          />
        </div>
        <div class="flex flex-col gap-2">
          <Label for="password">Password</Label>
          <Input
            id="password"
            type="password"
            bind:value={password}
            placeholder="Enter password"
            required
          />
        </div>
        {#if authStore.error}
          <p class="text-sm text-destructive">{authStore.error}</p>
        {/if}
      </Card.Content>
      <Card.Footer class="flex flex-col pt-6">
        <Button type="submit" class="w-full" disabled={authStore.isLoading}>
          {authStore.isLoading ? "Logging in..." : "Login"}
        </Button>
      </Card.Footer>
    </form>
  </Card.Root>
</div>

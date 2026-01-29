<script lang="ts">
  import "./layout.css";

  let { children } = $props();
</script>

<svelte:head>
  <meta
    name="viewport"
    content="width=device-width,initial-scale=1,viewport-fit=cover"
  />
  <title>Grindboard</title>
  <meta name="description" content="Minimal task management app" />

  <!-- Icons -->
  <link rel="icon" href="/favicon.svg" sizes="any" type="image/svg+xml" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
  <link rel="shortcut icon" href="/favicon.svg" sizes="32x32" />

  <!-- PWA Meta Tags -->
  <meta name="theme-color" content="#000000" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
  />
  <meta name="apple-mobile-web-app-title" content="Grindboard" />

  <!-- PWA Manifest -->
  <link rel="manifest" href="/manifest.webmanifest" />
</svelte:head>

{@render children()}

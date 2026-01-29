import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),

  kit: {
    paths: { relative: false },
    alias: {
      $lib: "src/lib",
      "$lib/*": "src/lib/*",
      $elements: "src/lib/elements",
      "$elements/*": "src/lib/elements/*",
      $dialogs: "src/lib/dialogs",
      "$dialogs/*": "src/lib/dialogs/*",
      $components: "src/lib/components",
      "$components/*": "src/lib/components/*",
    },
    adapter: adapter({
      pages: "build",
      assets: "build",
      fallback: "index.html",
      precompress: false,
      strict: true,
    }),
    prerender: {
      entries: ["*"],
      handleHttpError: "warn",
    },
  },
};

export default config;

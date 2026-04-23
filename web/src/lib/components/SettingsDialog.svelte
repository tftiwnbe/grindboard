<script lang="ts">
  import { Button } from "$lib/elements/button/index.js";
  import { Checkbox } from "$lib/elements/checkbox/index.js";
  import * as Dialog from "$lib/elements/dialog/index.js";
  import { Label } from "$lib/elements/label/index.js";

  interface Settings {
    addNewTasksToTop: boolean;
  }

  interface Props {
    open: boolean;
    onClose: () => void;
  }

  let { open = $bindable(), onClose }: Props = $props();

  const STORAGE_KEY = "grindboard:settings";

  function load(): Settings {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return { addNewTasksToTop: false, ...JSON.parse(raw) };
    } catch {}
    return { addNewTasksToTop: false };
  }

  function save(s: Settings) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  }

  let settings = $state<Settings>(load());

  function toggle(key: keyof Settings) {
    settings = { ...settings, [key]: !settings[key] };
    save(settings);
  }
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="max-w-sm">
    <Dialog.Header>
      <Dialog.Title>Settings</Dialog.Title>
      <Dialog.Description>Adjust your Grindboard preferences</Dialog.Description>
    </Dialog.Header>

    <div class="space-y-4 py-2">
      <div class="flex items-center justify-between gap-4">
        <Label for="setting-top" class="text-sm font-normal cursor-pointer">
          Add new tasks to top
        </Label>
        <Checkbox
          id="setting-top"
          checked={settings.addNewTasksToTop}
          onCheckedChange={() => toggle("addNewTasksToTop")}
        />
      </div>
    </div>

    <Dialog.Footer>
      <Button variant="outline" onclick={onClose}>Close</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>

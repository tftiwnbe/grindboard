<script lang="ts">
  import type { components } from "$lib/api/v1";
  import { Button } from "$lib/elements/button/index.js";
  import * as Dialog from "$lib/elements/dialog/index.js";
  import { Input } from "$lib/elements/input/index.js";
  import { Label } from "$lib/elements/label/index.js";
  import { Textarea } from "$lib/elements/textarea/index.js";
  import { XIcon } from "@lucide/svelte/icons";
  import TagSelector from "./TagSelector.svelte";

  type Task = components["schemas"]["TaskRead"];
  type Tag = components["schemas"]["TagRead"];

  interface Props {
    open: boolean;
    dialogMode: "create" | "edit";
    task?: Task | null;
    allTags: Tag[];
    selectedTags: Tag[];
    onClose: () => void;
    onSubmit: (
      title: string,
      description: string,
      tags: Tag[],
      deadline: string | null,
      keepOpen: boolean,
    ) => Promise<void>;
    onCreateTag: (name: string) => Promise<void>;
    isLoading?: boolean;
  }

  let {
    open = $bindable(),
    dialogMode,
    task = null,
    allTags,
    selectedTags = $bindable(),
    onClose,
    onSubmit,
    onCreateTag,
    isLoading = false,
  }: Props = $props();

  let title = $state("");
  let description = $state("");
  let deadline = $state("");

  $effect(() => {
    if (open) {
      if (dialogMode === "edit" && task) {
        title = task.title;
        description = task.description ?? "";
        deadline = task.deadline ?? "";
      } else if (dialogMode === "create") {
        title = "";
        description = "";
        deadline = "";
      }
    }
  });

  function handleToggleTag(tag: Tag, isSelected: boolean) {
    if (isSelected) {
      selectedTags = selectedTags.filter((t) => t.id !== tag.id);
    } else {
      selectedTags = [...selectedTags, tag];
    }
  }

  async function handleSubmit(e: SubmitEvent, keepOpen: boolean) {
    e.preventDefault();
    if (!title.trim()) return;
    await onSubmit(title.trim(), description, selectedTags, deadline || null, keepOpen);
    if (keepOpen) {
      title = "";
      description = "";
      deadline = "";
      selectedTags = [];
    }
  }

  function handleClose() {
    title = "";
    description = "";
    deadline = "";
    onClose();
  }


</script>

<Dialog.Root bind:open>
  <Dialog.Content class="max-w-md">
    <Dialog.Header>
      <Dialog.Title>{dialogMode === "create" ? "Create Task" : "Edit Task"}</Dialog.Title>
      <Dialog.Description>
        {dialogMode === "create" ? "Add a new task to your list" : "Update task details"}
      </Dialog.Description>
    </Dialog.Header>
    <form onsubmit={(e) => handleSubmit(e, false)} class="space-y-3">
      <div class="space-y-1.5">
        <Label for="task-title">Title</Label>
        <Input
          id="task-title"
          bind:value={title}
          placeholder="Task title"
          autofocus={dialogMode === "create"}
          required
        />
      </div>

      <div class="space-y-1.5">
        <Label for="task-description">Description</Label>
        <Textarea
          id="task-description"
          bind:value={description}
          placeholder="Description (optional)"
          rows={2}
        />
      </div>

      <div class="space-y-1.5">
        <Label for="task-deadline">Deadline</Label>
        <div class="relative">
          <Input
            id="task-deadline"
            type="date"
            bind:value={deadline}
            class="w-full {deadline ? 'pr-8' : ''}"
          />
          {#if deadline}
            <button
              type="button"
              onclick={() => (deadline = "")}
              class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear deadline"
            >
              <XIcon class="size-4" />
            </button>
          {/if}
        </div>
      </div>

      <TagSelector
        {allTags}
        bind:selectedTags
        onToggleTag={handleToggleTag}
        {onCreateTag}
      />

      <Dialog.Footer class="flex gap-2 pt-1">
        <Button type="button" variant="outline" onclick={handleClose} class="flex-1">
          Cancel
        </Button>
        {#if dialogMode === "create"}
          <Button
            type="button"
            variant="outline"
            disabled={isLoading}
            onclick={(e) => handleSubmit(e as unknown as SubmitEvent, true)}
            class="flex-1"
          >
            {isLoading ? "Saving…" : "One more"}
          </Button>
        {/if}
        <Button type="submit" disabled={isLoading} class="flex-1">
          {isLoading ? "Saving…" : dialogMode === "create" ? "Create" : "Update"}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>

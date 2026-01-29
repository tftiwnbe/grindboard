<script lang="ts">
  import type { components } from "$lib/api/v1";
  import { Button } from "$lib/elements/button/index.js";
  import * as Dialog from "$lib/elements/dialog/index.js";
  import { Input } from "$lib/elements/input/index.js";
  import { Label } from "$lib/elements/label/index.js";
  import { Textarea } from "$lib/elements/textarea/index.js";
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

  // Initialize form when dialog opens or task changes
  $effect(() => {
    if (open) {
      if (dialogMode === "edit" && task) {
        title = task.title;
        description = task.description || "";
      } else if (dialogMode === "create") {
        title = "";
        description = "";
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

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    await onSubmit(title, description, selectedTags);
    // Clear form after successful submit
    title = "";
    description = "";
  }

  function handleClose() {
    title = "";
    description = "";
    onClose();
  }
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="max-w-md">
    <Dialog.Header>
      <Dialog.Title
        >{dialogMode === "create" ? "Create Task" : "Edit Task"}</Dialog.Title
      >
      <Dialog.Description>
        {dialogMode === "create"
          ? "Add a new task to your list"
          : "Update task details"}
      </Dialog.Description>
    </Dialog.Header>
    <form onsubmit={handleSubmit} class="space-y-4">
      <div class="space-y-2">
        <Label for="task-title">Title</Label>
        <Input
          id="task-title"
          bind:value={title}
          placeholder="Task title"
          required
        />
      </div>
      <div class="space-y-2">
        <Label for="task-description">Description</Label>
        <Textarea
          id="task-description"
          bind:value={description}
          placeholder="Description (optional)"
          rows={3}
        ></Textarea>
      </div>

      <TagSelector
        {allTags}
        bind:selectedTags
        onToggleTag={handleToggleTag}
        {onCreateTag}
      />

      <Dialog.Footer>
        <Button type="button" variant="outline" onclick={handleClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {dialogMode === "create" ? "Create" : "Update"}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>

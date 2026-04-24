<script lang="ts">
  import type { components } from "$lib/api/v1";
  import { Button } from "$lib/elements/button/index.js";
  import * as Dialog from "$lib/elements/dialog/index.js";
  import { Input } from "$lib/elements/input/index.js";
  import { PencilIcon, PlusIcon, TrashIcon } from "@lucide/svelte/icons";

  type Tag = components["schemas"]["TagRead"];

  interface Props {
    open: boolean;
    tags: Tag[];
    onClose: () => void;
    onCreate: (name: string) => Promise<void>;
    onUpdate: (tagId: number, name: string) => Promise<void>;
    onDelete: (tagId: number) => Promise<void>;
  }

  let {
    open = $bindable(),
    tags,
    onClose,
    onCreate,
    onUpdate,
    onDelete,
  }: Props = $props();

  let newTagName = $state("");
  let editingTagId = $state<number | null>(null);
  let editingTagName = $state("");
  let isSaving = $state(false);

  async function handleCreate() {
    if (!newTagName.trim() || isSaving) return;
    isSaving = true;
    await onCreate(newTagName.trim());
    newTagName = "";
    isSaving = false;
  }

  function startEdit(tag: Tag) {
    editingTagId = tag.id ?? null;
    editingTagName = tag.name;
  }

  async function handleUpdate() {
    if (!editingTagId || !editingTagName.trim() || isSaving) return;
    isSaving = true;
    await onUpdate(editingTagId, editingTagName.trim());
    editingTagId = null;
    editingTagName = "";
    isSaving = false;
  }

  function cancelEdit() {
    editingTagId = null;
    editingTagName = "";
  }
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="max-w-md">
    <Dialog.Header>
      <Dialog.Title>Manage Tags</Dialog.Title>
      <Dialog.Description>Create, edit, or delete tags</Dialog.Description>
    </Dialog.Header>
    <div class="space-y-3">
      <form onsubmit={(e) => { e.preventDefault(); handleCreate(); }} class="flex gap-2">
        <Input
          bind:value={newTagName}
          placeholder="New tag name"
          class="flex-1 text-base"
          disabled={isSaving}
        />
        <Button type="submit" size="sm" disabled={isSaving || !newTagName.trim()}>
          <PlusIcon class="size-4 mr-1" />
          {isSaving ? "…" : "Create"}
        </Button>
      </form>

      {#if tags.length === 0}
        <p class="text-center text-muted-foreground py-8 text-sm">
          No tags here. Don't leave your tasks lonely.
        </p>
      {:else}
        <div class="space-y-1.5 max-h-[50vh] overflow-y-auto">
          {#each tags as tag (tag.id)}
            <div class="flex items-center gap-2 p-2 border rounded">
              {#if editingTagId === tag.id}
                <Input
                  bind:value={editingTagName}
                  class="flex-1 h-8 text-base"
                  autofocus
                  disabled={isSaving}
                  onkeydown={(e) => { if (e.key === "Escape") cancelEdit(); }}
                />
                <Button size="sm" class="h-8" onclick={handleUpdate} disabled={isSaving}>
                  {isSaving ? "…" : "Save"}
                </Button>
                <Button size="sm" variant="ghost" class="h-8" onclick={cancelEdit} disabled={isSaving}>
                  Cancel
                </Button>
              {:else}
                <span class="flex-1 text-sm">{tag.name}</span>
                <Button
                  size="icon"
                  variant="ghost"
                  class="h-7 w-7"
                  onclick={() => startEdit(tag)}
                  disabled={isSaving}
                >
                  <PencilIcon class="size-3.5" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  class="h-7 w-7"
                  onclick={() => { if (tag.id !== null) onDelete(tag.id); }}
                  disabled={isSaving}
                >
                  <TrashIcon class="size-3.5 text-destructive" />
                </Button>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
    <Dialog.Footer>
      <Button variant="outline" onclick={onClose}>Done</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>

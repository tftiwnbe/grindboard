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

  async function handleCreate() {
    if (!newTagName.trim()) return;
    await onCreate(newTagName);
    newTagName = "";
  }

  function startEdit(tag: Tag) {
    editingTagId = tag.id || null;
    editingTagName = tag.name;
  }

  async function handleUpdate() {
    if (!editingTagId || !editingTagName.trim()) return;
    await onUpdate(editingTagId, editingTagName);
    editingTagId = null;
    editingTagName = "";
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
    <div class="space-y-4">
      <form onsubmit={handleCreate} class="flex gap-2">
        <Input
          bind:value={newTagName}
          placeholder="New tag name"
          class="flex-1 text-base"
        />
        <Button type="submit" size="sm">
          <PlusIcon class="size-4 mr-1" />
          Create
        </Button>
      </form>

      {#if tags.length === 0}
        <p class="text-center text-muted-foreground py-8 text-sm">
          No tags here. Don’t leave your tasks lonely.
        </p>
      {:else}
        <div class="space-y-2 max-h-[50vh] overflow-y-auto">
          {#each tags as tag (tag.id)}
            <div class="flex items-center gap-2 p-2 border rounded-md">
              {#if editingTagId === tag.id}
                <Input
                  bind:value={editingTagName}
                  class="flex-1 h-9 text-base"
                  autofocus
                />
                <Button size="sm" class="h-9" onclick={handleUpdate}>
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  class="h-9"
                  onclick={cancelEdit}
                >
                  Cancel
                </Button>
              {:else}
                <span class="flex-1 text-sm">{tag.name}</span>
                <Button
                  size="icon"
                  variant="ghost"
                  class="h-8 w-8"
                  onclick={() => startEdit(tag)}
                >
                  <PencilIcon class="size-4" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  class="h-8 w-8"
                  onclick={() => onDelete(tag.id || 0)}
                >
                  <TrashIcon class="size-4 text-destructive" />
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

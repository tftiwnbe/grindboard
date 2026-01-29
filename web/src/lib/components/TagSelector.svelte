<script lang="ts">
  import type { components } from "$lib/api/v1";
  import { Button } from "$lib/elements/button/index.js";
  import { Input } from "$lib/elements/input/index.js";
  import { Label } from "$lib/elements/label/index.js";
  import { PlusIcon, XIcon } from "@lucide/svelte/icons";

  type Tag = components["schemas"]["TagRead"];

  interface Props {
    allTags: Tag[];
    selectedTags: Tag[];
    onToggleTag: (tag: Tag, isSelected: boolean) => void;
    onCreateTag: (name: string) => Promise<void>;
    isCreating?: boolean;
  }

  let {
    allTags,
    selectedTags = $bindable(),
    onToggleTag,
    onCreateTag,
  }: Props = $props();

  let showCreateInput = $state(false);
  let newTagName = $state("");
  let isSubmitting = $state(false);

  async function handleCreateTag() {
    if (!newTagName.trim() || isSubmitting) return;
    isSubmitting = true;
    await onCreateTag(newTagName);
    newTagName = "";
    showCreateInput = false;
    isSubmitting = false;
  }

  // Reset state when component unmounts or dialog closes
  $effect(() => {
    return () => {
      showCreateInput = false;
      newTagName = "";
    };
  });
</script>

<div class="space-y-3">
  <div>
    <Label>Tags</Label>
    <div class="flex flex-wrap gap-1.5 mt-2">
      {#if allTags.length > 0}
        {#each allTags as tag}
          {@const isSelected = selectedTags.find((t) => t.id === tag.id)}
          <Button
            type="button"
            variant={isSelected ? "default" : "outline"}
            size="sm"
            class="h-7 text-xs"
            onclick={() => onToggleTag(tag, !!isSelected)}
          >
            {tag.name}
          </Button>
        {/each}
      {:else}
        <p class="text-xs text-muted-foreground">
          Shh… the emptiness is listening.
        </p>
      {/if}
    </div>
  </div>

  {#if showCreateInput}
    <div class="border-t pt-3">
      <Label class="text-xs text-muted-foreground">Create new tag</Label>
      <div class="flex gap-2 mt-2">
        <div class="relative flex-1">
          <Input
            bind:value={newTagName}
            placeholder="Tag name"
            class="h-9 text-base pr-8"
            autofocus
            onkeydown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleCreateTag();
              }
            }}
          />
          <button
            type="button"
            onclick={() => {
              showCreateInput = false;
              newTagName = "";
            }}
            class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <XIcon class="size-4" />
          </button>
        </div>
        <Button
          type="button"
          size="sm"
          class="h-9"
          disabled={isSubmitting}
          onclick={handleCreateTag}
        >
          {isSubmitting ? "..." : "Add"}
        </Button>
      </div>
    </div>
  {:else}
    <Button
      type="button"
      variant="ghost"
      size="sm"
      class="h-7 text-xs w-full"
      onclick={() => (showCreateInput = true)}
    >
      <PlusIcon class="size-3 mr-1" />
      Create new tag
    </Button>
  {/if}
</div>

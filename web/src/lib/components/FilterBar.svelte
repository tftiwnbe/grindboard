<script lang="ts">
  import type { components } from "$lib/api/v1";
  import { Button } from "$lib/elements/button/index.js";
  import { Input } from "$lib/elements/input/index.js";
  import { XIcon } from "@lucide/svelte/icons";

  type Tag = components["schemas"]["TagRead"];

  interface Props {
    searchQuery: string;
    selectedFilterTags: number[];
    allTags: Tag[];
    onToggleTag: (tagId: number) => void;
    onClear: () => void;
  }

  let {
    searchQuery = $bindable(),
    selectedFilterTags,
    allTags,
    onToggleTag,
    onClear,
  }: Props = $props();
</script>

<div class="space-y-2">
  <Input
    bind:value={searchQuery}
    placeholder="Search tasks..."
    class="w-full text-base"
  />

  {#if allTags.length > 0}
    <div class="flex flex-wrap gap-1.5">
      {#each allTags as tag}
        {@const isActive = selectedFilterTags.includes(tag.id || 0)}
        <Button
          type="button"
          variant={isActive ? "default" : "outline"}
          size="sm"
          class="h-7 text-xs"
          onclick={() => onToggleTag(tag.id || 0)}
        >
          {tag.name}
        </Button>
      {/each}

      {#if searchQuery || selectedFilterTags.length > 0}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="h-7 text-xs"
          onclick={onClear}
        >
          <XIcon class="size-3 mr-1" />
          Clear
        </Button>
      {/if}
    </div>
  {/if}
</div>

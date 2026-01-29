<script lang="ts">
  import type { components } from "$lib/api/v1";
  import { Button } from "$lib/elements/button/index.js";
  import { Input } from "$lib/elements/input/index.js";
  import type { SortOption } from "$lib/stores/tasks.svelte";
  import {
    ArrowDownAZIcon,
    ArrowUpAZIcon,
    CheckIcon,
    ListOrderedIcon,
    SquircleIcon,
    XIcon,
  } from "@lucide/svelte/icons";

  type Tag = components["schemas"]["TagRead"];

  interface Props {
    searchQuery: string;
    selectedFilterTags: number[];
    allTags: Tag[];
    showCompleted: boolean;
    sortBy: SortOption;
    onToggleTag: (tagId: number) => void;
    onClear: () => void;
    onToggleCompleted: () => void;
    onSortChange: (sort: SortOption) => void;
  }

  let {
    searchQuery = $bindable(),
    selectedFilterTags,
    allTags,
    showCompleted,
    sortBy,
    onToggleTag,
    onClear,
    onToggleCompleted,
    onSortChange,
  }: Props = $props();

  const sortOptions: Array<{ value: SortOption; label: string }> = [
    { value: "manual", label: "Manual order" },
    { value: "alpha-asc", label: "Sort A to Z" },
    { value: "alpha-desc", label: "Sort Z to A" },
  ];

  let currentSortIndex = $state(0);

  $effect(() => {
    currentSortIndex = sortOptions.findIndex((opt) => opt.value === sortBy);
  });

  function cycleSortOption() {
    const nextIndex = (currentSortIndex + 1) % sortOptions.length;
    onSortChange(sortOptions[nextIndex].value);
  }
</script>

<div class="space-y-2">
  <div class="flex items-center gap-2">
    <Input
      bind:value={searchQuery}
      placeholder="Search tasks..."
      class="flex-1 text-base"
    />

    <Button
      type="button"
      variant={showCompleted ? "default" : "outline"}
      size="icon"
      class="h-10 w-10 shrink-0"
      onclick={onToggleCompleted}
      title={showCompleted ? "Show uncompleted tasks" : "Show completed tasks"}
    >
      {#if showCompleted}
        <CheckIcon class="size-5" />
      {:else}
        <SquircleIcon class="size-5" />
      {/if}
    </Button>

    <Button
      type="button"
      variant="outline"
      size="icon"
      class="h-10 w-10 shrink-0"
      onclick={cycleSortOption}
      title={sortOptions[currentSortIndex].label}
    >
      {#if sortBy === "manual"}
        <ListOrderedIcon class="size-5" />
      {:else if sortBy === "alpha-asc"}
        <ArrowUpAZIcon class="size-5" />
      {:else if sortBy === "alpha-desc"}
        <ArrowDownAZIcon class="size-5" />
      {/if}
    </Button>
  </div>

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

<script lang="ts">
  import type { components } from "$lib/api/v1";
  import { Button } from "$lib/elements/button/index.js";
  import { Checkbox } from "$lib/elements/checkbox/index.js";
  import { TrashIcon } from "@lucide/svelte/icons";

  type Task = components["schemas"]["TaskRead"];
  type Tag = components["schemas"]["TagRead"];

  interface Props {
    task: Task;
    tags: Tag[];
    onToggle: (taskId: number) => void;
    onEdit: (task: Task) => void;
    onDelete: (taskId: number) => void;
    onDragStart?: (taskId: number) => void;
    onDragOver?: (taskId: number) => void;
    onDragEnd?: () => void;
    isDragging?: boolean;
    isDragOver?: boolean;
  }

  let {
    task,
    tags,
    onToggle,
    onEdit,
    onDelete,
    onDragStart,
    onDragOver,
    onDragEnd,
    isDragging = false,
    isDragOver = false,
  }: Props = $props();

  function handleDragStart(e: DragEvent) {
    e.dataTransfer!.effectAllowed = "move";
    e.dataTransfer!.setData("application/x-task-id", task.id.toString());
    onDragStart?.(task.id);
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    e.dataTransfer!.dropEffect = "move";
    onDragOver?.(task.id);
  }

  function handleDragEnd() {
    onDragEnd?.();
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
  }
</script>

<div
  role="listitem"
  class="border rounded-lg bg-card p-4 transition-opacity cursor-move"
  class:opacity-50={isDragging}
  class:border-primary={isDragOver}
  class:border-2={isDragOver}
  draggable="true"
  ondragstart={handleDragStart}
  ondragover={handleDragOver}
  ondragend={handleDragEnd}
  ondrop={handleDrop}
>
  <div class="flex items-start gap-3">
    <Checkbox
      checked={task.completed}
      onCheckedChange={() => onToggle(task.id)}
      class="mt-1"
    />

    <button class="flex-1 min-w-0 text-left" onclick={() => onEdit(task)}>
      <h3
        class="font-medium text-base leading-snug"
        class:line-through={task.completed}
        class:text-muted-foreground={task.completed}
      >
        {task.title}
      </h3>
      {#if task.description}
        <p
          class="text-sm text-muted-foreground mt-1 whitespace-pre-wrap"
          class:line-through={task.completed}
        >
          {task.description}
        </p>
      {/if}

      <!-- Tags Display -->
      {#if tags.length > 0}
        <div class="flex flex-wrap gap-1.5 mt-3">
          {#each tags as tag (tag.id)}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              class="h-6 text-xs px-2 pointer-events-none"
            >
              {tag.name}
            </Button>
          {/each}
        </div>
      {/if}
    </button>

    <Button
      variant="ghost"
      size="icon"
      onclick={() => onDelete(task.id)}
      class="shrink-0 -mt-1"
    >
      <TrashIcon class="size-4 text-muted-foreground" />
    </Button>
  </div>
</div>

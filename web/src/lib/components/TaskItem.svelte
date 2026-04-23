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

  function handleDrop(e: DragEvent) { e.preventDefault(); }

  function formatCompletedAt(iso: string): string {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffDays = Math.floor(diffMs / 86_400_000);
    if (diffDays === 0) return "Completed today";
    if (diffDays === 1) return "Completed yesterday";
    if (diffDays < 7) return `Completed ${diffDays} days ago`;
    return `Completed ${d.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
  }

  function deadlineLabel(iso: string): { text: string; urgent: boolean; overdue: boolean } {
    const deadline = new Date(iso + "T00:00:00");
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffDays = Math.round((deadline.getTime() - today.getTime()) / 86_400_000);
    if (diffDays < 0) return { text: `Overdue · ${deadline.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`, urgent: false, overdue: true };
    if (diffDays === 0) return { text: "Due today", urgent: true, overdue: false };
    if (diffDays === 1) return { text: "Due tomorrow", urgent: true, overdue: false };
    return { text: `Due ${deadline.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`, urgent: false, overdue: false };
  }
</script>

<div
  role="listitem"
  class="border rounded bg-card px-3 py-2 transition-opacity cursor-move"
  class:opacity-40={isDragging}
  class:border-primary={isDragOver}
  class:border-2={isDragOver}
  draggable="true"
  ondragstart={handleDragStart}
  ondragover={handleDragOver}
  ondragend={onDragEnd}
  ondrop={handleDrop}
>
  <div class="flex items-start gap-2">
    <Checkbox
      checked={task.completed}
      onCheckedChange={() => onToggle(task.id)}
      class="mt-0.5 shrink-0"
    />

    <button class="flex-1 min-w-0 text-left" onclick={() => onEdit(task)}>
      <p
        class="text-sm font-medium leading-snug"
        class:line-through={task.completed}
        class:text-muted-foreground={task.completed}
      >
        {task.title}
      </p>

      {#if task.description}
        <p
          class="text-xs text-muted-foreground mt-0.5 whitespace-pre-wrap"
          class:line-through={task.completed}
        >
          {task.description}
        </p>
      {/if}

      {#if !task.completed && task.deadline}
        {@const dl = deadlineLabel(task.deadline)}
        <p
          class="text-xs mt-1"
          class:text-destructive={dl.overdue}
          class:text-amber-500={dl.urgent && !dl.overdue}
          class:text-muted-foreground={!dl.overdue && !dl.urgent}
        >
          {dl.text}
        </p>
      {/if}

      {#if task.completed && task.completed_at}
        <p class="text-xs text-muted-foreground mt-0.5">
          {formatCompletedAt(task.completed_at)}
        </p>
      {/if}

      {#if tags.length > 0}
        <div class="flex flex-wrap gap-1 mt-1.5">
          {#each tags as tag (tag.id)}
            <span class="text-xs px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground">
              {tag.name}
            </span>
          {/each}
        </div>
      {/if}
    </button>

    <Button
      variant="ghost"
      size="icon"
      onclick={() => onDelete(task.id)}
      class="shrink-0 h-7 w-7 -mt-0.5"
    >
      <TrashIcon class="size-3.5 text-muted-foreground" />
    </Button>
  </div>
</div>

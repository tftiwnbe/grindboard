<script lang="ts">
  import type { components } from "$lib/api/v1";
  import FilterBar from "$lib/components/FilterBar.svelte";
  import TagManager from "$lib/components/TagManager.svelte";
  import TaskDialog from "$lib/components/TaskDialog.svelte";
  import TaskItem from "$lib/components/TaskItem.svelte";
  import { Button } from "$lib/elements/button/index.js";
  import { ScrollArea } from "$lib/elements/scroll-area/index.js";
  import { authStore } from "$lib/stores/auth.svelte";
  import { tagsStore } from "$lib/stores/tags.svelte";
  import type { SortOption } from "$lib/stores/tasks.svelte";
  import { tasksStore } from "$lib/stores/tasks.svelte";
  import {
    getEffectiveTheme,
    initializeTheme,
    setupThemeListener,
    toggleTheme,
    type Theme,
  } from "$lib/utils/theme";
  import {
    LogOutIcon,
    MoonIcon,
    PlusIcon,
    SunIcon,
    TagIcon,
  } from "@lucide/svelte/icons";
  import { onMount } from "svelte";

  type Task = components["schemas"]["TaskRead"];
  type Tag = components["schemas"]["TagRead"];

  // UI State
  let themeOverride = $state<Theme | null>(null);
  let showTaskDialog = $state(false);
  let showTagManager = $state(false);
  let dialogMode = $state<"create" | "edit">("create");
  let editingTask = $state<Task | null>(null);
  let selectedDialogTags = $state<Tag[]>([]);

  // Filter State
  let searchQuery = $state("");
  let selectedFilterTags = $state<number[]>([]);

  // Derived filtered tasks
  const filteredTasks = $derived(() => {
    let result = tasksStore.getSortedTasks();

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (task) =>
          task.title.toLowerCase().includes(query) ||
          task.description?.toLowerCase().includes(query),
      );
    }

    // Tag filter
    if (selectedFilterTags.length > 0) {
      result = result.filter((task) => {
        return selectedFilterTags.some((tagId) =>
          task.tags.some((tag) => tag.id === tagId),
        );
      });
    }

    return result;
  });

  // Count of uncompleted tasks
  const uncompletedCount = $derived(
    tasksStore.tasks.filter((t) => !t.completed).length,
  );

  onMount(() => {
    themeOverride = initializeTheme();

    // Setup listener for system theme changes
    const cleanup = setupThemeListener(() => {
      // Force re-render when system theme changes (only matters if override is null)
      themeOverride = themeOverride;
    });

    // Load initial data
    Promise.all([tasksStore.fetchTasks(), tagsStore.fetchTags()]);

    return cleanup;
  });

  function handleToggleTheme() {
    themeOverride = toggleTheme();
  }

  function handleCreateTask() {
    dialogMode = "create";
    editingTask = null;
    selectedDialogTags = [];
    showTaskDialog = true;
  }

  function handleEditTask(task: Task) {
    dialogMode = "edit";
    editingTask = task;
    selectedDialogTags = task.tags;
    showTaskDialog = true;
  }

  async function handleSubmitTask(
    title: string,
    description: string,
    tags: Tag[],
  ) {
    const tagIds = tags
      .map((t) => t.id)
      .filter((id): id is number => id !== null);

    if (dialogMode === "create") {
      await tasksStore.createTask({ title, description }, tagIds);
    } else if (editingTask) {
      await tasksStore.updateTask(
        editingTask.id,
        { title, description },
        tagIds,
      );
    }

    showTaskDialog = false;
    await tagsStore.fetchTags();
  }

  async function handleCreateTag(name: string) {
    const newTag = await tagsStore.createTag(name);
    if (newTag && dialogMode === "edit" && editingTask) {
      selectedDialogTags = [...selectedDialogTags, newTag];
    }
  }

  async function handleToggleTask(taskId: number) {
    await tasksStore.toggleTask(taskId);
  }

  async function handleDeleteTask(taskId: number) {
    await tasksStore.deleteTask(taskId);
  }

  // Drag and drop handlers
  function handleDragStart(taskId: number) {
    tasksStore.setDraggedTask(taskId);
  }

  function handleDragOver(taskId: number) {
    tasksStore.setDragOverTask(taskId);
  }

  async function handleDragEnd() {
    await tasksStore.handleDrop();
  }

  // Tag manager handlers
  async function handleCreateTagInManager(name: string) {
    await tagsStore.createTag(name);
  }

  async function handleUpdateTag(tagId: number, name: string) {
    await tagsStore.updateTag(tagId, name);
  }

  async function handleDeleteTag(tagId: number) {
    await tagsStore.deleteTag(tagId);
  }

  // Filter handlers
  function handleToggleFilterTag(tagId: number) {
    if (selectedFilterTags.includes(tagId)) {
      selectedFilterTags = selectedFilterTags.filter((id) => id !== tagId);
    } else {
      selectedFilterTags = [...selectedFilterTags, tagId];
    }
  }

  function handleClearFilters() {
    searchQuery = "";
    selectedFilterTags = [];
  }

  function handleToggleCompleted() {
    tasksStore.toggleShowCompleted();
  }

  function handleSortChange(sort: SortOption) {
    tasksStore.setSortBy(sort);
  }

  function handleLogout() {
    authStore.logout();
  }
</script>

<div class="min-h-screen bg-background">
  <header
    class="fixed top-0 left-0 w-full border-b bg-card pt-[env(safe-area-inset-top)] z-10"
  >
    <div class="container mx-auto px-4 py-2 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Grindboard</h1>
        {#if authStore.username}
          <p class="text-sm text-muted-foreground">
            {authStore.username} · {uncompletedCount}
            {uncompletedCount === 1 ? "task" : "tasks"}
          </p>
        {/if}
      </div>
      <div class="flex items-center gap-2">
        <Button
          size="icon"
          variant="ghost"
          onclick={() => (showTagManager = true)}
          title="Manage Tags"
        >
          <TagIcon class="size-5" />
        </Button>
        <Button size="icon" variant="ghost" onclick={handleToggleTheme}>
          {#if getEffectiveTheme() === "dark"}
            <SunIcon class="size-5" />
          {:else}
            <MoonIcon class="size-5" />
          {/if}
        </Button>
        <Button size="icon" variant="ghost" onclick={handleLogout}>
          <LogOutIcon class="size-5" />
        </Button>
      </div>
    </div>
  </header>

  <ScrollArea
    class="h-screen pt-[calc(4.2rem+env(safe-area-inset-top))] pb-[env(safe-area-inset-bottom)]"
  >
    <div class="container mx-auto px-4 max-w-3xl pt-4 pb-8">
      <Button onclick={handleCreateTask} class="w-full">
        <PlusIcon class="size-4 mr-2" />
        Add Task
      </Button>

      <div class="my-4">
        <FilterBar
          bind:searchQuery
          {selectedFilterTags}
          allTags={tagsStore.tags}
          showCompleted={tasksStore.showCompleted}
          sortBy={tasksStore.sortBy}
          onToggleTag={handleToggleFilterTag}
          onClear={handleClearFilters}
          onToggleCompleted={handleToggleCompleted}
          onSortChange={handleSortChange}
        />
      </div>

      {#if tasksStore.isLoading}
        <div class="text-center py-12 text-muted-foreground">
          Loading tasks...
        </div>
      {:else if filteredTasks().length === 0}
        <div class="text-center py-12 text-muted-foreground">
          {#if searchQuery || selectedFilterTags.length > 0}
            Filters too strong, or you just picky?
          {:else}
            Nothing to see here… yet
          {/if}
        </div>
      {:else}
        <div class="space-y-3" role="list">
          {#each filteredTasks() as task (task.id)}
            <TaskItem
              {task}
              tags={task.tags}
              onToggle={handleToggleTask}
              onEdit={handleEditTask}
              onDelete={handleDeleteTask}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDragEnd={handleDragEnd}
              isDragging={tasksStore.draggedTaskId === task.id}
              isDragOver={tasksStore.dragOverTaskId === task.id}
            />
          {/each}
        </div>
      {/if}

      {#if tasksStore.error}
        <div class="mt-4 p-4 bg-destructive/10 text-destructive rounded-lg">
          {tasksStore.error}
        </div>
      {/if}
    </div>
  </ScrollArea>

  <TaskDialog
    bind:open={showTaskDialog}
    {dialogMode}
    task={editingTask}
    allTags={tagsStore.tags}
    bind:selectedTags={selectedDialogTags}
    onClose={() => (showTaskDialog = false)}
    onSubmit={handleSubmitTask}
    onCreateTag={handleCreateTag}
  />

  <TagManager
    bind:open={showTagManager}
    tags={tagsStore.tags}
    onClose={() => (showTagManager = false)}
    onCreate={handleCreateTagInManager}
    onUpdate={handleUpdateTag}
    onDelete={handleDeleteTag}
  />
</div>

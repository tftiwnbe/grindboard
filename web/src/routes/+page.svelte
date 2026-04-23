<script lang="ts">
  import type { components } from "$lib/api/v1";
  import FilterBar from "$lib/components/FilterBar.svelte";
  import SettingsDialog from "$lib/components/SettingsDialog.svelte";
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
    SettingsIcon,
    SunIcon,
    TagIcon,
  } from "@lucide/svelte/icons";
  import { onMount } from "svelte";

  type Task = components["schemas"]["TaskRead"];
  type Tag = components["schemas"]["TagRead"];

  const STORAGE_KEY = "grindboard:settings";
  function loadSettings() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw) as { addNewTasksToTop?: boolean };
    } catch {}
    return {};
  }

  // UI State
  let themeOverride = $state<Theme | null>(null);
  let currentTheme = $state<Theme>("dark");
  let showTaskDialog = $state(false);
  let showTagManager = $state(false);
  let showSettings = $state(false);
  let dialogMode = $state<"create" | "edit">("create");
  let editingTask = $state<Task | null>(null);
  let selectedDialogTags = $state<Tag[]>([]);
  let isTaskSaving = $state(false);

  // Drag-to-top state
  let dragOverTop = $state(false);

  // Filter State
  let searchQuery = $state("");
  let selectedFilterTags = $state<number[]>([]);

  // Search input element ref for "/" shortcut
  let searchInputEl = $state<HTMLInputElement | null>(null);

  const filteredTasks = $derived(() => {
    let result = tasksStore.getSortedTasks();
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (task) =>
          task.title.toLowerCase().includes(query) ||
          task.description?.toLowerCase().includes(query),
      );
    }
    if (selectedFilterTags.length > 0) {
      result = result.filter((task) =>
        selectedFilterTags.every((tagId) => task.tags.some((tag) => tag.id === tagId)),
      );
    }
    return result;
  });

  onMount(() => {
    themeOverride = initializeTheme();
    currentTheme = getEffectiveTheme();
    const cleanup = setupThemeListener(() => {
      themeOverride = themeOverride;
      currentTheme = getEffectiveTheme();
    });
    Promise.all([tasksStore.fetchTasks(), tagsStore.fetchTags()]);
    return cleanup;
  });

  function handleToggleTheme() {
    themeOverride = toggleTheme();
    currentTheme = getEffectiveTheme();
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
    deadline: string | null,
    keepOpen: boolean,
  ) {
    const tagIds = tags.map((t) => t.id).filter((id): id is number => id !== null);
    isTaskSaving = true;

    if (dialogMode === "create") {
      const settings = loadSettings();
      await tasksStore.createTask(
        { title, description, deadline: deadline ?? undefined },
        tagIds,
        settings.addNewTasksToTop ?? false,
      );
    } else if (editingTask) {
      await tasksStore.updateTask(
        editingTask.id,
        { title, description, deadline: deadline ?? null },
        tagIds,
      );
    }

    isTaskSaving = false;
    if (!keepOpen) showTaskDialog = false;
    await tagsStore.fetchTags();
  }

  async function handleCreateTag(name: string) {
    const newTag = await tagsStore.createTag(name);
    if (newTag && dialogMode === "edit" && editingTask) {
      selectedDialogTags = [...selectedDialogTags, newTag];
    }
  }

  async function handleToggleTask(taskId: number) { await tasksStore.toggleTask(taskId); }
  async function handleDeleteTask(taskId: number) { await tasksStore.deleteTask(taskId); }

  // Drag and drop
  function handleDragStart(taskId: number) { tasksStore.setDraggedTask(taskId); }
  function handleDragOver(taskId: number) {
    dragOverTop = false;
    tasksStore.setDragOverTask(taskId);
  }
  async function handleDragEnd() { await tasksStore.handleDrop(); }

  function handleDragOverTop(e: DragEvent) {
    e.preventDefault();
    dragOverTop = true;
    tasksStore.setDragOverTask(null);
  }
  function handleDragLeaveTop() { dragOverTop = false; }
  async function handleDropTop(e: DragEvent) {
    e.preventDefault();
    dragOverTop = false;
    const id = tasksStore.draggedTaskId;
    if (id !== null) await tasksStore.moveTask(id, null);
  }

  // Tag manager
  async function handleCreateTagInManager(name: string) { await tagsStore.createTag(name); }
  async function handleUpdateTag(tagId: number, name: string) { await tagsStore.updateTag(tagId, name); }
  async function handleDeleteTag(tagId: number) { await tagsStore.deleteTag(tagId); }

  // Filters
  function handleToggleFilterTag(tagId: number) {
    if (selectedFilterTags.includes(tagId)) {
      selectedFilterTags = selectedFilterTags.filter((id) => id !== tagId);
    } else {
      selectedFilterTags = [...selectedFilterTags, tagId];
    }
  }
  function handleClearFilters() { searchQuery = ""; selectedFilterTags = []; }
  function handleToggleCompleted() { tasksStore.toggleShowCompleted(); }
  function handleSortChange(sort: SortOption) { tasksStore.setSortBy(sort); }
  function handleLogout() { authStore.logout(); }

  // Keyboard shortcuts
  function handleKeydown(e: KeyboardEvent) {
    const target = e.target as HTMLElement;
    const inInput = target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable;
    if (inInput) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    if (e.key === "n") { e.preventDefault(); handleCreateTask(); }
    else if (e.key === "/") { e.preventDefault(); searchInputEl?.focus(); }
    else if (e.key === "t") { e.preventDefault(); showTagManager = true; }
    else if (e.key === "s") { e.preventDefault(); showSettings = true; }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="min-h-screen bg-background">
  <header class="fixed top-0 left-0 w-full border-b bg-card pt-[env(safe-area-inset-top)] z-10">
    <div class="container mx-auto px-4 py-2 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold leading-tight">Grindboard</h1>
        {#if authStore.username}
          {@const tasks = filteredTasks()}
          <p class="text-xs text-muted-foreground">
            {authStore.username} · {tasks.length} {tasks.length === 1 ? "task" : "tasks"}
          </p>
        {/if}
      </div>
      <div class="flex items-center gap-1">
        <Button size="icon" variant="ghost" onclick={() => (showTagManager = true)} title="Manage Tags (T)">
          <TagIcon class="size-4" />
        </Button>
        <Button size="icon" variant="ghost" onclick={() => (showSettings = true)} title="Settings (S)">
          <SettingsIcon class="size-4" />
        </Button>
        <Button size="icon" variant="ghost" onclick={handleToggleTheme}>
          {#if currentTheme === "dark"}
            <SunIcon class="size-4" />
          {:else}
            <MoonIcon class="size-4" />
          {/if}
        </Button>
        <Button size="icon" variant="ghost" onclick={handleLogout}>
          <LogOutIcon class="size-4" />
        </Button>
      </div>
    </div>
  </header>

  <ScrollArea class="h-screen pt-[calc(3.8rem+env(safe-area-inset-top))] pb-[env(safe-area-inset-bottom)]">
    <div class="container mx-auto px-3 max-w-2xl pt-3 pb-8">
      <Button
        onclick={handleCreateTask}
        class="w-full"
        disabled={isTaskSaving}
      >
        <PlusIcon class="size-4 mr-2" />
        {isTaskSaving ? "Saving…" : "Add Task"}
      </Button>

      <div class="my-3">
        <FilterBar
          bind:searchQuery
          bind:searchInputEl
          {selectedFilterTags}
          allTags={tagsStore.tags}
          allTasks={tasksStore.tasks}
          showCompleted={tasksStore.showCompleted}
          sortBy={tasksStore.sortBy}
          onToggleTag={handleToggleFilterTag}
          onClear={handleClearFilters}
          onToggleCompleted={handleToggleCompleted}
          onSortChange={handleSortChange}
        />
      </div>

      {#if tasksStore.isLoading}
        <div class="text-center py-12 text-muted-foreground text-sm">Loading tasks…</div>
      {:else}
        {@const visibleTasks = filteredTasks()}
        {#if visibleTasks.length === 0}
          <div class="text-center py-12 text-muted-foreground text-sm">
            {#if searchQuery || selectedFilterTags.length > 0}
              Filters too strong, or you just picky?
            {:else}
              Nothing to see here… yet
            {/if}
          </div>
        {:else}
          <!-- Drop zone for moving to top position -->
          {#if tasksStore.draggedTaskId !== null}
            <div
              role="none"
              class="h-2 mb-1 rounded transition-colors {dragOverTop ? 'bg-primary/30' : ''}"
              ondragover={handleDragOverTop}
              ondragleave={handleDragLeaveTop}
              ondrop={handleDropTop}
            ></div>
          {/if}

          <div class="space-y-1.5" role="list">
            {#each visibleTasks as task (task.id)}
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
      {/if}

      {#if tasksStore.error}
        <div class="mt-3 p-3 bg-destructive/10 text-destructive rounded text-sm">
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
    isLoading={isTaskSaving}
  />

  <TagManager
    bind:open={showTagManager}
    tags={tagsStore.tags}
    onClose={() => (showTagManager = false)}
    onCreate={handleCreateTagInManager}
    onUpdate={handleUpdateTag}
    onDelete={handleDeleteTag}
  />

  <SettingsDialog
    bind:open={showSettings}
    onClose={() => (showSettings = false)}
  />
</div>

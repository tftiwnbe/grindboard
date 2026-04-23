import type { components } from "$lib/api/v1";
import client from "$lib/api/client";

type Task = components["schemas"]["TaskRead"];
type TaskCreate = components["schemas"]["TaskCreate"];
type TaskUpdate = components["schemas"]["TaskUpdate"];

export type SortOption = "manual" | "alpha-asc" | "alpha-desc";

interface TasksState {
  tasks: Task[];
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  draggedTaskId: number | null;
  dragOverTaskId: number | null;
  showCompleted: boolean;
  sortBy: SortOption;
}

class TasksStore {
  private state = $state<TasksState>({
    tasks: [],
    isLoading: false,
    isSaving: false,
    error: null,
    draggedTaskId: null,
    dragOverTaskId: null,
    showCompleted: false,
    sortBy: "manual",
  });

  get tasks() { return this.state.tasks; }
  get isLoading() { return this.state.isLoading; }
  get isSaving() { return this.state.isSaving; }
  get error() { return this.state.error; }
  get draggedTaskId() { return this.state.draggedTaskId; }
  get dragOverTaskId() { return this.state.dragOverTaskId; }
  get showCompleted() { return this.state.showCompleted; }
  get sortBy() { return this.state.sortBy; }

  async fetchTasks() {
    this.state.isLoading = true;
    this.state.error = null;
    try {
      const { data, error } = await client.GET("/api/v1/tasks/");
      if (error || !data) { this.state.error = "Failed to load tasks"; return; }
      this.state.tasks = data;
    } catch (err) {
      this.state.error = "Failed to load tasks";
      console.error("Fetch tasks error:", err);
    } finally {
      this.state.isLoading = false;
    }
  }

  async createTask(
    taskData: TaskCreate,
    tagIds: number[] = [],
    addToTop = false,
  ): Promise<Task | null> {
    this.state.isSaving = true;
    this.state.error = null;
    try {
      const { data, error } = await client.POST("/api/v1/tasks/", { body: taskData });
      if (error || !data) { this.state.error = "Failed to create task"; return null; }

      if (tagIds.length > 0) {
        await Promise.all(
          tagIds.map((tagId) =>
            client.POST("/api/v1/tasks/{task_id}/tags/{tag_id}", {
              params: { path: { task_id: data.id, tag_id: tagId } },
            }),
          ),
        );
      }

      if (addToTop) {
        await client.POST("/api/v1/tasks/{task_id}/move", {
          params: { path: { task_id: data.id }, query: { after_id: null } },
        });
      }

      await this.fetchTasks();
      return data;
    } catch (err) {
      this.state.error = "Failed to create task";
      console.error("Create task error:", err);
      return null;
    } finally {
      this.state.isSaving = false;
    }
  }

  async updateTask(
    taskId: number,
    updates: TaskUpdate,
    tagIds: number[] = [],
  ): Promise<boolean> {
    this.state.isSaving = true;
    this.state.error = null;
    try {
      const { error } = await client.PUT("/api/v1/tasks/{task_id}", {
        params: { path: { task_id: taskId } },
        body: updates,
      });
      if (error) { this.state.error = "Failed to update task"; return false; }

      const currentTask = this.state.tasks.find((t) => t.id === taskId);
      const currentTagIds = currentTask?.tags.map((t) => t.id) ?? [];

      const tagsToRemove = currentTagIds.filter((id) => !tagIds.includes(id));
      await Promise.all(
        tagsToRemove.map((tagId) =>
          client.DELETE("/api/v1/tasks/{task_id}/tags/{tag_id}", {
            params: { path: { task_id: taskId, tag_id: tagId } },
          }),
        ),
      );

      const tagsToAdd = tagIds.filter((id) => !currentTagIds.includes(id));
      await Promise.all(
        tagsToAdd.map((tagId) =>
          client.POST("/api/v1/tasks/{task_id}/tags/{tag_id}", {
            params: { path: { task_id: taskId, tag_id: tagId } },
          }),
        ),
      );

      await this.fetchTasks();
      return true;
    } catch (err) {
      this.state.error = "Failed to update task";
      console.error("Update task error:", err);
      return false;
    } finally {
      this.state.isSaving = false;
    }
  }

  async toggleTask(taskId: number) {
    this.state.error = null;
    const taskIndex = this.state.tasks.findIndex((t) => t.id === taskId);
    if (taskIndex !== -1) {
      this.state.tasks[taskIndex] = {
        ...this.state.tasks[taskIndex],
        completed: !this.state.tasks[taskIndex].completed,
      };
    }
    try {
      const { error } = await client.PATCH("/api/v1/tasks/{task_id}/complete", {
        params: { path: { task_id: taskId } },
      });
      if (error) {
        if (taskIndex !== -1) {
          this.state.tasks[taskIndex] = {
            ...this.state.tasks[taskIndex],
            completed: !this.state.tasks[taskIndex].completed,
          };
        }
        this.state.error = "Failed to toggle task";
      } else {
        await this.fetchTasks();
      }
    } catch (err) {
      if (taskIndex !== -1) {
        this.state.tasks[taskIndex] = {
          ...this.state.tasks[taskIndex],
          completed: !this.state.tasks[taskIndex].completed,
        };
      }
      this.state.error = "Failed to toggle task";
      console.error("Toggle task error:", err);
    }
  }

  async deleteTask(taskId: number): Promise<boolean> {
    this.state.error = null;
    try {
      const { error } = await client.DELETE("/api/v1/tasks/{task_id}", {
        params: { path: { task_id: taskId } },
      });
      if (error) { this.state.error = "Failed to delete task"; return false; }
      await this.fetchTasks();
      return true;
    } catch (err) {
      this.state.error = "Failed to delete task";
      console.error("Delete task error:", err);
      return false;
    }
  }

  async moveTask(taskId: number, afterTaskId: number | null) {
    this.state.error = null;
    try {
      const { error } = await client.POST("/api/v1/tasks/{task_id}/move", {
        params: {
          path: { task_id: taskId },
          query: { after_id: afterTaskId },
        },
      });
      if (error) { this.state.error = "Failed to move task"; return; }
      await this.fetchTasks();
    } catch (err) {
      this.state.error = "Failed to move task";
      console.error("Move task error:", err);
    }
  }

  setDraggedTask(taskId: number | null) { this.state.draggedTaskId = taskId; }
  setDragOverTask(taskId: number | null) { this.state.dragOverTaskId = taskId; }

  async handleDrop() {
    if (this.state.draggedTaskId && this.state.dragOverTaskId) {
      await this.moveTask(this.state.draggedTaskId, this.state.dragOverTaskId);
    }
    this.state.draggedTaskId = null;
    this.state.dragOverTaskId = null;
  }

  clearError() { this.state.error = null; }
  toggleShowCompleted() { this.state.showCompleted = !this.state.showCompleted; }
  setSortBy(sortBy: SortOption) { this.state.sortBy = sortBy; }

  getSortedTasks(): Task[] {
    let result = [...this.state.tasks];
    if (this.state.showCompleted) {
      result = result.filter((task) => task.completed);
    } else {
      result = result.filter((task) => !task.completed);
    }
    switch (this.state.sortBy) {
      case "alpha-asc":
        result.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case "alpha-desc":
        result.sort((a, b) => b.title.localeCompare(a.title));
        break;
      case "manual":
      default:
        break;
    }
    return result;
  }
}

export const tasksStore = new TasksStore();

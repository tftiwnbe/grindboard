import type { components } from "$lib/api/v1";
import client from "$lib/api/client";

type Task = components["schemas"]["TaskRead"];
type TaskCreate = components["schemas"]["TaskCreate"];
type TaskUpdate = components["schemas"]["TaskUpdate"];

export type SortOption =
  | "manual"
  | "date-desc"
  | "date-asc"
  | "alpha-asc"
  | "alpha-desc";

interface TasksState {
  tasks: Task[];
  isLoading: boolean;
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
    error: null,
    draggedTaskId: null,
    dragOverTaskId: null,
    showCompleted: false,
    sortBy: "manual",
  });

  // Getters
  get tasks() {
    return this.state.tasks;
  }

  get isLoading() {
    return this.state.isLoading;
  }

  get error() {
    return this.state.error;
  }

  get draggedTaskId() {
    return this.state.draggedTaskId;
  }

  get dragOverTaskId() {
    return this.state.dragOverTaskId;
  }

  get showCompleted() {
    return this.state.showCompleted;
  }

  get sortBy() {
    return this.state.sortBy;
  }

  // Fetch all tasks (tags are included in the response)
  async fetchTasks() {
    this.state.isLoading = true;
    this.state.error = null;

    try {
      const { data, error } = await client.GET("/api/v1/tasks/");

      if (error || !data) {
        this.state.error = "Failed to load tasks";
        return;
      }

      this.state.tasks = data;
    } catch (err) {
      this.state.error = "Failed to load tasks";
      console.error("Fetch tasks error:", err);
    } finally {
      this.state.isLoading = false;
    }
  }

  // Create a new task with tags
  async createTask(
    taskData: TaskCreate,
    tagIds: number[] = [],
  ): Promise<boolean> {
    this.state.error = null;

    try {
      const { data, error } = await client.POST("/api/v1/tasks/", {
        body: taskData,
      });

      if (error || !data) {
        this.state.error = "Failed to create task";
        return false;
      }

      // Add tags if any
      if (tagIds.length > 0) {
        await Promise.all(
          tagIds.map((tagId) =>
            client.POST("/api/v1/tags/tasks/{task_id}/tags/{tag_id}", {
              params: { path: { task_id: data.id, tag_id: tagId } },
            }),
          ),
        );
      }

      // Refresh tasks to get updated tag data
      await this.fetchTasks();
      return true;
    } catch (err) {
      this.state.error = "Failed to create task";
      console.error("Create task error:", err);
      return false;
    }
  }

  // Update an existing task with tags
  async updateTask(
    taskId: number,
    updates: TaskUpdate,
    tagIds: number[] = [],
  ): Promise<boolean> {
    this.state.error = null;

    try {
      // Update task details
      const { error } = await client.PUT("/api/v1/tasks/{task_id}", {
        params: { path: { task_id: taskId } },
        body: updates,
      });

      if (error) {
        this.state.error = "Failed to update task";
        return false;
      }

      // Find current task to get its tags
      const currentTask = this.state.tasks.find((t) => t.id === taskId);
      const currentTagIds = currentTask?.tags.map((t) => t.id) || [];

      // Remove tags that are no longer selected
      const tagsToRemove = currentTagIds.filter((id) => !tagIds.includes(id));
      await Promise.all(
        tagsToRemove.map((tagId) =>
          client.DELETE("/api/v1/tags/tasks/{task_id}/tags/{tag_id}", {
            params: { path: { task_id: taskId, tag_id: tagId } },
          }),
        ),
      );

      // Add new tags
      const tagsToAdd = tagIds.filter((id) => !currentTagIds.includes(id));
      await Promise.all(
        tagsToAdd.map((tagId) =>
          client.POST("/api/v1/tags/tasks/{task_id}/tags/{tag_id}", {
            params: { path: { task_id: taskId, tag_id: tagId } },
          }),
        ),
      );

      // Refresh tasks to get updated tag data
      await this.fetchTasks();
      return true;
    } catch (err) {
      this.state.error = "Failed to update task";
      console.error("Update task error:", err);
      return false;
    }
  }

  // Toggle task completion status
  async toggleTask(taskId: number) {
    this.state.error = null;

    // Optimistically update the UI
    const taskIndex = this.state.tasks.findIndex((t) => t.id === taskId);
    if (taskIndex !== -1) {
      this.state.tasks[taskIndex] = {
        ...this.state.tasks[taskIndex],
        completed: !this.state.tasks[taskIndex].completed,
      };
    }

    try {
      const { error } = await client.POST("/api/v1/tasks/{task_id}/complete", {
        params: { path: { task_id: taskId } },
      });

      if (error) {
        // Revert on error
        if (taskIndex !== -1) {
          this.state.tasks[taskIndex] = {
            ...this.state.tasks[taskIndex],
            completed: !this.state.tasks[taskIndex].completed,
          };
        }
        this.state.error = "Failed to toggle task";
        return;
      }
    } catch (err) {
      // Revert on error
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

  // Delete a task
  async deleteTask(taskId: number): Promise<boolean> {
    this.state.error = null;

    try {
      const { error } = await client.DELETE("/api/v1/tasks/{task_id}", {
        params: { path: { task_id: taskId } },
      });

      if (error) {
        this.state.error = "Failed to delete task";
        return false;
      }

      await this.fetchTasks();
      return true;
    } catch (err) {
      this.state.error = "Failed to delete task";
      console.error("Delete task error:", err);
      return false;
    }
  }

  // Move a task to a new position
  async moveTask(taskId: number, afterTaskId: number | null) {
    this.state.error = null;

    try {
      const { error } = await client.POST("/api/v1/tasks/{task_id}/move", {
        params: {
          path: { task_id: taskId },
          query: { after_id: afterTaskId },
        },
      });

      if (error) {
        this.state.error = "Failed to move task";
        return;
      }

      await this.fetchTasks();
    } catch (err) {
      this.state.error = "Failed to move task";
      console.error("Move task error:", err);
    }
  }

  // Drag and drop handlers
  setDraggedTask(taskId: number | null) {
    this.state.draggedTaskId = taskId;
  }

  setDragOverTask(taskId: number | null) {
    this.state.dragOverTaskId = taskId;
  }

  async handleDrop() {
    if (this.state.draggedTaskId && this.state.dragOverTaskId) {
      await this.moveTask(this.state.draggedTaskId, this.state.dragOverTaskId);
    }
    this.state.draggedTaskId = null;
    this.state.dragOverTaskId = null;
  }

  // Clear error
  clearError() {
    this.state.error = null;
  }

  // Toggle showing completed tasks
  toggleShowCompleted() {
    this.state.showCompleted = !this.state.showCompleted;
  }

  // Set sort option
  setSortBy(sortBy: SortOption) {
    this.state.sortBy = sortBy;
  }

  // Get sorted and filtered tasks
  getSortedTasks(): Task[] {
    let result = [...this.state.tasks];

    // Filter by completion status
    if (this.state.showCompleted) {
      // Show only completed tasks
      result = result.filter((task) => task.completed);
    } else {
      // Show only uncompleted tasks
      result = result.filter((task) => !task.completed);
    }

    // Sort tasks
    switch (this.state.sortBy) {
      case "alpha-asc":
        result.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case "alpha-desc":
        result.sort((a, b) => b.title.localeCompare(a.title));
        break;
      case "manual":
      default:
        // Keep original order (already sorted by position from API)
        break;
    }

    return result;
  }
}

// Export singleton instance
export const tasksStore = new TasksStore();

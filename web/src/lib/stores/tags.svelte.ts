import type { components } from "$lib/api/v1";
import client from "$lib/api/client";
import { tasksStore } from "./tasks.svelte";

type Tag = components["schemas"]["TagRead"];

interface TagsState {
  tags: Tag[];
  isLoading: boolean;
  error: string | null;
}

class TagsStore {
  private state = $state<TagsState>({
    tags: [],
    isLoading: false,
    error: null,
  });

  // Getters
  get tags() {
    return this.state.tags;
  }

  get isLoading() {
    return this.state.isLoading;
  }

  get error() {
    return this.state.error;
  }

  // Fetch all tags
  async fetchTags() {
    this.state.isLoading = true;
    this.state.error = null;

    try {
      const { data, error } = await client.GET("/api/v1/tags/");

      if (error || !data) {
        this.state.error = "Failed to load tags";
        return;
      }

      this.state.tags = data;
    } catch (err) {
      this.state.error = "Failed to load tags";
      console.error("Fetch tags error:", err);
    } finally {
      this.state.isLoading = false;
    }
  }

  // Create a new tag
  async createTag(name: string): Promise<Tag | null> {
    this.state.error = null;

    try {
      const { data, error } = await client.POST("/api/v1/tags/", {
        params: { query: { name } },
      });

      if (error || !data) {
        this.state.error = "Failed to create tag";
        return null;
      }

      this.state.tags = [...this.state.tags, data];
      return data;
    } catch (err) {
      this.state.error = "Failed to create tag";
      console.error("Create tag error:", err);
      return null;
    }
  }

  // Update tag name
  async updateTag(tagId: number, name: string): Promise<boolean> {
    this.state.error = null;

    try {
      const { error } = await client.PUT("/api/v1/tags/{tag_id}", {
        params: { path: { tag_id: tagId }, query: { name } },
      });

      if (error) {
        this.state.error = "Failed to update tag";
        return false;
      }

      this.state.tags = this.state.tags.map((tag) =>
        tag.id === tagId ? { ...tag, name } : tag,
      );
      tasksStore.renameTag(tagId, name);
      return true;
    } catch (err) {
      this.state.error = "Failed to update tag";
      console.error("Update tag error:", err);
      return false;
    }
  }

  // Delete a tag
  async deleteTag(tagId: number): Promise<boolean> {
    this.state.error = null;

    try {
      const { error } = await client.DELETE("/api/v1/tags/{tag_id}", {
        params: { path: { tag_id: tagId } },
      });

      if (error) {
        this.state.error = "Failed to delete tag";
        return false;
      }

      this.state.tags = this.state.tags.filter((tag) => tag.id !== tagId);
      tasksStore.removeTag(tagId);
      return true;
    } catch (err) {
      this.state.error = "Failed to delete tag";
      console.error("Delete tag error:", err);
      return false;
    }
  }

  // Clear error
  clearError() {
    this.state.error = null;
  }
}

// Export singleton instance
export const tagsStore = new TagsStore();

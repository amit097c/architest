import { SavedTest, Collection, IntegrationSettings, JiraConfig, GitHubConfig } from './types';
import { ApiService } from './api-service';

export const TestStorageService = {
  saveTest: async (test: SavedTest): Promise<SavedTest> => {
    try {
      return await ApiService.saveTest(test);
    } catch (error) {
      console.error('Error saving test:', error);
      throw error;
    }
  },
  
  getAllTests: async (): Promise<SavedTest[]> => {
    try {
      return await ApiService.getAllTests();
    } catch (error) {
      console.error('Error retrieving tests:', error);
      return [];
    }
  },
  
  getTestById: async (id: string): Promise<SavedTest | undefined> => {
    try {
      return await ApiService.getTestById(id);
    } catch (error) {
      console.error(`Error retrieving test with ID ${id}:`, error);
      return undefined;
    }
  },
  
  deleteTest: async (id: string): Promise<void> => {
    try {
      await ApiService.deleteTest(id);
    } catch (error) {
      console.error(`Error deleting test with ID ${id}:`, error);
      throw error;
    }
  },
  
  updateTest: async (id: string, updates: Partial<SavedTest>): Promise<void> => {
    try {
      await ApiService.updateTest(id, updates);
    } catch (error) {
      console.error(`Error updating test with ID ${id}:`, error);
      throw error;
    }
  },
  
  addTagToTest: async (id: string, tag: string): Promise<void> => {
    try {
      await ApiService.addTagToTest(id, tag);
    } catch (error) {
      console.error(`Error adding tag to test with ID ${id}:`, error);
      throw error;
    }
  },
  
  removeTagFromTest: async (id: string, tag: string): Promise<void> => {
    try {
      await ApiService.removeTagFromTest(id, tag);
    } catch (error) {
      console.error(`Error removing tag from test with ID ${id}:`, error);
      throw error;
    }
  },

  // Collection management methods
  createCollection: async (collection: Collection): Promise<void> => {
    try {
      await ApiService.createCollection(collection);
    } catch (error) {
      console.error('Error creating collection:', error);
      throw error;
    }
  },

  getAllCollections: async (): Promise<Collection[]> => {
    try {
      return await ApiService.getAllCollections();
    } catch (error) {
      console.error('Error retrieving collections:', error);
      return [];
    }
  },

  getCollectionById: async (id: string): Promise<Collection | undefined> => {
    try {
      return await ApiService.getCollectionById(id);
    } catch (error) {
      console.error(`Error retrieving collection with ID ${id}:`, error);
      return undefined;
    }
  },

  updateCollection: async (id: string, updates: Partial<Collection>): Promise<void> => {
    try {
      await ApiService.updateCollection(id, updates);
    } catch (error) {
      console.error(`Error updating collection with ID ${id}:`, error);
      throw error;
    }
  },

  deleteCollection: async (id: string): Promise<void> => {
    try {
      await ApiService.deleteCollection(id);
    } catch (error) {
      console.error(`Error deleting collection with ID ${id}:`, error);
      throw error;
    }
  },

  addTestToCollection: async (testId: string, collectionId: string): Promise<void> => {
    try {
      await ApiService.addTestToCollection(testId, collectionId);
    } catch (error) {
      console.error(`Error adding test ${testId} to collection ${collectionId}:`, error);
      throw error;
    }
  },

  removeTestFromCollection: async (testId: string): Promise<void> => {
    try {
      await ApiService.removeTestFromCollection(testId);
    } catch (error) {
      console.error(`Error removing test ${testId} from collection:`, error);
      throw error;
    }
  },

  getTestsByCollectionId: async (collectionId: string): Promise<SavedTest[]> => {
    try {
      return await ApiService.getTestsByCollectionId(collectionId);
    } catch (error) {
      console.error(`Error getting tests by collection ID ${collectionId}:`, error);
      return [];
    }
  },

  // Integration settings methods
  getIntegrationSettings: async (): Promise<IntegrationSettings> => {
    try {
      return await ApiService.getIntegrationSettings();
    } catch (error) {
      console.error('Error retrieving integration settings:', error);
      return {};
    }
  },

  saveIntegrationSettings: async (settings: IntegrationSettings): Promise<void> => {
    try {
      await ApiService.saveIntegrationSettings(settings);
    } catch (error) {
      console.error('Error saving integration settings:', error);
      throw error;
    }
  },

  saveJiraConfig: async (config: JiraConfig): Promise<void> => {
    try {
      await ApiService.saveJiraConfig(config);
    } catch (error) {
      console.error('Error saving Jira config:', error);
      throw error;
    }
  },

  saveGitHubConfig: async (config: GitHubConfig): Promise<void> => {
    try {
      await ApiService.saveGitHubConfig(config);
    } catch (error) {
      console.error('Error saving GitHub config:', error);
      throw error;
    }
  },

  clearJiraConfig: async (): Promise<void> => {
    try {
      await ApiService.clearJiraConfig();
    } catch (error) {
      console.error('Error clearing Jira config:', error);
      throw error;
    }
  },

  clearGitHubConfig: async (): Promise<void> => {
    try {
      await ApiService.clearGitHubConfig();
    } catch (error) {
      console.error('Error clearing GitHub config:', error);
      throw error;
    }
  },

  // Test runner methods
  async runTest(test: SavedTest): Promise<{id: string, status: string}> {
    return ApiService.runTest(test);
  },
  
  async getTestStatus(testId: string): Promise<{
    id: string;
    status: string;
    output: string[];
    execution_time: number;
  }> {
    return ApiService.getTestStatus(testId);
  },
  
  async cancelTest(testId: string): Promise<boolean> {
    return ApiService.cancelTest(testId);
  }
}; 
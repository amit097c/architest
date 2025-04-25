import { SavedTest, Collection, IntegrationSettings } from './types';

const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

export const ApiService = {
  // Tests
  async saveTest(test: SavedTest): Promise<SavedTest> {
    try {
      const response = await fetch(`${API_URL}/api/tests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(test),
      });
      
      if (!response.ok) {
        throw new Error(`Error saving test: ${response.statusText}`);
      }
      
      const savedTest = await response.json();
      return {
        ...savedTest,
        createdAt: new Date(savedTest.createdAt)
      };
    } catch (error) {
      console.error('Error saving test:', error);
      throw error;
    }
  },
  
  async getAllTests(): Promise<SavedTest[]> {
    try {
      const response = await fetch(`${API_URL}/api/tests`);
      
      if (!response.ok) {
        throw new Error(`Error retrieving tests: ${response.statusText}`);
      }
      
      const tests = await response.json();
      
      // Convert string dates to Date objects
      return tests.map((test: any) => ({
        ...test,
        createdAt: new Date(test.createdAt)
      }));
    } catch (error) {
      console.error('Error retrieving tests:', error);
      throw error;
    }
  },
  
  async getTestById(id: string): Promise<SavedTest | undefined> {
    try {
      const response = await fetch(`${API_URL}/api/tests/${id}`);
      
      if (response.status === 404) {
        return undefined;
      }
      
      if (!response.ok) {
        throw new Error(`Error retrieving test: ${response.statusText}`);
      }
      
      const test = await response.json();
      return {
        ...test,
        createdAt: new Date(test.createdAt)
      };
    } catch (error) {
      console.error(`Error retrieving test with ID ${id}:`, error);
      throw error;
    }
  },
  
  async deleteTest(id: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/tests/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Error deleting test: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error deleting test with ID ${id}:`, error);
      throw error;
    }
  },
  
  async updateTest(id: string, updates: Partial<SavedTest>): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/tests/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      
      if (!response.ok) {
        throw new Error(`Error updating test: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error updating test with ID ${id}:`, error);
      throw error;
    }
  },
  
  async addTagToTest(id: string, tag: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/tests/${id}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tag }),
      });
      
      if (!response.ok) {
        throw new Error(`Error adding tag: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error adding tag to test with ID ${id}:`, error);
      throw error;
    }
  },
  
  async removeTagFromTest(id: string, tag: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/tests/${id}/tags/${encodeURIComponent(tag)}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Error removing tag: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error removing tag from test with ID ${id}:`, error);
      throw error;
    }
  },
  
  // Collections
  async createCollection(collection: Collection): Promise<string> {
    try {
      const response = await fetch(`${API_URL}/api/collections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(collection),
      });
      
      if (!response.ok) {
        throw new Error(`Error creating collection: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data.id;
    } catch (error) {
      console.error('Error creating collection:', error);
      throw error;
    }
  },
  
  async getAllCollections(): Promise<Collection[]> {
    try {
      const response = await fetch(`${API_URL}/api/collections`);
      
      if (!response.ok) {
        throw new Error(`Error retrieving collections: ${response.statusText}`);
      }
      
      const collections = await response.json();
      
      // Convert string dates to Date objects
      return collections.map((collection: any) => ({
        ...collection,
        createdAt: new Date(collection.createdAt)
      }));
    } catch (error) {
      console.error('Error retrieving collections:', error);
      throw error;
    }
  },
  
  async getCollectionById(id: string): Promise<Collection | undefined> {
    try {
      const response = await fetch(`${API_URL}/api/collections/${id}`);
      
      if (response.status === 404) {
        return undefined;
      }
      
      if (!response.ok) {
        throw new Error(`Error retrieving collection: ${response.statusText}`);
      }
      
      const collection = await response.json();
      return {
        ...collection,
        createdAt: new Date(collection.createdAt)
      };
    } catch (error) {
      console.error(`Error retrieving collection with ID ${id}:`, error);
      throw error;
    }
  },
  
  async updateCollection(id: string, updates: Partial<Collection>): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/collections/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      
      if (!response.ok) {
        throw new Error(`Error updating collection: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error updating collection with ID ${id}:`, error);
      throw error;
    }
  },
  
  async deleteCollection(id: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/collections/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Error deleting collection: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error deleting collection with ID ${id}:`, error);
      throw error;
    }
  },
  
  async getTestsByCollectionId(collectionId: string): Promise<SavedTest[]> {
    try {
      const response = await fetch(`${API_URL}/api/collections/${collectionId}/tests`);
      
      if (!response.ok) {
        throw new Error(`Error retrieving tests for collection: ${response.statusText}`);
      }
      
      const tests = await response.json();
      
      // Convert string dates to Date objects
      return tests.map((test: any) => ({
        ...test,
        createdAt: new Date(test.createdAt)
      }));
    } catch (error) {
      console.error(`Error retrieving tests for collection with ID ${collectionId}:`, error);
      throw error;
    }
  },
  
  async addTestToCollection(testId: string, collectionId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/tests/${testId}/collection/${collectionId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`Error adding test to collection: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error adding test ${testId} to collection ${collectionId}:`, error);
      throw error;
    }
  },
  
  async removeTestFromCollection(testId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/tests/${testId}/collection`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Error removing test from collection: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error removing test ${testId} from collection:`, error);
      throw error;
    }
  },
  
  // Integration settings
  async getIntegrationSettings(): Promise<IntegrationSettings> {
    try {
      const response = await fetch(`${API_URL}/api/integration-settings`);
      
      if (!response.ok) {
        throw new Error(`Error retrieving integration settings: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error retrieving integration settings:', error);
      throw error;
    }
  },
  
  async saveIntegrationSettings(settings: IntegrationSettings): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/integration-settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });
      
      if (!response.ok) {
        throw new Error(`Error saving integration settings: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error saving integration settings:', error);
      throw error;
    }
  },
  
  async saveJiraConfig(config: IntegrationSettings['jira']): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/integration-settings/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        throw new Error(`Error saving Jira config: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error saving Jira config:', error);
      throw error;
    }
  },
  
  async saveGitHubConfig(config: IntegrationSettings['github']): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/integration-settings/github`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        throw new Error(`Error saving GitHub config: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error saving GitHub config:', error);
      throw error;
    }
  },
  
  async clearJiraConfig(): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/integration-settings/jira`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Error clearing Jira config: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error clearing Jira config:', error);
      throw error;
    }
  },
  
  async clearGitHubConfig(): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/integration-settings/github`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Error clearing GitHub config: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error clearing GitHub config:', error);
      throw error;
    }
  },
  
  async runTest(test: SavedTest): Promise<{id: string, status: string}> {
    try {
      const response = await fetch(`${API_URL}/api/run-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: test.id,
          name: test.name,
          framework: test.framework,
          language: test.language,
          test_script: test.testScript,
          url: typeof test.url === 'string' ? test.url : test.url[0]
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Error running test: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error running test:', error);
      throw error;
    }
  },
  
  async getTestStatus(testId: string): Promise<{
    id: string;
    status: string;
    output: string[];
    execution_time: number;
  }> {
    try {
      const response = await fetch(`${API_URL}/api/test-status/${testId}`);
      
      if (!response.ok) {
        throw new Error(`Error getting test status: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error getting test status for ID ${testId}:`, error);
      throw error;
    }
  },
  
  async cancelTest(testId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/cancel-test/${testId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Error cancelling test: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error cancelling test with ID ${testId}:`, error);
      throw error;
    }
  }
}; 
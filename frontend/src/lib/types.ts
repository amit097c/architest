export interface SavedTest {
  id?: string;
  createdAt: Date;
  name: string;
  url: string | string[];
  testSteps: string;
  framework: "playwright" | "cypress" | "selenium";
  language: "python" | "javascript" | "java";
  testScript: string;
  status: "passed" | "failed" | "unknown";
  isApiTest?: boolean;
  apiDetails?: {
    endpoint: string;
    method: string;
    payload: string;
  };
  tags?: string[];
  collectionId?: string;
  lastRun?: Date;
  code?: string;
}

export interface Collection {
  id?: string;
  name: string;
  description?: string;
  createdAt: Date;
  color?: string;
}

export type TestStatus = "idle" | "extracting-and-processing-html" | "generating" | "running" | "passed" | "failed" | "refining";
export type Framework = "playwright" | "cypress" | "selenium";
export type Language = "python" | "javascript" | "java";

export interface TestErrors {
  message: string;
}

export interface TestResult {
  status: "passed" | "failed";
  message?: string;
  errorDetails?: string;
  iterations?: number;
}

export interface StatusEvent {
  id: string;
  timestamp: Date;
  type: "info" | "success" | "error" | "warning";
  message: string;
  details?: string;
}

export interface JiraConfig {
  url: string;
  apiToken: string;
  email: string;
  project: string;
}

export interface GitHubConfig {
  token: string;
  owner: string;
  repo: string;
}

export interface IntegrationSettings {
  jira?: JiraConfig;
  github?: GitHubConfig;
} 
import React, { createContext, useState, useContext, useRef, useEffect, ReactNode } from 'react';
import axios from 'axios';
import { 
  TestStatus, 
  Framework, 
  Language, 
  TestErrors, 
  TestResult, 
  StatusEvent 
} from '@/lib/types';

interface ArchiTestContextProps {
  // URL and test inputs
  url: string;
  setUrl: React.Dispatch<React.SetStateAction<string>>;
  testSteps: string;
  setTestSteps: React.Dispatch<React.SetStateAction<string>>;
  maxRetries: number;
  setMaxRetries: React.Dispatch<React.SetStateAction<number>>;
  framework: Framework;
  setFramework: React.Dispatch<React.SetStateAction<Framework>>;
  language: Language;
  setLanguage: React.Dispatch<React.SetStateAction<Language>>;
  
  // Multi-page settings
  isMultiPage: boolean;
  setIsMultiPage: React.Dispatch<React.SetStateAction<boolean>>;
  multiPageUrls: string[];
  setMultiPageUrls: React.Dispatch<React.SetStateAction<string[]>>;
  includeApi: boolean;
  setIncludeApi: React.Dispatch<React.SetStateAction<boolean>>;
  
  // Test status
  status: TestStatus;
  generateTestScript: () => Promise<void>;
  testScript: string;
  results: TestResult | null;
  statusEvents: StatusEvent[];
  iterations: number;
  duration: number;
  statusTestErrors: TestErrors | null;
  
  // Jira settings
  useJira: boolean;
  setUseJira: React.Dispatch<React.SetStateAction<boolean>>;
  jiraTicketId: string;
  setJiraTicketId: React.Dispatch<React.SetStateAction<string>>;
  jiraEmail: string;
  setJiraEmail: React.Dispatch<React.SetStateAction<string>>;
  jiraToken: string;
  setJiraToken: React.Dispatch<React.SetStateAction<string>>;
  jiraDomain: string;
  setJiraDomain: React.Dispatch<React.SetStateAction<string>>;
  
  // API Test settings
  isApiTest: boolean;
  setIsApiTest: React.Dispatch<React.SetStateAction<boolean>>;
  apiEndpoint: string;
  setApiEndpoint: React.Dispatch<React.SetStateAction<string>>;
  apiMethod: string;
  setApiMethod: React.Dispatch<React.SetStateAction<string>>;
  apiPayload: string;
  setApiPayload: React.Dispatch<React.SetStateAction<string>>;
  
  // Actions
  addStatusEvent: (
    type: "info" | "success" | "error" | "warning",
    message: string,
    details?: string
  ) => void;
  resetTest: () => void;
  cancelGeneration: () => Promise<void>;
  eventSource: EventSource | null;
}

const ArchiTestContext = createContext<ArchiTestContextProps | undefined>(undefined);

export const ArchiTestProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  // URL and test inputs
  const [url, setUrl] = useState<string>("");
  const [testSteps, setTestSteps] = useState<string>("");
  const [maxRetries, setMaxRetries] = useState<number>(10);
  const [framework, setFramework] = useState<Framework>("playwright");
  const [language, setLanguage] = useState<Language>("python");
  
  // Multi-page settings
  const [isMultiPage, setIsMultiPage] = useState<boolean>(false);
  const [multiPageUrls, setMultiPageUrls] = useState<string[]>([]);
  const [includeApi, setIncludeApi] = useState<boolean>(false);
  
  // Test status
  const [testScript, setTestScript] = useState<string>("");
  const [status, setStatus] = useState<TestStatus>("idle");
  const [results, setResults] = useState<TestResult | null>(null);
  const [statusTestErrors, setStatusTestErrors] = useState<TestErrors | null>(null);
  const [iterations, setIterations] = useState<number>(0);
  
  // Jira settings
  const [useJira, setUseJira] = useState(false);
  const [jiraTicketId, setJiraTicketId] = useState("");
  const [jiraEmail, setJiraEmail] = useState("");
  const [jiraToken, setJiraToken] = useState("");
  const [jiraDomain, setJiraDomain] = useState("");
  
  // API Test settings
  const [isApiTest, setIsApiTest] = useState<boolean>(false);
  const [apiEndpoint, setApiEndpoint] = useState<string>("");
  const [apiMethod, setApiMethod] = useState<string>("GET");
  const [apiPayload, setApiPayload] = useState<string>("{}");
  
  // Status tracking
  const [statusEvents, setStatusEvents] = useState<StatusEvent[]>([]);
  const [duration, setDuration] = useState(0);
  const intervalIdRef = useRef<NodeJS.Timeout | null>(null);
  const [triggerEffect, setTriggerEffect] = useState(false);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  // Add event to status log
  const addStatusEvent = (
    type: "info" | "success" | "error" | "warning",
    message: string,
    details?: string
  ) => {
    const newEvent: StatusEvent = {
      id: crypto.randomUUID(),
      timestamp: new Date(),
      type,
      message,
      details
    };

    console.log(newEvent);

    setStatusEvents(prev => [newEvent, ...prev]);
  };

  // Reset the test state
  const resetTest = () => {
    setTestScript("");
    setStatus("idle");
    setResults(null);
    setStatusTestErrors(null);
    setIterations(0);
    setStatusEvents([]);
    setDuration(0);
  };

  const cancelGeneration = async () => {
    try {
      // Cancel at backend
      await axios.post(`${import.meta.env.VITE_BACKEND_URL}/cancel_generation`);
      
      // Cancel at LLM server
      await axios.post(`${import.meta.env.VITE_LLM_URL}/cancel_generation`);
      
      // Close the event source
      if (eventSource) {
        eventSource.close();
        setEventSource(null);
      }
      
      // Reset state
      setStatus("idle");
      
      addStatusEvent("info", "Test generation cancelled");
      
    } catch (error) {
      console.error("Error cancelling test generation:", error);
      addStatusEvent("error", "Failed to cancel test generation");
    }
  };

  // Event source listener for real-time updates
  useEffect(() => {
    const eventSourceInstance = new EventSource(`${import.meta.env.VITE_BACKEND_URL}/api/stream`);
    setEventSource(eventSourceInstance);

    eventSourceInstance.onopen = () => {
      console.log("Connection established to /stream");
    };

    eventSourceInstance.onmessage = (event) => {
      const newEvent = JSON.parse(event.data);
      let details;

      if (newEvent.message === "Generating script") { 
        setStatus("generating");
      }
      else if (newEvent.message.includes("Refining test script")) {
        setIterations(prev => prev + 1);
        setStatus("refining");
      }
      else if (newEvent.message === "Executing test script") {
        details = `Framework: ${framework}`;
        setStatus("running");
      }
      else if (newEvent.message.includes("Max refinement attempts reached")) {
        setStatus("failed");
        setResults({
          status: "failed",
          message: "Max number of generations reached. This could mean:",
          errorDetails: "• Your test steps may need to be more specific\n• The webpage elements might not be accessible\n• The webpage structure might have changed\n\nPlease verify your test steps and check if the webpage is accessible.",
        });
      }
      else if (newEvent.type === "error" || newEvent.message === "Test execution failed" || newEvent.message === "Compilation failed") {
        setStatusTestErrors({
          message: newEvent.errors
        });
        setStatus("failed");
      }
      else if (newEvent.message === "Tests executed successfully" || newEvent.message === "API tests executed successfully") {
        details = "All test assertions passed";
        setResults({
          status: "passed",
          message: "Tests passed!",
        });
        setStatusTestErrors(null);
        setStatus("passed");
      }

      // If the event type is script, display the generated test script
      if (newEvent.type === 'script') {
        setTestScript(newEvent.message);
      } else {
        addStatusEvent(newEvent.type, newEvent.message, details);
      }
    };

    eventSourceInstance.onerror = (error) => {
      console.error('EventSource failed:', error);
      eventSourceInstance.close();
    };

    return () => {
      eventSourceInstance.close();
      setEventSource(null);
    };
  }, [triggerEffect, framework]);

  // Test script generation function
  const generateTestScript = async () => {
    // Reset previous test data
    resetTest();

    let finalTestSteps = testSteps;
    let finalUrl = url;

    if (useJira) {
      try {
        const response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/fetch_jira_test_steps`, {
          issue_key: jiraTicketId,
          email: jiraEmail,
          api_token: jiraToken,
          domain: jiraDomain,
        });
  
        const { test_steps, url } = response.data;
        finalTestSteps = test_steps;
        finalUrl = url;
        
        setTestSteps(test_steps);
        setUrl(url);
      } catch (error) {
        console.error("Failed to fetch from Jira:", error);
        alert("Error fetching from Jira. Check ticket ID or backend.");
        return; // Stop here if fetch fails
      }
    }

    // Initialize time tracking
    const startTime = new Date();
    console.log("Timer started at:", startTime);

    // Start real-time stopwatch that updates the UI
    const intervalId = setInterval(() => {
      const currentTime = new Date();
      const elapsedSeconds = (currentTime.getTime() - startTime.getTime()) / 1000;
      setDuration(elapsedSeconds);
    }, 100);

    // Store the interval ID in the ref
    intervalIdRef.current = intervalId;

    setStatus("extracting-and-processing-html");
    addStatusEvent("info", "Extracting and processing html");
    
    try {
      await axios.post(`${import.meta.env.VITE_BACKEND_URL}/api/send_test`, {
        test_steps: finalTestSteps,
        framework: framework,
        language: isApiTest ? framework : language,
        max_retries: maxRetries,
        jira_ticket_id: useJira ? jiraTicketId : null,
        jira_email: useJira ? jiraEmail : null,
        jira_token: useJira ? jiraToken : null,
        jira_domain: useJira ? jiraDomain : null,
        is_api_test: isApiTest,
        ...(isApiTest 
          ? {
              api_details: {
                endpoint: apiEndpoint,
                method: apiMethod,
                payload: apiPayload
              },
              url: [apiEndpoint]
            }
          : {
              url: isMultiPage ? [finalUrl, ...multiPageUrls.filter(Boolean)] : [finalUrl]
            }
        ),
      });
      
      setTriggerEffect(prev => !prev);
    } catch (error) {
      console.error('Error:', error);
      addStatusEvent("error", "Error sending test request", error instanceof Error ? error.message : "Unknown error");
      setStatus("idle");
    } finally {
      // Stop the timer using the ref
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    
      // Set final duration
      const endTime = new Date();
      const finalDuration = (endTime.getTime() - startTime.getTime()) / 1000;
      setDuration(finalDuration);
    }
  };

  return (
    <ArchiTestContext.Provider
      value={{
        url,
        setUrl,
        testSteps,
        setTestSteps,
        maxRetries,
        setMaxRetries,
        framework,
        setFramework,
        language,
        setLanguage,
        isMultiPage,
        setIsMultiPage,
        multiPageUrls,
        setMultiPageUrls,
        includeApi,
        setIncludeApi,
        status,
        generateTestScript,
        testScript,
        results,
        statusEvents,
        iterations,
        duration,
        statusTestErrors,
        useJira,
        setUseJira,
        jiraTicketId,
        setJiraTicketId,
        jiraEmail,
        setJiraEmail,
        jiraToken,
        setJiraToken,
        jiraDomain,
        setJiraDomain,
        isApiTest,
        setIsApiTest,
        apiEndpoint,
        setApiEndpoint,
        apiMethod,
        setApiMethod,
        apiPayload,
        setApiPayload,
        addStatusEvent,
        resetTest,
        cancelGeneration,
        eventSource
      }}
    >
      {children}
    </ArchiTestContext.Provider>
  );
};

export const useArchiTestContext = () => {
  const context = useContext(ArchiTestContext);
  if (context === undefined) {
    throw new Error('useArchiTestContext must be used within an ArchiTestProvider');
  }
  return context;
}; 
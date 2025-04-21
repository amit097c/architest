import React, { useState, useEffect, useRef } from "react";
import axios from 'axios';
import InputSection from "@/components/sections/InputSection";
import OutputSection from "@/components/sections/OutputSection";
import TestResultsSection from "./components/sections/TestResultsSection";
// import TestErrorsSection from "./components/sections/TestErrorsSection";
import ToolsSection from "@/components/sections/ToolsSection";
import StatusSection from "./components/sections/StatusSection";
import { Badge } from "@/components/ui/badge";

// Types
type TestStatus = "idle" | "extracting-and-processing-html" | "generating" | "running" | "passed" | "failed" | "refining";
type Framework = "playwright" | "cypress" | "selenium";
type Language = "python" | "javascript" | "java";

interface TestErrors {
  message: string;
}

interface TestResult {
  status: "passed" | "failed";
  message?: string;
  errorDetails?: string;
  iterations?: number;
}

interface StatusEvent {
  id: string;
  timestamp: Date;
  type: "info" | "success" | "error" | "warning";
  message: string;
  details?: string;
}

const ArchiTest: React.FC = () => {
  // State
  const [url, setUrl] = useState<string>("");
  const [testSteps, setTestSteps] = useState<string>("");
  const [maxRetries, setMaxRetries] = useState<number>(10);
  const [framework, setFramework] = useState<Framework>("playwright");
  const [testScript, setTestScript] = useState<string>("");
  const [status, setStatus] = useState<TestStatus>("idle");
  const [results, setResults] = useState<TestResult | null>(null);
  const [jiraEmail, setJiraEmail] = useState("");
  const [jiraToken, setJiraToken] = useState("");
  const [jiraDomain, setJiraDomain] = useState("");
  // const [testErrors, setTestErrors] = useState<TestErrors | null>(null);
  const [statusTestErrors, setStatusTestErrors] = useState<TestErrors | null>(null);
  const [iterations, setIterations] = useState<number>(0);
  const [isMultiPage, setIsMultiPage] = useState<boolean>(false);
  const [multiPageUrls, setMultiPageUrls] = useState<string[]>([]);
  const [includeApi, setIncludeApi] = useState<boolean>(false);
  const [triggerEffect, setTriggerEffect] = useState(false);
  const [language, setLanguage] = useState<Language>("python");
  // Status tracking
  const [statusEvents, setStatusEvents] = useState<StatusEvent[]>([]);
  const [duration, setDuration] = useState(0);
  const intervalIdRef = useRef<NodeJS.Timeout | null>(null);
  const [useJira, setUseJira] = useState(false);
  const [jiraTicketId, setJiraTicketId] = useState("");

  const [isApiTest, setIsApiTest] = useState<boolean>(false);
  const [apiEndpoint, setApiEndpoint] = useState<string>("");
  const [apiMethod, setApiMethod] = useState<string>("GET");
  const [apiPayload, setApiPayload] = useState<string>("{}");


  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8001/stream");

    eventSource.onopen = () => {
      console.log("Connection established to /stream");
    };

    eventSource.onmessage = (event) => {
      const newEvent = JSON.parse(event.data);

      // Statuses:
      // Extracting and processing html
      // Generating Script
      // Refining test script
      // Executing test script
      // Test execution failed
      // Tests executed successfully 

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
      // else if (newEvent.type === "error_msg") {
      //   setResults({
      //     status: "failed",
      //     message: "Test failed to execute correctly",
      //     errorDetails: newEvent.message,
      //   });
      //   setStatus("failed");
      // }
      else if (newEvent.message === "Tests executed successfully") {
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

    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [triggerEffect,framework]);

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

  // Mock function to simulate test script generation
  const generateTestScript = async() => {
    // Reset previous test data
    resetTest();

    let finalTestSteps = testSteps;
    let finalUrl = url;

    if (useJira) {
      try {
        const response = await axios.post("http://localhost:8001/fetch_jira_test_steps", {
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
      console.log("Timer tick, elapsed seconds:", elapsedSeconds);
      setDuration(elapsedSeconds);
    }, 100); // this function runs every second

    // Store the interval ID in the ref
    intervalIdRef.current = intervalId;

    setStatus("extracting-and-processing-html");
    addStatusEvent("info", "Extracting and processing html");
    console.log("sending request to send_test with payload", {finalUrl, finalTestSteps, framework});
    (axios.post('http://localhost:8001/send_test', {
      // url: isMultiPage ? [finalUrl, ...multiPageUrls.filter(Boolean)] : [finalUrl],
      test_steps: finalTestSteps, // Ensure test_steps matches API expectations
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
            url: [apiEndpoint] // Include endpoint as URL for API tests
          }
        : {
            url: isMultiPage ? [finalUrl, ...multiPageUrls.filter(Boolean)] : [finalUrl]
          }
      ),
    }) as Promise<any>)
    .then(response => {
      console.log('Success:', response.data);
      setTriggerEffect(prev => !prev); 
    })
    .catch(error => {
      console.error('Error:', error);
    })
    .finally(() => {
      // Stop the timer using the ref
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    
      // Set final duration
      const endTime = new Date();
      const finalDuration = (endTime.getTime() - startTime.getTime()) / 1000;
      setDuration(finalDuration);
      
      setStatus("idle");

      console.log(`Final duration: ${finalDuration} seconds`);
    });
  };

  const StatusBadge = () => {
    switch (status) {
      case "idle":
        return null;
      case "generating":
        return <Badge variant="outline" className="bg-blue-50 text-blue-500">Generating Script...</Badge>;
      case "running":
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-500">Running Tests...</Badge>;
      case "passed":
        return <Badge variant="outline" className="bg-green-50 text-green-500">Tests Passed</Badge>;
      case "failed":
        return <Badge variant="outline" className="bg-red-50 text-red-500">Tests Failed</Badge>;
      case "refining":
        return <Badge variant="outline" className="bg-purple-50 text-purple-500">Refining Script...</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <header className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">ArchiTest</h1>
          <p className="text-muted-foreground">AI-Powered Test Script Generator</p>
        </div>
        <StatusBadge />
      </header>

      <div className="grid gap-6 md:grid-cols-12">
        <div className="md:col-span-5 space-y-6">
          <InputSection
            url={url}
            setUrl={setUrl}
            testSteps={testSteps}
            setTestSteps={setTestSteps}
            maxRetries={maxRetries}
            setMaxRetries={setMaxRetries}
            framework={framework}
            setFramework={setFramework}
            language={language}
            setLanguage={setLanguage}
            isMultiPage={isMultiPage}
            setIsMultiPage={setIsMultiPage}
            multiPageUrls={multiPageUrls}
            setMultiPageUrls={setMultiPageUrls}
            includeApi={includeApi}
            setIncludeApi={setIncludeApi}
            useJira={useJira}
            setUseJira={setUseJira}
            jiraTicketId={jiraTicketId}
            setJiraTicketId={setJiraTicketId}
            status={status}
            generateTestScript={generateTestScript}
            jiraEmail={jiraEmail}
            setJiraEmail={setJiraEmail}
            jiraToken={jiraToken}
            setJiraToken={setJiraToken}
            jiraDomain={jiraDomain}
            setJiraDomain={setJiraDomain}
            isApiTest={isApiTest}
            setIsApiTest={setIsApiTest}
            apiEndpoint={apiEndpoint}
            setApiEndpoint={setApiEndpoint}
            apiMethod={apiMethod}
            setApiMethod={setApiMethod}
            apiPayload={apiPayload}
            setApiPayload={setApiPayload}
          />

          <TestResultsSection 
            results={results}
          />
        </div>

        <div className="md:col-span-7 space-y-6">
          <OutputSection
            testScript={testScript}
            iterations={iterations}
            addStatusEvent={addStatusEvent}
          />

          <StatusSection
            currentStatus={status}
            events={statusEvents}
            iterations={iterations}
            duration={duration}
            statusTestErrors={statusTestErrors}
          />

          <ToolsSection />
        </div>
      </div>
    </div>
  );
};

export default ArchiTest;

import React, { useState, useEffect, useRef } from "react";
import axios from 'axios';
import InputSection from "@/components/sections/InputSection";
import OutputSection from "@/components/sections/OutputSection";
import TestResultsSection from "./components/sections/TestResultsSection";
import ToolsSection from "@/components/sections/ToolsSection";
import StatusSection from "./components/sections/StatusSection";
import { Badge } from "@/components/ui/badge";

// Types
type TestStatus = "idle" | "extracting-and-processing-html" | "generating" | "running" | "passed" | "failed" | "refining";
type Framework = "playwright" | "cypress" | "selenium";

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
  const [framework, setFramework] = useState<Framework>("playwright");
  const [testScript, setTestScript] = useState<string>("");
  const [status, setStatus] = useState<TestStatus>("idle");
  const [results, setResults] = useState<TestResult | null>(null);
  const [iterations, setIterations] = useState<number>(0);
  const [isMultiPage, setIsMultiPage] = useState<boolean>(false);
  const [includeApi, setIncludeApi] = useState<boolean>(false);
  const [triggerEffect, setTriggerEffect] = useState(false);
  // Status tracking
  const [statusEvents, setStatusEvents] = useState<StatusEvent[]>([]);
  const [duration, setDuration] = useState(0);
  const intervalIdRef = useRef<NodeJS.Timeout | null>(null);

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

      if (newEvent.message === "Generating test script") { 
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
          message: "Unable to generate a valid test script after 10 attempts.",
          errorDetails: newEvent.details,
        });
      }
      else if (newEvent.message === "Test execution failed") {
        // placeholder (replace in the future)
        const errorMsg = "Unable to locate element: .results-count";
        setResults({
          status: "failed",
          message: "Test failed to execute correctly",
          errorDetails: errorMsg,
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
  }, [triggerEffect]);

  // Add event to status log
  const addStatusEvent = (
    type: "info" | "success" | "error" | "warning",
    message: string,
    details?: string
  ) => {
    const newEvent: StatusEvent = {
      id: Date.now().toString(),
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
    setIterations(0);
    setStatusEvents([]);
    setDuration(0);
  };

  // Mock function to simulate test script generation
  const generateTestScript = () => {
    // Reset previous test data
    resetTest();

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

    (axios.post('http://localhost:8001/send_test', {
      url,
      test_steps: testSteps, // Ensure test_steps matches API expectations
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
        <div className="md:col-span-5">
          <InputSection
            url={url}
            setUrl={setUrl}
            testSteps={testSteps}
            setTestSteps={setTestSteps}
            framework={framework}
            setFramework={setFramework}
            isMultiPage={isMultiPage}
            setIsMultiPage={setIsMultiPage}
            includeApi={includeApi}
            setIncludeApi={setIncludeApi}
            status={status}
            generateTestScript={generateTestScript}
          />
        </div>

        <div className="md:col-span-7 space-y-6">
          <OutputSection
            testScript={testScript}
            iterations={iterations}
            addStatusEvent={addStatusEvent}
          />

          <TestResultsSection 
            results={results}
            duration={duration}
          />

          <StatusSection
            currentStatus={status}
            events={statusEvents}
            iterations={iterations}
            duration={duration}
          />

          <ToolsSection />
        </div>
      </div>
    </div>
  );
};

export default ArchiTest;

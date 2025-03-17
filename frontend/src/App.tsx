import React, { useState, useEffect, useRef } from "react";
import axios from 'axios';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle, AlertCircle, Play, RefreshCw, Globe, FileText, Save, Copy, Download } from "lucide-react";
import StatusSection from "./StatusSection";

// Types
type TestStatus = "idle" | "generating" | "running" | "passed" | "failed" | "refining";
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
      // Generating Script
      // Refining test script
      // Executing test script
      // Test execution failed
      // Tests executed successfully 

      let details;

      if (newEvent.message.includes("Refining test script")) {
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
    setStatus("generating");

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
        {/* Left Column - Input */}
        <Card className="md:col-span-5">
          <CardHeader>
            <CardTitle>Test Configuration</CardTitle>
            <CardDescription>
              Provide a URL and test steps to generate automated test scripts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="url" className="text-sm font-medium">Target URL</label>
              <Input
                id="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="test-steps" className="text-sm font-medium">Test Steps</label>
              <Textarea
                id="test-steps"
                placeholder="1. Navigate to homepage
2. Search for 'product'
3. Verify search results appear
4. Click on first result
5. Verify product details page loads"
                value={testSteps}
                onChange={(e) => setTestSteps(e.target.value)}
                rows={8}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label htmlFor="framework" className="text-sm font-medium">Framework</label>
                <Select
                  value={framework}
                  onValueChange={(value: Framework) => setFramework(value)}
                >
                  <SelectTrigger id="framework">
                    <SelectValue placeholder="Select framework" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="playwright">Playwright</SelectItem>
                    <SelectItem value="cypress">Cypress</SelectItem>
                    <SelectItem value="selenium">Selenium</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Options</label>
                <div className="flex space-x-3 pt-2">
                  <Button
                    variant={isMultiPage ? "default" : "outline"}
                    size="sm"
                    onClick={() => setIsMultiPage(!isMultiPage)}
                  >
                    Multi-Page
                  </Button>
                  <Button
                    variant={includeApi ? "default" : "outline"}
                    size="sm"
                    onClick={() => setIncludeApi(!includeApi)}
                  >
                    API Tests
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button
              className="w-full"
              onClick={generateTestScript}
              disabled={!url || !testSteps || status !== "idle"}
            >
              {status === "idle" ? (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Generate & Run Tests
                </>
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              {status === "generating" ? "Generating..." :
                status === "running" ? "Running..." :
                  status === "refining" ? "Refining..." :
                  status === "passed" ? "Tests Passed" :
                  status === "failed" ? "Tests Failed" : ""}
            </Button>
          </CardFooter>
        </Card>

        {/* Right Column - Output */}
        <div className="md:col-span-7 space-y-6">
          {/* Test Script Card */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle>Generated Test Script</CardTitle>
                <CardDescription>
                  AI-generated test script based on your inputs
                </CardDescription>
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="icon"
                  disabled={!testScript}
                  onClick={() => {
                    navigator.clipboard.writeText(testScript);
                    addStatusEvent("info", "Test script copied to clipboard");
                  }}
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  disabled={!testScript}
                  onClick={() => {
                    addStatusEvent("info", "Test script saved");
                    // Implement save functionality here
                  }}
                >
                  <Save className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-60 w-full rounded-md border">
                {testScript ? (
                  <pre className="p-4 text-sm">
                    <code>{testScript}</code>
                  </pre>
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <p>Your generated test script will appear here</p>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Status Section */}
          <StatusSection
            currentStatus={status}
            events={statusEvents}
            iterations={iterations}
            duration={duration}
          />

          {/* Test Results */}
          {results && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center">
                  {results.status === "passed" ? (
                    <>
                      <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                      <span>Test Results - Passed</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="mr-2 h-5 w-5 text-red-500" />
                      <span>Test Results - Failed</span>
                    </>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Alert variant={results.status === "passed" ? "default" : "destructive"}>
                  <AlertTitle>
                    {results.status === "passed" ? "Success" : "Error"}
                  </AlertTitle>
                  <AlertDescription>
                    {results.message}
                    {results.errorDetails && (
                      <div className="mt-2 p-2 bg-red-50 rounded text-sm">
                        {results.errorDetails}
                      </div>
                    )}
                    {results.iterations && (
                      <div className="mt-2 text-sm text-muted-foreground">
                        Tests completed after {results.iterations} iteration{results.iterations !== 1 ? 's' : ''}
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          )}

          {/* Additional Tools Tabs */}
          <Tabs defaultValue="execution">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="execution">
                <Play className="mr-2 h-4 w-4" />
                Execution
              </TabsTrigger>
              <TabsTrigger value="browser">
                <Globe className="mr-2 h-4 w-4" />
                Browser
              </TabsTrigger>
              <TabsTrigger value="reports">
                <FileText className="mr-2 h-4 w-4" />
                Reports
              </TabsTrigger>
            </TabsList>
            <TabsContent value="execution" className="p-4 border rounded-md mt-2">
              <h3 className="text-sm font-medium mb-2">Execution Settings</h3>
              <div className="grid grid-cols-2 gap-4">
                <Select defaultValue="chromium">
                  <SelectTrigger>
                    <SelectValue placeholder="Browser" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="chromium">Chromium</SelectItem>
                    <SelectItem value="firefox">Firefox</SelectItem>
                    <SelectItem value="webkit">WebKit</SelectItem>
                  </SelectContent>
                </Select>
                <Select defaultValue="desktop">
                  <SelectTrigger>
                    <SelectValue placeholder="Device" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="desktop">Desktop</SelectItem>
                    <SelectItem value="tablet">Tablet</SelectItem>
                    <SelectItem value="mobile">Mobile</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>
            <TabsContent value="browser" className="p-4 border rounded-md mt-2">
              <div className="text-center text-muted-foreground p-6">
                Browser preview will appear here during test execution
              </div>
            </TabsContent>
            <TabsContent value="reports" className="p-4 border rounded-md mt-2">
              <div className="flex justify-between mb-4">
                <h3 className="text-sm font-medium">Test Reports</h3>
                <Button variant="outline" size="sm">
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </Button>
              </div>
              <div className="text-center text-muted-foreground p-6">
                Test reports will be available after execution
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default ArchiTest;

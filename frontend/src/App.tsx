import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { CheckCircle, AlertCircle, Play, RefreshCw, Code, Globe, FileText, Save, Copy, Download } from "lucide-react";
import StatusSection from "./StatusSection";
// Uncomment when connecting to real API
// import { architestService } from '../services/architestService';

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

  // Status tracking
  const [statusEvents, setStatusEvents] = useState<StatusEvent[]>([]);
  const [startTime, setStartTime] = useState<Date | undefined>(undefined);
  const [endTime, setEndTime] = useState<Date | undefined>(undefined);

  const [events, setEvents] = useState([]);

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8001/stream");

    eventSource.onmessage = (event) => {
      const newEvent = event.data;
      console.log(newEvent);
    };

    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

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

    setStatusEvents(prev => [newEvent, ...prev]);
  };

  // Reset the test state
  const resetTest = () => {
    setTestScript("");
    setStatus("idle");
    setResults(null);
    setIterations(0);
    setStatusEvents([]);
    setStartTime(undefined);
    setEndTime(undefined);
  };

  // Mock function to simulate test script generation
  const generateTestScript = () => {
    // Reset previous test data
    resetTest();

    // Set start time
    const start = new Date();
    setStartTime(start);

    // Update status
    setStatus("generating");
    addStatusEvent("info", "Starting test script generation", `URL: ${url}`);

    // Simulate API call delay
    setTimeout(() => {
      const sampleScript = `import { test, expect } from '@playwright/test';

test('${testSteps.split('\n')[0]}', async ({ page }) => {
  // Navigate to the page
  await page.goto('${url}');
  
  // Your test steps
  const searchInput = page.locator('[aria-label="Search"]');
  await expect(searchInput).toBeVisible();
  await searchInput.fill('Automated Testing');
  await searchInput.press('Enter');
  
  // Verify results appear
  await expect(page.locator('.results-container')).toBeVisible();
  await expect(page.locator('.results-count')).toContainText('results');
});`;

      setTestScript(sampleScript);
      addStatusEvent("success", "Test script generated successfully");
      setStatus("running");
      addStatusEvent("info", "Executing test script", `Framework: ${framework}`);

      // Simulate test running
      setTimeout(() => {
        const passTest = Math.random() > 0.3;

        if (passTest) {
          setStatus("passed");
          setResults({
            status: "passed",
            message: "All tests have passed successfully!",
            iterations: iterations + 1
          });
          addStatusEvent("success", "Tests executed successfully", "All test assertions passed");
          setEndTime(new Date());
        } else {
          setStatus("failed");
          const errorMsg = "Unable to locate element: .results-count";
          setResults({
            status: "failed",
            message: "Test failed to execute correctly",
            errorDetails: errorMsg,
            iterations: iterations + 1
          });
          addStatusEvent("error", "Test execution failed", errorMsg);

          // Simulate refining
          setStatus("refining");
          addStatusEvent("info", "Refining test script", "Attempting to fix element selector");

          setTimeout(() => {
            setIterations(prev => prev + 1);
            const refinedScript = sampleScript.replace(
              ".results-count",
              ".search-results-count"
            );
            setTestScript(refinedScript);
            addStatusEvent("info", "Script refinement complete", "Updated element selector");

            // Run the refined script
            addStatusEvent("info", "Executing refined test script");
            setTimeout(() => {
              setStatus("passed");
              setResults({
                status: "passed",
                message: "Tests passed after refinement!",
                iterations: iterations + 2
              });
              addStatusEvent("success", "Refined test executed successfully");
              setEndTime(new Date());
            }, 1500);
          }, 2000);
        }
      }, 2000);
    }, 2000);
  };

  // Status badge component
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
              disabled={!url || !testSteps || status === "generating" || status === "running" || status === "refining"}
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
                    "Generate & Run Tests"}
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
                  {iterations > 0 ? `Iteration ${iterations}` : "AI-generated test script based on your inputs"}
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
            startTime={startTime}
            endTime={endTime}
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

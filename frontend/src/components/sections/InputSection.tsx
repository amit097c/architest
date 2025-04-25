import React, {Dispatch, SetStateAction, useEffect} from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Play, Loader } from "lucide-react";

type Framework = 'playwright' | 'cypress' | 'selenium';
type Language = 'python' | 'javascript' | 'java';

interface InputSectionProps {
  url: string;
  setUrl: (url: string) => void;
  testSteps: string;
  setTestSteps: (steps: string) => void;
  maxRetries: number;
  setMaxRetries: Dispatch<SetStateAction<number>>;
  framework: Framework;
  setFramework: Dispatch<SetStateAction<Framework>>;
  isMultiPage: boolean;
  setIsMultiPage: (isMultiPage: boolean) => void;
  multiPageUrls: string[];
  setMultiPageUrls: Dispatch<SetStateAction<string[]>>;
  includeApi: boolean;
  setIncludeApi: (includeApi: boolean) => void;
  status: 'idle' | 'extracting-and-processing-html' | 'generating' | 'running' | 'refining' | 'passed' | 'failed';
  generateTestScript: () => void;
  language: Language;
  setLanguage: Dispatch<SetStateAction<Language>>;
  useJira: boolean;
  setUseJira: Dispatch<SetStateAction<boolean>>;
  jiraTicketId: string;
  setJiraTicketId: Dispatch<SetStateAction<string>>;
  jiraEmail: string;
  setJiraEmail: Dispatch<SetStateAction<string>>;
  jiraToken: string;
  setJiraToken: Dispatch<SetStateAction<string>>;
  jiraDomain: string;
  setJiraDomain: Dispatch<SetStateAction<string>>;
  isApiTest: boolean;
  setIsApiTest: (isApiTest: boolean) => void;
  apiEndpoint: string;
  setApiEndpoint: (endpoint: string) => void;
  apiMethod: string;
  setApiMethod: (method: string) => void;
  apiPayload: string;
  setApiPayload: (payload: string) => void;
  onCancel: () => Promise<void>;
}

const InputSection: React.FC<InputSectionProps> = ({
  url,
  setUrl,
  testSteps,
  setTestSteps,
  maxRetries,
  setMaxRetries,
  framework,
  setFramework,
  status,
  generateTestScript,
  language,
  setLanguage,
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
  onCancel
}) => {
  // Function to handle the generation of test scripts
  const apiMethods = [
    { value: "GET", label: "GET" },
    { value: "POST", label: "POST" },
    { value: "PUT", label: "PUT" },
    { value: "DELETE", label: "DELETE" }
  ];


  // Function to get available languages for the selected framework
  const getAvailableLanguages = (framework: Framework) => {
    if (isApiTest) {
      return [
        { value: "postman", label: "Postman" },
        { value: "restassured", label: "REST Assured" }
      ];
    }
    switch (framework) {
      case "playwright":
        return [
          { value: "python", label: "Python" },
          { value: "javascript", label: "JavaScript" }
        ];
      case "selenium":
        return [
          { value: "java", label: "Java" }
        ];
      case "cypress":
        return [
          { value: "javascript", label: "JavaScript" }
        ];
      default:
        return [];
    }
  };

  // Update language when framework changes if current language isn't available
  useEffect(() => {
    const availableLanguages = getAvailableLanguages(framework);
    if (!availableLanguages.some(lang => lang.value === language)) {
      setLanguage(availableLanguages[0].value as Language);
    }
  }, [framework]);

  // Get available frameworks based on testing type
  const getAvailableFrameworks = (isApiTest: boolean) => {
    if (isApiTest) {
      return [
        { value: "postman", label: "Postman" },
        { value: "restassured", label: "REST Assured" }
      ];
    }
    return [
      { value: "playwright", label: "Playwright" },
      { value: "selenium", label: "Selenium" },
      { value: "cypress", label: "Cypress" }
    ];
  };
  // Define default test steps for API and UI tests
  const defaultApiSteps = "1. Send GET request to /users\n2. Verify response status is 200\n3. Validate user data in response";
  const defaultUiSteps = "1. Navigate to homepage\n2. Search for 'product'\n3. Verify search results appear\n4. Click on first result\n5. Verify product details page loads";

  // Update framework when switching between UI and API testing
  useEffect(() => {
    const frameworks = getAvailableFrameworks(isApiTest);
    setFramework(frameworks[0].value as Framework);
    setTestSteps("");
    
    // Reset Jira settings when switching to API Testing
    if (isApiTest && useJira) {
      setUseJira(false);
      setJiraTicketId("");
      setJiraEmail("");
      setJiraToken("");
      setJiraDomain("");
    }
  }, [isApiTest]);


  return (
    <Card>
      <CardHeader>
        <CardTitle>Test Configuration</CardTitle>
        <CardDescription>
        {isApiTest
            ? "Configure API test settings"
            : "Provide a URL and test steps to generate automated test scripts"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Testing Type Toggle */}
        <div className="flex space-x-3">
          <Button
            variant={!isApiTest ? "default" : "outline"}
            size="sm"
            onClick={() => setIsApiTest(false)}
          >
            Script Testing
          </Button>
          <Button
            variant={isApiTest ? "default" : "outline"}
            size="sm"
            onClick={() => setIsApiTest(true)}
          >
            API Testing
          </Button>
        </div>

        {/* Show URL input only for UI testing */}
        {!isApiTest && (
          <>
            <div className="space-y-2">
              <label htmlFor="url" className="text-sm font-medium">Target URL</label>
              <Input
                id="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          </>
        )}

        {/* API Testing Fields */}
        {isApiTest && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="apiEndpoint" className="text-sm font-medium">API Endpoint</label>
              <Input
                id="apiEndpoint"
                placeholder="https://api.example.com/v1/resource"
                value={apiEndpoint}
                onChange={(e) => setApiEndpoint(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">HTTP Method</label>
              <Select
                value={apiMethod}
                onValueChange={setApiMethod}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select HTTP method" />
                </SelectTrigger>
                <SelectContent>
                  {apiMethods.map(method => (
                    <SelectItem key={method.value} value={method.value}>
                      {method.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {(apiMethod === "POST" || apiMethod === "PUT") && (
              <div className="space-y-2">
                <label htmlFor="apiPayload" className="text-sm font-medium">Request Payload (JSON)</label>
                <Textarea
                  id="apiPayload"
                  placeholder="{}"
                  value={apiPayload}
                  onChange={(e) => setApiPayload(e.target.value)}
                />
              </div>
            )}
          </div>
        )}

        

        {/* Test Steps Input */}
        <div className="space-y-2">
          <label htmlFor="test-steps" className="text-sm font-medium">Test Steps</label>
          <Textarea
            id="test-steps"
            /*placeholder={isApiTest
              ? "1. Send GET request to /users\n2. Verify response status is 200\n3. Validate user data in response"
              : "1. Navigate to homepage\n2. Search for 'product'\n3. Verify search results appear\n4. Click on first result\n5. Verify product details page loads"
            }*/
           
            placeholder={isApiTest ? defaultApiSteps : defaultUiSteps}
            value={testSteps}
            onChange={(e) => setTestSteps(e.target.value)}
            rows={8}
          />
        </div>

        {/* Jira Ticket ID Input - Only show in Script Testing mode */}
        {!isApiTest && useJira && (
          <div className="space-y-2">
            <label htmlFor="jira-ticket" className="text-sm font-medium">Jira Ticket ID</label>
            <Input
              id="jira-ticket"
              placeholder="e.g. SCRUM-1"
              value={jiraTicketId}
              onChange={(e) => setJiraTicketId(e.target.value)}
            />
          </div>
        )}

        {/* Jira credentials - Only show in Script Testing mode */}
        {!isApiTest && useJira && (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium">Jira Email</label>
              <Input
                placeholder="you@example.com"
                value={jiraEmail}
                onChange={(e) => setJiraEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">API Token</label>
              <Input
                placeholder="Your Jira API Token"
                value={jiraToken}
                onChange={(e) => setJiraToken(e.target.value)}
                type="password"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Jira Domain</label>
              <Input
                placeholder="https://yourcompany.atlassian.net"
                value={jiraDomain}
                onChange={(e) => setJiraDomain(e.target.value)}
              />
            </div>
          </>
        )}

        {/* Max Retries Input */}
        <div className="space-y-2">
          <label htmlFor="max-retries" className="text-sm font-medium">Max Refinement Attempts</label>
          <Select
            value={maxRetries.toString()}
            onValueChange={(value) => setMaxRetries(Number(value))}
          >
            <SelectTrigger id="max-retries">
              <SelectValue placeholder="Select max retries" />
            </SelectTrigger>
            <SelectContent>
              {[...Array(25)].map((_, i) => (
                <SelectItem key={i+1} value={(i+1).toString()}>
                  {i + 1}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Framework and Language Options */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label htmlFor="framework" className="text-sm font-medium">Framework</label>
            <Select
              value={framework}
              onValueChange={(value) => setFramework(value as Framework)}
            >
              <SelectTrigger id="framework">
                <SelectValue placeholder="Select framework" />
              </SelectTrigger>
              <SelectContent>
                {getAvailableFrameworks(isApiTest).map(fw => (
                  <SelectItem key={fw.value} value={fw.value}>
                    {fw.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

            {/* Language Selection */}
            {!isApiTest && (
            <div className="space-y-2">
              <label htmlFor="language" className="text-sm font-medium">Language</label>
              <Select
                value={language}
                onValueChange={(value) => setLanguage(value as Language)}
              >
                <SelectTrigger id="language">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  {getAvailableLanguages(framework).map(lang => (
                    <SelectItem key={lang.value} value={lang.value}>
                      {lang.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* Options - Only show in Script Testing mode */}
        {!isApiTest && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Options</label>
            <div className="flex space-x-3 pt-2">
              <Button
                variant={useJira ? "default" : "outline"}
                size="sm"
                onClick={() => setUseJira(!useJira)}
              >
                {useJira ? "Jira Enabled" : "Use Jira Ticket"}
              </Button>
            </div>
        </div>
        )}
      </CardContent>
      <CardFooter>
      <div className="flex flex-col w-full space-y-2">
        <Button
          className="w-full"
          onClick={generateTestScript}
          //disabled={!url || !testSteps || status !== "idle"}
          disabled={isApiTest ? !apiEndpoint || !testSteps || (status !== "idle" && status !== "passed" && status !== "failed") : (!useJira && (!url || !testSteps)) || (status !== "idle" && status !== "passed" && status !== "failed")}
        >
          {status === "idle" || status === "passed" || status === "failed" ? (
            <>
              <Play className="mr-2 h-4 w-4" />
              Generate & Run Tests
            </>
          ) : (
            <>
              <Loader className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          )}
        </Button>

        {/* Show Stop button when script is running */}
        {(status === "generating" || status === "running" || status === "refining" || status === "extracting-and-processing-html") && (
          <Button
            variant="destructive"
            className="w-full"
            onClick={onCancel}
          >
            Stop Execution
          </Button>
        )}
      </div>
      </CardFooter>
    </Card>
  );
};

export default InputSection;
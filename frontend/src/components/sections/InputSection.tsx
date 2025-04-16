import React, {Dispatch, SetStateAction, useEffect} from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Play, RefreshCw } from "lucide-react";

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
  status: string;
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
  isMultiPage,
  setIsMultiPage,
  multiPageUrls,
  setMultiPageUrls,
  includeApi,
  setIncludeApi,
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
  setJiraDomain
}) => {
  // Function to get available languages for the selected framework
  const getAvailableLanguages = (framework: Framework) => {
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Test Configuration</CardTitle>
        <CardDescription>
          Provide a URL and test steps to generate automated test scripts
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* URL Input */}
        <div className="space-y-2">
          <label htmlFor="url" className="text-sm font-medium">Target URL</label>
          <Input
            id="url"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>

        {/* Multi-Page URLs Input */}
        {isMultiPage && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Additional URLs</label>
            {multiPageUrls.map((pageUrl, index) => (
              <div key={index} className="flex space-x-2">
                <Input
                  value={pageUrl}
                  onChange={(e) => {
                    const updated = [...multiPageUrls];
                    updated[index] = e.target.value;
                    setMultiPageUrls(updated);
                  }}
                  placeholder={`Page URL ${index + 1}`}
                />
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    const updated = multiPageUrls.filter((_, i) => i !== index);
                    setMultiPageUrls(updated);
                  }}
                >
                  Remove
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setMultiPageUrls([...multiPageUrls, ""])}
            >
              + Add Page
            </Button>
          </div>
        )}

        {/* Test Steps Input */}
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

        {/* Jira Ticket ID Input */}
        {useJira && (
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

        {useJira && (
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
                <SelectItem value="playwright">Playwright</SelectItem>
                <SelectItem value="cypress">Cypress</SelectItem>
                <SelectItem value="selenium">Selenium</SelectItem>
              </SelectContent>
            </Select>
          </div>

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
        </div>

        {/* Options */}
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
            <Button
              variant={useJira ? "default" : "outline"}
              size="sm"
              onClick={() => setUseJira(!useJira)}
            >
              {useJira ? "Jira Enabled" : "Use Jira Ticket"}
            </Button>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button
          className="w-full"
          onClick={generateTestScript}
          //disabled={!url || !testSteps || status !== "idle"}
          disabled={(!useJira && (!url || !testSteps)) || status !== "idle"}
        >
          {status === "idle" ? (
            <>
              <Play className="mr-2 h-4 w-4" />
              Generate & Run Tests
            </>
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          {status === "extracting-and-processing-html" ? "Extracting and processing HTML..." :
           status === "generating" ? "Generating..." :
           status === "running" ? "Running..." :
           status === "refining" ? "Refining..." :
           status === "passed" ? "Tests Passed" :
           status === "failed" ? "Tests Failed" : ""}
        </Button>
      </CardFooter>
    </Card>
  );
};

export default InputSection;
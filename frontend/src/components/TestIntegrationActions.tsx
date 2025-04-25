import React, { useState, useEffect } from 'react';
import { SavedTest } from '@/lib/types';
import { TestStorageService } from '@/lib/storage-service';
import { IntegrationService } from '@/lib/integration-service';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2, Github } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

interface TestIntegrationActionsProps {
  test: SavedTest;
}

const TestIntegrationActions: React.FC<TestIntegrationActionsProps> = ({ test }) => {
  const [jiraAvailable, setJiraAvailable] = useState(false);
  const [githubAvailable, setGithubAvailable] = useState(false);
  const [creatingJiraIssue, setCreatingJiraIssue] = useState(false);
  const [creatingGithubIssue, setCreatingGithubIssue] = useState(false);
  const [jiraIssueKey, setJiraIssueKey] = useState<string | null>(null);
  const [githubIssueUrl, setGithubIssueUrl] = useState<string | null>(null);
  
  useEffect(() => {
    checkIntegrations();
  }, []);
  
  const checkIntegrations = async () => {
    try {
      const settings = await TestStorageService.getIntegrationSettings();
    setJiraAvailable(!!settings.jira);
    setGithubAvailable(!!settings.github);
    } catch (error) {
      console.error('Error checking integrations:', error);
    }
  };
  
  const createJiraIssue = async () => {
    setCreatingJiraIssue(true);
    
    try {
      const issue = await IntegrationService.createJiraIssue(test);
      if (issue) {
        setJiraIssueKey(issue.key);
      }
    } catch (error) {
      console.error('Error creating Jira issue:', error);
    } finally {
      setCreatingJiraIssue(false);
    }
  };
  
  const createGithubIssue = async () => {
    setCreatingGithubIssue(true);
    
    try {
      const issue = await IntegrationService.createGitHubIssue(test);
      if (issue) {
        setGithubIssueUrl(issue.html_url);
      }
    } catch (error) {
      console.error('Error creating GitHub issue:', error);
    } finally {
      setCreatingGithubIssue(false);
    }
  };
  
  if (!jiraAvailable && !githubAvailable) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Integrations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-6 text-center">
            <div>
              <AlertCircle className="h-10 w-10 text-muted-foreground mb-2 mx-auto" />
              <p className="text-muted-foreground">No integrations configured</p>
              <Button 
                variant="link" 
                className="mt-2" 
                onClick={() => window.location.href = '/integrations'}
              >
                Configure Integrations
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>External Integrations</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue={jiraAvailable ? "jira" : "github"} className="w-full">
          <TabsList className="mb-4 grid grid-cols-2">
            <TabsTrigger value="jira" disabled={!jiraAvailable}>Jira</TabsTrigger>
            <TabsTrigger value="github" disabled={!githubAvailable}>GitHub</TabsTrigger>
          </TabsList>
          
          {jiraAvailable && (
            <TabsContent value="jira">
              <div className="p-4 border rounded-md">
                {jiraIssueKey ? (
                  <div className="text-center">
                    <p className="mb-2">Issue created successfully!</p>
                    <p className="text-xl font-bold mb-4">{jiraIssueKey}</p>
                    <Button 
                      variant="outline" 
                      onClick={async () => {
                        try {
                          const settings = await TestStorageService.getIntegrationSettings();
                        if (settings.jira) {
                          window.open(`${settings.jira.url}/browse/${jiraIssueKey}`, '_blank');
                          }
                        } catch (error) {
                          console.error('Error getting integration settings:', error);
                        }
                      }}
                    >
                      View in Jira
                    </Button>
                  </div>
                ) : (
                  <div className="text-center">
                    <p className="mb-4">Create a Jira issue for this test</p>
                    <Button 
                      onClick={createJiraIssue} 
                      disabled={creatingJiraIssue}
                    >
                      {creatingJiraIssue ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Creating Issue...
                        </>
                      ) : (
                        'Create Jira Issue'
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>
          )}
          
          {githubAvailable && (
            <TabsContent value="github">
              <div className="p-4 border rounded-md">
                {githubIssueUrl ? (
                  <div className="text-center">
                    <p className="mb-2">Issue created successfully!</p>
                    <p className="text-sm text-muted-foreground mb-4 truncate">{githubIssueUrl}</p>
                    <Button 
                      variant="outline"
                      onClick={() => window.open(githubIssueUrl, '_blank')}
                    >
                      <Github className="h-4 w-4 mr-2" />
                      View on GitHub
                    </Button>
                  </div>
                ) : (
                  <div className="text-center">
                    <p className="mb-4">Create a GitHub issue for this test</p>
                    <Button 
                      onClick={createGithubIssue} 
                      disabled={creatingGithubIssue}
                    >
                      {creatingGithubIssue ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Creating Issue...
                        </>
                      ) : (
                        <>
                          <Github className="h-4 w-4 mr-2" />
                          Create GitHub Issue
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>
          )}
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default TestIntegrationActions; 
import React, { useState, useEffect } from 'react';
import { TestStorageService } from '@/lib/storage-service';
import { IntegrationService } from '@/lib/integration-service';
import { JiraConfig, GitHubConfig } from '@/lib/types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { CheckCircle2, XCircle, Loader2, Github, ExternalLink } from 'lucide-react';

const IntegrationsPage: React.FC = () => {
  // Jira state
  const [jiraConfig, setJiraConfig] = useState<JiraConfig>({
    url: '',
    apiToken: '',
    email: '',
    project: ''
  });
  const [jiraConnected, setJiraConnected] = useState(false);
  const [jiraTestingConnection, setJiraTestingConnection] = useState(false);
  const [jiraTestResult, setJiraTestResult] = useState<'success' | 'error' | null>(null);

  // GitHub state
  const [githubConfig, setGithubConfig] = useState<GitHubConfig>({
    token: '',
    owner: '',
    repo: ''
  });
  const [githubConnected, setGithubConnected] = useState(false);
  const [githubTestingConnection, setGithubTestingConnection] = useState(false);
  const [githubTestResult, setGithubTestResult] = useState<'success' | 'error' | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const settings = await TestStorageService.getIntegrationSettings();
    
    if (settings.jira) {
      setJiraConfig(settings.jira);
      setJiraConnected(true);
    }
    
    if (settings.github) {
      setGithubConfig(settings.github);
      setGithubConnected(true);
      }
    } catch (error) {
      console.error('Error loading integration settings:', error);
    }
  };

  const handleJiraInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setJiraConfig(prev => ({ ...prev, [name]: value }));
  };

  const handleGithubInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setGithubConfig(prev => ({ ...prev, [name]: value }));
  };

  const testJiraConnection = async () => {
    setJiraTestingConnection(true);
    setJiraTestResult(null);
    
    try {
      const success = await IntegrationService.testJiraConnection(jiraConfig);
      setJiraTestResult(success ? 'success' : 'error');
    } catch (error) {
      setJiraTestResult('error');
      console.error('Error testing Jira connection:', error);
    } finally {
      setJiraTestingConnection(false);
    }
  };

  const testGithubConnection = async () => {
    setGithubTestingConnection(true);
    setGithubTestResult(null);
    
    try {
      const success = await IntegrationService.testGitHubConnection(githubConfig);
      setGithubTestResult(success ? 'success' : 'error');
    } catch (error) {
      setGithubTestResult('error');
      console.error('Error testing GitHub connection:', error);
    } finally {
      setGithubTestingConnection(false);
    }
  };

  const saveJiraConfig = async () => {
    try {
      await TestStorageService.saveJiraConfig(jiraConfig);
    setJiraConnected(true);
    setJiraTestResult('success');
    } catch (error) {
      console.error('Error saving Jira config:', error);
      setJiraTestResult('error');
    }
  };

  const saveGithubConfig = async () => {
    try {
      await TestStorageService.saveGitHubConfig(githubConfig);
    setGithubConnected(true);
    setGithubTestResult('success');
    } catch (error) {
      console.error('Error saving GitHub config:', error);
      setGithubTestResult('error');
    }
  };

  const disconnectJira = async () => {
    try {
      await TestStorageService.clearJiraConfig();
    setJiraConnected(false);
    setJiraTestResult(null);
    setJiraConfig({
      url: '',
      apiToken: '',
      email: '',
      project: ''
    });
    } catch (error) {
      console.error('Error disconnecting Jira:', error);
    }
  };

  const disconnectGithub = async () => {
    try {
      await TestStorageService.clearGitHubConfig();
    setGithubConnected(false);
    setGithubTestResult(null);
    setGithubConfig({
      token: '',
      owner: '',
      repo: ''
    });
    } catch (error) {
      console.error('Error disconnecting GitHub:', error);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Integrations</h1>
        <p className="text-muted-foreground">Connect your test management system with external tools</p>
      </div>
      
      <Tabs defaultValue="jira" className="mb-6">
        <TabsList className="mb-6">
          <TabsTrigger value="jira">Jira</TabsTrigger>
          <TabsTrigger value="github">GitHub</TabsTrigger>
        </TabsList>
        
        <TabsContent value="jira">
          <Card>
            <CardHeader>
              <CardTitle>Jira Integration</CardTitle>
              <CardDescription>
                Connect to Jira to create issues from test failures, track test cases, and link test executions.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {jiraTestResult === 'success' && (
                <Alert className="mb-6 bg-green-50 border-green-200">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <AlertTitle>Connection Successful</AlertTitle>
                  <AlertDescription>
                    Your Jira integration is working correctly.
                  </AlertDescription>
                </Alert>
              )}
              
              {jiraTestResult === 'error' && (
                <Alert className="mb-6 bg-red-50 border-red-200">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <AlertTitle>Connection Failed</AlertTitle>
                  <AlertDescription>
                    Could not connect to Jira with the provided credentials. Please check your settings and try again.
                  </AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="url">Jira URL</Label>
                  <Input
                    id="url"
                    name="url"
                    placeholder="https://your-domain.atlassian.net"
                    value={jiraConfig.url}
                    onChange={handleJiraInputChange}
                    readOnly={jiraConnected}
                  />
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    name="email"
                    placeholder="your-email@example.com"
                    value={jiraConfig.email}
                    onChange={handleJiraInputChange}
                    readOnly={jiraConnected}
                  />
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="apiToken">API Token</Label>
                  <Input
                    id="apiToken"
                    name="apiToken"
                    type="password"
                    placeholder="••••••••••••••••"
                    value={jiraConfig.apiToken}
                    onChange={handleJiraInputChange}
                    readOnly={jiraConnected}
                  />
                  {!jiraConnected && (
                    <p className="text-xs text-muted-foreground">
                      You can generate an API token in your{' '}
                      <a 
                        href="https://id.atlassian.com/manage-profile/security/api-tokens" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline inline-flex items-center"
                      >
                        Atlassian Account Settings
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    </p>
                  )}
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="project">Project Key</Label>
                  <Input
                    id="project"
                    name="project"
                    placeholder="TEST"
                    value={jiraConfig.project}
                    onChange={handleJiraInputChange}
                    readOnly={jiraConnected}
                  />
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              {!jiraConnected ? (
                <>
                  <Button variant="outline" onClick={testJiraConnection} disabled={jiraTestingConnection}>
                    {jiraTestingConnection ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Testing Connection
                      </>
                    ) : (
                      'Test Connection'
                    )}
                  </Button>
                  <Button onClick={saveJiraConfig} disabled={jiraTestResult !== 'success'}>
                    Connect
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">
                    Connected to {jiraConfig.url}
                  </p>
                  <Button variant="destructive" onClick={disconnectJira}>
                    Disconnect
                  </Button>
                </>
              )}
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="github">
          <Card>
            <CardHeader>
              <CardTitle>GitHub Integration</CardTitle>
              <CardDescription>
                Connect to GitHub to create issues from test failures, track test cases in your repository, and link to pull requests.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {githubTestResult === 'success' && (
                <Alert className="mb-6 bg-green-50 border-green-200">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <AlertTitle>Connection Successful</AlertTitle>
                  <AlertDescription>
                    Your GitHub integration is working correctly.
                  </AlertDescription>
                </Alert>
              )}
              
              {githubTestResult === 'error' && (
                <Alert className="mb-6 bg-red-50 border-red-200">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <AlertTitle>Connection Failed</AlertTitle>
                  <AlertDescription>
                    Could not connect to GitHub with the provided token. Please check your settings and try again.
                  </AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="token">Personal Access Token</Label>
                  <Input
                    id="token"
                    name="token"
                    type="password"
                    placeholder="ghp_••••••••••••••••"
                    value={githubConfig.token}
                    onChange={handleGithubInputChange}
                    readOnly={githubConnected}
                  />
                  {!githubConnected && (
                    <p className="text-xs text-muted-foreground">
                      You can generate a token in your{' '}
                      <a 
                        href="https://github.com/settings/tokens" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline inline-flex items-center"
                      >
                        GitHub Developer Settings
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    </p>
                  )}
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="owner">Repository Owner</Label>
                  <Input
                    id="owner"
                    name="owner"
                    placeholder="username or organization"
                    value={githubConfig.owner}
                    onChange={handleGithubInputChange}
                    readOnly={githubConnected}
                  />
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="repo">Repository Name</Label>
                  <Input
                    id="repo"
                    name="repo"
                    placeholder="repository-name"
                    value={githubConfig.repo}
                    onChange={handleGithubInputChange}
                    readOnly={githubConnected}
                  />
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              {!githubConnected ? (
                <>
                  <Button variant="outline" onClick={testGithubConnection} disabled={githubTestingConnection}>
                    {githubTestingConnection ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Testing Connection
                      </>
                    ) : (
                      'Test Connection'
                    )}
                  </Button>
                  <Button onClick={saveGithubConfig} disabled={githubTestResult !== 'success'}>
                    <Github className="h-4 w-4 mr-2" />
                    Connect
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">
                    Connected to {githubConfig.owner}/{githubConfig.repo}
                  </p>
                  <Button variant="destructive" onClick={disconnectGithub}>
                    Disconnect
                  </Button>
                </>
              )}
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default IntegrationsPage; 
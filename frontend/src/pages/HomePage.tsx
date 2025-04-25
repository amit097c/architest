import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import InputSection from '@/components/sections/InputSection';
import OutputSection from '@/components/sections/OutputSection';
import StatusSection from '@/components/sections/StatusSection';
import TestResultsSection from '@/components/sections/TestResultsSection';
import ToolsSection from '@/components/sections/ToolsSection';
import { TestStorageService } from '@/lib/storage-service';
import { useArchiTestContext } from '@/context/ArchiTestContext';
import { SavedTest, Collection } from '@/lib/types';

const HomePage: React.FC = () => {
  const {
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
    useJira,
    setUseJira,
    jiraTicketId,
    setJiraTicketId,
    status,
    generateTestScript,
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
    testScript,
    results,
    statusEvents,
    iterations,
    duration,
    statusTestErrors,
    addStatusEvent,
    cancelGeneration
  } = useArchiTestContext();

  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('');
  const [showCollectionDropdown, setShowCollectionDropdown] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      const allCollections = await TestStorageService.getAllCollections();
    setCollections(allCollections);
    } catch (error) {
      console.error('Error loading collections:', error);
    }
  };

  // Function to save the current test to history
  const saveToHistory = async () => {
    // Only save if a test script has been generated
    if (testScript) {
      setLoading(true);

      try {
      const currentStatus = status === 'passed' ? 'passed' as const : 
                          status === 'failed' ? 'failed' as const : 
                          'unknown' as const;
      
        const test: Omit<SavedTest, 'id'> = {
        createdAt: new Date(),
        name: isApiTest 
          ? `API Test - ${apiMethod} ${apiEndpoint}` 
          : `Web Test - ${typeof url === 'string' ? url : url[0]}`,
        url: isApiTest ? apiEndpoint : (isMultiPage ? [url, ...multiPageUrls.filter(Boolean)] : url),
        testSteps,
        framework,
        language,
        testScript,
        status: currentStatus,
        isApiTest,
        apiDetails: isApiTest ? {
          endpoint: apiEndpoint,
          method: apiMethod,
          payload: apiPayload
        } : undefined,
        collectionId: selectedCollectionId || undefined
      };
        console.log(test);
        const savedTest = await TestStorageService.saveTest(test as SavedTest);
        console.log('Saved test:', savedTest);
      alert('Test saved to history');
      setShowCollectionDropdown(false);
      setSelectedCollectionId('');
      } catch (error) {
        console.error('Error saving test:', error);
        alert('Error saving test. Please try again.');
      } finally {
        setLoading(false);
      }
    } else {
      alert('Please generate a test script first');
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Create a Test</h2>
      </div>
      <div className="flex justify-end mb-4 gap-2">
        <div className="relative">
          <Button 
            variant="outline" 
            onClick={() => setShowCollectionDropdown(!showCollectionDropdown)}
            disabled={!testScript || loading}
          >
            {selectedCollectionId 
              ? `Save to: ${collections.find(c => c.id === selectedCollectionId)?.name || 'Selected Collection'}` 
              : "Select Collection"}
          </Button>
          
          {showCollectionDropdown && (
            <div className="absolute right-0 top-full mt-2 w-56 p-2 bg-white border rounded-md shadow-lg z-50">
              <p className="text-sm font-medium pb-2 border-b mb-2">Select Collection</p>
              <div className="max-h-60 overflow-y-auto">
                <div 
                  className={`text-sm p-2 hover:bg-gray-100 rounded cursor-pointer ${!selectedCollectionId ? 'bg-gray-100' : ''}`}
                  onClick={() => {
                    setSelectedCollectionId('');
                    setShowCollectionDropdown(false);
                  }}
                >
                  No Collection (Uncategorized)
                </div>
                {collections.length === 0 ? (
                  <p className="text-sm text-muted-foreground p-2">No collections available</p>
                ) : (
                  <ul className="space-y-1">
                    {collections.map(collection => (
                      <li 
                        key={collection.id}
                        className={`text-sm p-2 hover:bg-gray-100 rounded cursor-pointer ${collection.color} ${selectedCollectionId === collection.id ? 'border border-primary' : ''}`}
                        onClick={() => {
                          setSelectedCollectionId(collection.id || '');
                          setShowCollectionDropdown(false);
                        }}
                      >
                        {collection.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
        
        <Button onClick={saveToHistory} disabled={!testScript || loading}>
          {loading ? 'Saving...' : 'Save Test'}
        </Button>
      </div>

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
            onCancel={cancelGeneration}
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
            isApiTest={isApiTest}
          />

          <ToolsSection />
        </div>
      </div>
    </div>
  );
};

export default HomePage; 
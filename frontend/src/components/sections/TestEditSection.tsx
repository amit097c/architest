/**
 * NOTE: This file has been converted from TestEditSection to TestDetailsSection.
 * The file should be renamed to TestDetailsSection.tsx to match its purpose.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent,
  CardFooter
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SavedTest } from '@/lib/types';
import { TestStorageService } from '@/lib/storage-service';
import OutputSection from '@/components/sections/OutputSection';
import TestIntegrationActions from '@/components/TestIntegrationActions';

const TestDetailsSection: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [test, setTest] = useState<SavedTest | null>(null);
  const [isLoadingTest, setIsLoadingTest] = useState(true);
  const [tag, setTag] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const loadTest = async () => {
      if (id) {
        setIsLoadingTest(true);
        try {
          const savedTest = await TestStorageService.getTestById(id);
          if (savedTest) {
            setTest(savedTest);
          } else {
            navigate('/history');
          }
        } catch (error) {
          console.error('Error loading test:', error);
          navigate('/history');
        } finally {
          setIsLoadingTest(false);
        }
      }
    };
    
    loadTest();
  }, [id, navigate]);

  const handleAddTag = async () => {
    if (!test || !tag.trim()) return;
    
    setLoading(true);
    try {
      await TestStorageService.addTagToTest(test.id || '', tag.trim());
    
      // Update local state
      setTest(prevTest => {
        if (!prevTest) return null;
        
        const tags = prevTest.tags || [];
        return {
          ...prevTest,
          tags: [...tags, tag.trim()]
        };
      });
      
      setTag('');
    } catch (error) {
      console.error('Error adding tag:', error);
      alert('Error adding tag. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveTag = async (tagToRemove: string) => {
    if (!test) return;
    
    setLoading(true);
    try {
      await TestStorageService.removeTagFromTest(test.id || '', tagToRemove);
    
      // Update local state
      setTest(prevTest => {
        if (!prevTest || !prevTest.tags) return prevTest;
        
        return {
          ...prevTest,
          tags: prevTest.tags.filter(t => t !== tagToRemove)
        };
      });
    } catch (error) {
      console.error('Error removing tag:', error);
      alert('Error removing tag. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (isLoadingTest) {
    return (
      <div className="flex justify-center items-center h-64">
        <p>Loading test...</p>
      </div>
    );
  }

  if (!test) {
    return (
      <div className="flex justify-center items-center h-64">
        <p>Test not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Test Details</h2>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/history')}>Back to History</Button>
        </div>
      </div>

      {/* Add integration actions */}
      {test.status === 'failed' && (
        <TestIntegrationActions test={test} />
      )}

      <Card>
        <CardHeader>
          <CardTitle>{test.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-1">Test Type</h3>
              <p className="px-3 py-2 border bg-gray-50 rounded-md">
                {test.isApiTest ? 'API Test' : 'Web Test'}
              </p>
            </div>
            
            {!test.isApiTest ? (
              <div>
                <h3 className="text-sm font-medium mb-1">URL</h3>
                <p className="px-3 py-2 border bg-gray-50 rounded-md">
                  {typeof test.url === 'string' ? test.url : test.url[0]}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium mb-1">API Endpoint</h3>
                  <p className="px-3 py-2 border bg-gray-50 rounded-md">
                    {test.apiDetails?.endpoint}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium mb-1">HTTP Method</h3>
                  <p className="px-3 py-2 border bg-gray-50 rounded-md">
                    {test.apiDetails?.method}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium mb-1">Request Payload</h3>
                  <pre className="px-3 py-2 border bg-gray-50 rounded-md font-mono text-sm overflow-auto max-h-40">
                    {test.apiDetails?.payload}
                  </pre>
                </div>
              </div>
            )}
            
            <div>
              <h3 className="text-sm font-medium mb-1">Test Steps</h3>
              <pre className="px-3 py-2 border bg-gray-50 rounded-md whitespace-pre-wrap">
                {test.testSteps}
              </pre>
            </div>
            
            <div className="flex gap-4">
              <div className="w-1/2">
                <h3 className="text-sm font-medium mb-1">Framework</h3>
                <p className="px-3 py-2 border bg-gray-50 rounded-md">
                  {test.framework}
                </p>
              </div>
              <div className="w-1/2">
                <h3 className="text-sm font-medium mb-1">Language</h3>
                <p className="px-3 py-2 border bg-gray-50 rounded-md">
                  {test.language}
                </p>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium mb-1">Tags</h3>
              <div className="flex flex-wrap gap-2 mb-2">
                {test.tags?.map((tag) => (
                  <div 
                    key={tag} 
                    className="bg-gray-100 px-2 py-1 rounded-md flex items-center text-sm"
                  >
                    {tag}
                    <button 
                      className="ml-1 text-red-500 hover:text-red-700"
                      onClick={() => handleRemoveTag(tag)}
                      disabled={loading}
                    >
                      ×
                    </button>
                  </div>
                ))}
                {(!test.tags || test.tags.length === 0) && (
                  <p className="text-gray-500 italic">No tags</p>
                )}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="flex-1 px-3 py-2 border rounded-md"
                  value={tag}
                  onChange={(e) => setTag(e.target.value)}
                  placeholder="Add a tag"
                  disabled={loading}
                />
                <Button onClick={handleAddTag} disabled={!tag.trim() || loading}>
                  Add
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button variant="outline" onClick={() => navigate('/history')}>
            Back to History
          </Button>
        </CardFooter>
      </Card>
      
      <OutputSection
        testScript={test.testScript}
        iterations={0}
        addStatusEvent={() => {}}
      />
    </div>
  );
};

export default TestDetailsSection; 
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent,
  CardFooter
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { SavedTest, Collection } from '@/lib/types';
import { TestStorageService } from '@/lib/storage-service';

const HistorySection: React.FC<{ collectionId?: string }> = ({ collectionId }) => {
  const [savedTests, setSavedTests] = useState<SavedTest[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed'>('all');
  const [collectionFilter, setCollectionFilter] = useState<'all' | 'uncategorized' | 'in-collection'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTestId, setSelectedTestId] = useState<string | null>(null);
  const [showCollectionDropdown, setShowCollectionDropdown] = useState<{ [key: string]: boolean }>({});
  const [loading, setLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        await Promise.all([loadTests(), loadCollections()]);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [collectionId]);

  const loadTests = async () => {
    try {
      let tests;
      if (collectionId) {
        // If viewing a specific collection, only show tests in that collection
        tests = await TestStorageService.getTestsByCollectionId(collectionId);
      } else {
        // Otherwise, show all tests
        tests = await TestStorageService.getAllTests();
      }
      setSavedTests(tests);
    } catch (error) {
      console.error('Error loading tests:', error);
    }
  };

  const loadCollections = async () => {
    try {
      const allCollections = await TestStorageService.getAllCollections();
      setCollections(allCollections);
    } catch (error) {
      console.error('Error loading collections:', error);
    }
  };

  const handleDeleteTest = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this test?')) {
      setLoading(true);
      try {
        await TestStorageService.deleteTest(id);
        setSavedTests(prev => prev.filter(test => test.id !== id));
      } catch (error) {
        console.error('Error deleting test:', error);
        alert('Error deleting test. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleEditTest = (id: string) => {
    navigate(`/edit/${id}`);
  };

  const toggleCollectionDropdown = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setShowCollectionDropdown(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleAddToCollection = async (testId: string, collectionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setLoading(true);
    try {
      await TestStorageService.addTestToCollection(testId, collectionId);
      
      // Hide dropdown
      setShowCollectionDropdown(prev => ({
        ...prev,
        [testId]: false
      }));
      
      // If we're viewing a specific collection, refresh to show only tests in that collection
      if (collectionId) {
        await loadTests();
      } else {
        // Refresh all tests to update collectionId
        await loadTests();
      }
    } catch (error) {
      console.error('Error adding test to collection:', error);
      alert('Error adding test to collection. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filteredTests = savedTests.filter(test => {
    // Apply status filter
    if (filter !== 'all' && test.status !== filter) return false;
    
    // Apply collection filter (when not in a specific collection view)
    if (!collectionId) {
      if (collectionFilter === 'uncategorized' && test.collectionId) return false;
      if (collectionFilter === 'in-collection' && !test.collectionId) return false;
    }
    
    // Apply search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return (
        test.name.toLowerCase().includes(searchLower) || 
        (typeof test.url === 'string' && test.url.toLowerCase().includes(searchLower)) ||
        test.testSteps.toLowerCase().includes(searchLower) ||
        (test.tags && test.tags.some(tag => tag.toLowerCase().includes(searchLower)))
      );
    }
    
    return true;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'bg-green-50 text-green-500';
      case 'failed': return 'bg-red-50 text-red-500';
      default: return 'bg-gray-50 text-gray-500';
    }
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const getCollectionName = (collectionId: string) => {
    const collection = collections.find(c => c.id === collectionId);
    return collection ? collection.name : 'Unknown';
  };

  // Safely get test id or return an empty string
  const ensureTestId = (test: SavedTest): string => {
    return test.id || '';
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p>Loading test history...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Test History</h2>
      </div>

      <div className="flex items-center space-x-4 mb-4">
        <div className="flex-grow">
          <input
            type="text"
            placeholder="Search tests..."
            className="w-full px-3 py-2 border rounded-md"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            disabled={loading}
          />
        </div>
        <Tabs defaultValue="all" onValueChange={(value) => setFilter(value as any)}>
          <TabsList>
            <TabsTrigger value="all" disabled={loading}>All</TabsTrigger>
            <TabsTrigger value="passed" disabled={loading}>Passed</TabsTrigger>
            <TabsTrigger value="failed" disabled={loading}>Failed</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {!collectionId && (
        <div className="mb-4">
          <Tabs defaultValue="all" onValueChange={(value) => setCollectionFilter(value as any)}>
            <TabsList className="w-full">
              <TabsTrigger value="all" className="flex-1" disabled={loading}>All Tests</TabsTrigger>
              <TabsTrigger value="uncategorized" className="flex-1" disabled={loading}>Uncategorized</TabsTrigger>
              <TabsTrigger value="in-collection" className="flex-1" disabled={loading}>In Collections</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      )}

      {filteredTests.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            {searchTerm || filter !== 'all' || collectionFilter !== 'all'
              ? 'No tests match your search criteria' 
              : 'No saved tests yet. Start by creating a new test!'}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredTests.map(test => {
            const testId = ensureTestId(test);
            return (
              <Card 
                key={testId} 
                className="cursor-pointer hover:border-primary/20 transition-all"
                onClick={() => handleEditTest(testId)}
              >
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle>{test.name}</CardTitle>
                      <CardDescription className="mt-1">
                        {typeof test.url === 'string' 
                          ? test.url 
                          : (test.url && test.url.length > 0 ? test.url[0] : 'No URL')}
                      </CardDescription>
                      {test.collectionId && (
                        <Badge variant="secondary" className="mt-2">
                          Collection: {getCollectionName(test.collectionId)}
                        </Badge>
                      )}
                    </div>
                    <Badge variant="outline" className={getStatusColor(test.status)}>
                      {test.status.charAt(0).toUpperCase() + test.status.slice(1)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col space-y-2">
                    <div className="text-sm text-muted-foreground">
                      <span className="font-medium">Framework:</span> {test.framework}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <span className="font-medium">Language:</span> {test.language}
                    </div>
                    {test.isApiTest && (
                      <div className="text-sm text-muted-foreground">
                        <span className="font-medium">API Test:</span> {test.apiDetails?.method} {test.apiDetails?.endpoint}
                      </div>
                    )}
                    {test.tags && test.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {test.tags.map(tag => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between items-center">
                  <div className="text-sm text-muted-foreground">
                    {formatDate(test.createdAt)}
                  </div>
                  <div className="flex space-x-2">
                    <div className="relative">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={(e) => toggleCollectionDropdown(testId, e)}
                        disabled={loading}
                      >
                        {test.collectionId ? 'Move' : 'Add to Collection'}
                      </Button>
                      
                      {showCollectionDropdown[testId] && (
                        <div className="absolute right-0 top-full mt-2 w-56 p-2 bg-white border rounded-md shadow-lg z-50">
                          <p className="text-sm font-medium pb-2 border-b mb-2">Select Collection</p>
                          <div className="max-h-60 overflow-y-auto">
                            {collections.length === 0 ? (
                              <p className="text-sm text-muted-foreground p-2">No collections available</p>
                            ) : (
                              <ul className="space-y-1">
                                {collections.map(collection => (
                                  <li 
                                    key={collection.id}
                                    className="text-sm p-2 hover:bg-gray-100 rounded cursor-pointer"
                                    onClick={(e) => handleAddToCollection(testId, collection.id, e)}
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
                    
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={(e) => handleDeleteTest(testId, e)}
                      disabled={loading}
                    >
                      Delete
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default HistorySection; 
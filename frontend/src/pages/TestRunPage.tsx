import React, { useState, useEffect } from 'react';
import { SavedTest, Collection } from '@/lib/types';
import { TestStorageService } from '@/lib/storage-service';
import BulkTestRunner from '@/components/BulkTestRunner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { CheckCircle2, AlertCircle, Clock } from 'lucide-react';

const TestRunPage: React.FC = () => {
  const [tests, setTests] = useState<SavedTest[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedTestIds, setSelectedTestIds] = useState<string[]>([]);
  const [filter, setFilter] = useState<'all' | 'collection' | 'uncategorized'>('all');
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const allTests = await TestStorageService.getAllTests();
      const allCollections = await TestStorageService.getAllCollections();
    setTests(allTests);
    setCollections(allCollections);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const getFilteredTests = () => {
    if (filter === 'all') {
      return tests;
    } else if (filter === 'uncategorized') {
      return tests.filter(test => !test.collectionId);
    } else if (filter === 'collection' && selectedCollection) {
      return tests.filter(test => test.collectionId === selectedCollection);
    }
    return [];
  };

  const getSelectedTests = () => {
    return tests.filter(test => test.id && selectedTestIds.includes(test.id));
  };

  const handleSelectAll = () => {
    const filteredTests = getFilteredTests();
    if (selectedTestIds.length === filteredTests.length) {
      // Deselect all
      setSelectedTestIds([]);
    } else {
      // Select all filtered tests with defined IDs
      setSelectedTestIds(filteredTests.map(test => test.id || '').filter(id => id !== ''));
    }
  };

  const handleSelectTest = (testId: string) => {
    if (selectedTestIds.includes(testId)) {
      setSelectedTestIds(prev => prev.filter(id => id !== testId));
    } else {
      setSelectedTestIds(prev => [...prev, testId]);
    }
  };

  const handleTestsComplete = () => {
    loadData(); // Refresh data after tests complete
  };

  const getStatusIcon = (status: 'passed' | 'failed' | 'unknown') => {
    switch (status) {
      case 'passed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
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

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Test Runner</h1>
        <p className="text-muted-foreground">Run and manage your test executions</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Test Selection Panel */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Select Tests</CardTitle>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleSelectAll}
                >
                  {selectedTestIds.length === getFilteredTests().length ? 'Deselect All' : 'Select All'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="all" className="mb-6" onValueChange={(v) => setFilter(v as any)}>
                <TabsList className="mb-4">
                  <TabsTrigger value="all">All Tests</TabsTrigger>
                  <TabsTrigger value="collection">By Collection</TabsTrigger>
                  <TabsTrigger value="uncategorized">Uncategorized</TabsTrigger>
                </TabsList>
                
                {filter === 'collection' && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {collections.map(collection => (
                      <Button
                        key={collection.id}
                        variant={selectedCollection === collection.id ? 'default' : 'outline'}
                        size="sm"
                        className={`${collection.color || ''}`}
                        onClick={() => setSelectedCollection(collection.id || null)}
                      >
                        {collection.name}
                      </Button>
                    ))}
                  </div>
                )}
              </Tabs>
              
              <div className="space-y-2 max-h-[400px] overflow-auto">
                {getFilteredTests().length === 0 ? (
                  <div className="text-center p-6 border rounded-md">
                    <p className="text-muted-foreground">No tests found</p>
                  </div>
                ) : (
                  getFilteredTests().map(test => (
                    <div
                      key={test.id}
                      className={`flex items-center p-3 border rounded-md ${
                        test.id && selectedTestIds.includes(test.id) ? 'bg-blue-50 border-blue-200' : ''
                      }`}
                    >
                      <Checkbox 
                        id={`test-${test.id}`}
                        checked={test.id ? selectedTestIds.includes(test.id) : false}
                        onCheckedChange={() => test.id && handleSelectTest(test.id)}
                        className="mr-3"
                      />
                      <div className="flex-1 min-w-0">
                        <label htmlFor={`test-${test.id}`} className="flex items-center cursor-pointer">
                          <div className="truncate">
                            <div className="font-medium">{test.name}</div>
                            <div className="text-xs text-muted-foreground">
                              {test.framework} - {test.language} - Last run: {test.lastRun ? formatDate(new Date(test.lastRun)) : 'Never'}
                            </div>
                          </div>
                        </label>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="flex items-center gap-1">
                          {getStatusIcon(test.status)}
                          {test.status.charAt(0).toUpperCase() + test.status.slice(1)}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Runner Panel */}
        <div>
          <BulkTestRunner tests={getSelectedTests()} onTestsComplete={handleTestsComplete} />
        </div>
      </div>
    </div>
  );
};

export default TestRunPage; 
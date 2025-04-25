import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TestStorageService } from '@/lib/storage-service';
import { SavedTest, Collection } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const DashboardPage: React.FC = () => {
  const [tests, setTests] = useState<SavedTest[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [recentTests, setRecentTests] = useState<SavedTest[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const allTests = await TestStorageService.getAllTests();
      const allCollections = await TestStorageService.getAllCollections();
    
    setTests(allTests);
    setCollections(allCollections);
    
    // Get recent tests (up to 5)
    setRecentTests(
      [...allTests]
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
        .slice(0, 5)
    );
      
    // Get all collections
    setCollections(allCollections);
      
    // Sort tests by last run date if available
    /*const lastRun = [...allTests].sort((a, b) => {
      const dateA = a.lastRun ? new Date(a.lastRun).getTime() : 0;
      const dateB = b.lastRun ? new Date(b.lastRun).getTime() : 0;
      return dateB - dateA;
    })[0];*/
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const getTestCountByStatus = (status: 'passed' | 'failed' | 'unknown') => {
    return tests.filter(test => test.status === status).length;
  };

  const getTestCountByFramework = (framework: string) => {
    return tests.filter(test => test.framework === framework).length;
  };

  const getTestCountByLanguage = (language: string) => {
    return tests.filter(test => test.language === language).length;
  };

  const getUncategorizedTestCount = () => {
    return tests.filter(test => !test.collectionId).length;
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'bg-green-50 text-green-500';
      case 'failed': return 'bg-red-50 text-red-500';
      default: return 'bg-gray-50 text-gray-500';
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Overview</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Total Tests Card */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Tests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{tests.length}</div>
          </CardContent>
        </Card>
        
        {/* Passed Tests Card */}
        <Card className="bg-green-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Passed Tests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-700">{getTestCountByStatus('passed')}</div>
          </CardContent>
        </Card>
        
        {/* Failed Tests Card */}
        <Card className="bg-red-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Failed Tests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-700">{getTestCountByStatus('failed')}</div>
          </CardContent>
        </Card>
        
        {/* Collections Card */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Collections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{collections.length}</div>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Framework Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Framework Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Playwright</span>
                <div className="flex items-center gap-2">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-purple-600 h-2.5 rounded-full" 
                      style={{ width: `${tests.length > 0 ? (getTestCountByFramework('playwright') / tests.length) * 100 : 0}%` }}
                    ></div>
                  </div>
                  <span className="text-sm">{getTestCountByFramework('playwright')}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>Cypress</span>
                <div className="flex items-center gap-2">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-cyan-600 h-2.5 rounded-full" 
                      style={{ width: `${tests.length > 0 ? (getTestCountByFramework('cypress') / tests.length) * 100 : 0}%` }}
                    ></div>
                  </div>
                  <span className="text-sm">{getTestCountByFramework('cypress')}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>Selenium</span>
                <div className="flex items-center gap-2">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-green-600 h-2.5 rounded-full" 
                      style={{ width: `${tests.length > 0 ? (getTestCountByFramework('selenium') / tests.length) * 100 : 0}%` }}
                    ></div>
                  </div>
                  <span className="text-sm">{getTestCountByFramework('selenium')}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Language Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Language Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Python</span>
                <div className="flex items-center gap-2">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full" 
                      style={{ width: `${tests.length > 0 ? (getTestCountByLanguage('python') / tests.length) * 100 : 0}%` }}
                    ></div>
                  </div>
                  <span className="text-sm">{getTestCountByLanguage('python')}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>JavaScript</span>
                <div className="flex items-center gap-2">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-yellow-500 h-2.5 rounded-full" 
                      style={{ width: `${tests.length > 0 ? (getTestCountByLanguage('javascript') / tests.length) * 100 : 0}%` }}
                    ></div>
                  </div>
                  <span className="text-sm">{getTestCountByLanguage('javascript')}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>Java</span>
                <div className="flex items-center gap-2">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-red-500 h-2.5 rounded-full" 
                      style={{ width: `${tests.length > 0 ? (getTestCountByLanguage('java') / tests.length) * 100 : 0}%` }}
                    ></div>
                  </div>
                  <span className="text-sm">{getTestCountByLanguage('java')}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button className="w-full" onClick={() => navigate('/create')}>
              Create New Test
            </Button>
            <Button variant="outline" className="w-full" onClick={() => navigate('/collections')}>
              Manage Collections
            </Button>
            <Button variant="outline" className="w-full" onClick={() => navigate('/history')}>
              View All Tests
            </Button>
            <Button variant="outline" className="w-full" onClick={() => navigate('/integrations')}>
              Configure Integrations
            </Button>
          </CardContent>
        </Card>
        
        {/* Recent Tests */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Tests</CardTitle>
            <Button variant="link" className="p-0 h-auto" onClick={() => navigate('/history')}>
              View All
            </Button>
          </CardHeader>
          <CardContent>
            {recentTests.length === 0 ? (
              <p className="text-muted-foreground text-center py-6">No tests created yet</p>
            ) : (
              <div className="space-y-4">
                {recentTests.map(test => (
                  <div 
                    key={test.id} 
                    className="flex items-center justify-between p-3 border rounded-md cursor-pointer hover:bg-gray-50"
                    onClick={() => navigate(`/edit/${test.id}`)}
                  >
                    <div>
                      <h3 className="font-medium">{test.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(test.createdAt)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={getStatusColor(test.status)}>
                        {test.status.charAt(0).toUpperCase() + test.status.slice(1)}
                      </Badge>
                      <Badge variant="secondary">
                        {test.framework}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Collection Distribution */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Collection Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-gray-100 p-4 rounded-md">
              <h3 className="font-medium mb-2">Uncategorized</h3>
              <p className="text-3xl font-bold">{getUncategorizedTestCount()}</p>
            </div>
            
            {collections.map(collection => (
              <div 
                key={collection.id} 
                className={`${collection.color} p-4 rounded-md cursor-pointer hover:shadow-md transition-shadow`}
                onClick={() => navigate(`/collection/${collection.id}`)}
              >
                <h3 className="font-medium mb-2">{collection.name}</h3>
                <p className="text-3xl font-bold">
                  {tests.filter(test => test.collectionId === collection.id).length}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardPage; 
import React, { useState } from 'react';
import { Play, CheckCircle2, AlertCircle, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SavedTest } from '@/lib/types';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { TestStorageService } from '@/lib/storage-service';

interface BulkTestRunnerProps {
  tests: SavedTest[];
  onTestsComplete?: () => void;
}

const BulkTestRunner: React.FC<BulkTestRunnerProps> = ({ tests, onTestsComplete }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [currentTestIndex, setCurrentTestIndex] = useState<number>(-1);
  const [results, setResults] = useState<Record<string, 'passed' | 'failed' | 'pending'>>({});
  const [progress, setProgress] = useState(0);

  const runTests = async () => {
    if (tests.length === 0) return;
    
    setIsRunning(true);
    setProgress(0);
    
    // Initialize all tests as pending
    const initialResults: Record<string, 'passed' | 'failed' | 'pending'> = {};
    tests.forEach(test => {
      if (test.id && typeof test.id === 'string') {
      initialResults[test.id] = 'pending';
      }
    });
    setResults(initialResults);
    
    for (let i = 0; i < tests.length; i++) {
      setCurrentTestIndex(i);
      setProgress(Math.round((i / tests.length) * 100));
      
      const test = tests[i];
      
      // Skip tests without IDs
      if (!test.id || typeof test.id !== 'string') continue;
      
      // Simulate test execution with a random delay
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
      
      // Randomly determine if test passes (for demo)
      const passed = Math.random() > 0.3;
      
      // Update test status
      const updatedTest: SavedTest = {
        ...test,
        status: passed ? 'passed' : 'failed',
        lastRun: new Date()
      };
      
      try {
        const savedTest = await TestStorageService.saveTest(updatedTest);
        console.log('Saved test:', savedTest);
      
        // Update results using the returned test ID
        if (savedTest && savedTest.id && typeof savedTest.id === 'string') {
      setResults(prev => ({
        ...prev,
            [savedTest.id as string]: passed ? 'passed' : 'failed'
      }));
        }
      } catch (error) {
        console.error('Error saving test result:', error);
      }
    }
    
    setProgress(100);
    setIsRunning(false);
    setCurrentTestIndex(-1);
    
    if (onTestsComplete) {
      onTestsComplete();
    }
  };

  const getPassedCount = () => {
    return Object.values(results).filter(status => status === 'passed').length;
  };

  const getFailedCount = () => {
    return Object.values(results).filter(status => status === 'failed').length;
  };

  const getStatusBadge = (status: 'passed' | 'failed' | 'pending') => {
    switch (status) {
      case 'passed':
        return <Badge variant="outline" className="bg-green-50 text-green-500">Passed</Badge>;
      case 'failed':
        return <Badge variant="outline" className="bg-red-50 text-red-500">Failed</Badge>;
      case 'pending':
        return <Badge variant="outline" className="bg-gray-50 text-gray-500">Pending</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Bulk Test Runner</CardTitle>
          {Object.keys(results).length > 0 && (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>{getPassedCount()}</span>
              </div>
              <div className="flex items-center gap-1">
                <AlertCircle className="h-4 w-4 text-red-500" />
                <span>{getFailedCount()}</span>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isRunning ? (
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium">
                Running {currentTestIndex + 1} of {tests.length}...
              </p>
              <span className="text-sm text-muted-foreground">{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        ) : (
          <div className="text-center text-muted-foreground py-4">
            {Object.keys(results).length > 0 ? (
              <p>Test run complete. Check results below.</p>
            ) : (
              <p>Select tests to run and click the Run Tests button.</p>
            )}
          </div>
        )}

        {tests.length > 0 && (
          <div className="space-y-2 mt-4 max-h-64 overflow-auto">
            {tests.map((test, index) => (
              <div 
                key={test.id ? test.id.toString() : index} 
                className={`flex items-center justify-between p-3 border rounded-md ${
                  currentTestIndex === index ? 'bg-blue-50 border-blue-200' : ''
                }`}
              >
                <div className="truncate">
                  <p className="font-medium truncate">{test.name}</p>
                  <p className="text-xs text-muted-foreground">{test.framework} - {test.language}</p>
                </div>
                <div>
                  {test.id && typeof test.id === 'string' && results[test.id] 
                    ? getStatusBadge(results[test.id]) 
                    : <Badge variant="outline">Not Run</Badge>
                  }
                </div>
              </div>
            ))}
          </div>
        )}

        {tests.length === 0 && (
          <div className="border rounded-md p-8 text-center">
            <p className="text-muted-foreground">No tests selected</p>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            {tests.length} test{tests.length !== 1 ? 's' : ''} selected
          </p>
        </div>
        <div className="flex gap-2">
          {Object.keys(results).length > 0 && !isRunning && (
            <Button variant="outline" onClick={runTests} disabled={isRunning} className="gap-2">
              <RotateCcw className="h-4 w-4" />
              Rerun Tests
            </Button>
          )}
          <Button onClick={runTests} disabled={isRunning || tests.length === 0} className="gap-2">
            <Play className="h-4 w-4" />
            Run Tests
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default BulkTestRunner; 
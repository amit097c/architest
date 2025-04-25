import React, { useState, useEffect, useRef } from 'react';
import { Play, AlertCircle, CheckCircle2, Clock, StopCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SavedTest } from '@/lib/types';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TestStorageService } from '@/lib/storage-service';

interface TestRunnerProps {
  test: SavedTest;
  onTestComplete?: (updatedTest: SavedTest) => void;
}

const TestRunner: React.FC<TestRunnerProps> = ({ test, onTestComplete }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [currentStatus, setCurrentStatus] = useState<'idle' | 'running' | 'passed' | 'failed'>('idle');
  const [executionTime, setExecutionTime] = useState(0);
  const [runningTestId, setRunningTestId] = useState<string | null>(null);
  const statusCheckInterval = useRef<NodeJS.Timeout | null>(null);
  const outputRef = useRef<HTMLPreElement>(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (statusCheckInterval.current) {
        clearInterval(statusCheckInterval.current);
      }
    };
  }, []);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const runTest = async () => {
    setIsRunning(true);
    setCurrentStatus('running');
    setOutput([]);
    setExecutionTime(0);

    try {
      // Start the test execution
      const result = await TestStorageService.runTest(test);
      setRunningTestId(result.id);
      
      // Set up interval to check status
      statusCheckInterval.current = setInterval(checkTestStatus, 1000);
    } catch (error) {
      console.error('Error starting test:', error);
      setOutput(prev => [...prev, `Error starting test: ${error}`]);
      setCurrentStatus('failed');
      setIsRunning(false);
    }
  };

  const checkTestStatus = async () => {
    if (!runningTestId) return;

    try {
      const status = await TestStorageService.getTestStatus(runningTestId);
      
      // Update UI with latest status
      setOutput(status.output);
      setExecutionTime(status.execution_time);
      
      // Check if test is complete
      if (status.status === 'passed' || status.status === 'failed') {
        setCurrentStatus(status.status as 'passed' | 'failed');
        setIsRunning(false);
        
        if (statusCheckInterval.current) {
          clearInterval(statusCheckInterval.current);
          statusCheckInterval.current = null;
        }
        
        // Update test status
        const updatedTest: SavedTest = {
          ...test,
          status: status.status,
          lastRun: new Date()
        };
        
        try {
          const savedTest = await TestStorageService.saveTest(updatedTest);
          
          if (onTestComplete) {
            onTestComplete(savedTest);
          }
        } catch (error) {
          console.error('Error saving test result:', error);
        }
      }
    } catch (error) {
      console.error('Error checking test status:', error);
      setOutput(prev => [...prev, `Error checking test status: ${error}`]);
      setCurrentStatus('failed');
      setIsRunning(false);
      
      if (statusCheckInterval.current) {
        clearInterval(statusCheckInterval.current);
        statusCheckInterval.current = null;
      }
    }
  };

  const cancelTest = async () => {
    if (!runningTestId) return;
    
    try {
      await TestStorageService.cancelTest(runningTestId);
      setOutput(prev => [...prev, "Test execution cancelled by user"]);
      setCurrentStatus('failed');
      setIsRunning(false);
      
      if (statusCheckInterval.current) {
        clearInterval(statusCheckInterval.current);
        statusCheckInterval.current = null;
      }
      
      // Update test status
      const updatedTest: SavedTest = {
        ...test,
        status: 'failed',
        lastRun: new Date()
      };
      
      const savedTest = await TestStorageService.saveTest(updatedTest);
      
      if (onTestComplete) {
        onTestComplete(savedTest);
      }
    } catch (error) {
      console.error('Error cancelling test:', error);
    }
  };

  const getStatusIcon = () => {
    switch (currentStatus) {
      case 'running':
        return <Clock className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'passed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = () => {
    switch (currentStatus) {
      case 'running':
        return <Badge variant="outline" className="bg-blue-50 text-blue-500">Running</Badge>;
      case 'passed':
        return <Badge variant="outline" className="bg-green-50 text-green-500">Passed</Badge>;
      case 'failed':
        return <Badge variant="outline" className="bg-red-50 text-red-500">Failed</Badge>;
      default:
        return <Badge variant="outline">Not Run</Badge>;
    }
  };

  const formatExecutionTime = () => {
    if (executionTime < 60) {
      return `${executionTime.toFixed(1)}s`;
    } else {
      const minutes = Math.floor(executionTime / 60);
      const seconds = Math.floor(executionTime % 60);
      return `${minutes}m ${seconds}s`;
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-xl font-medium">Test Runner</CardTitle>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent>
        {isRunning && (
          <div className="mb-4">
            <div className="flex gap-2 mb-2 items-center">
              <Skeleton className="h-4 w-4 rounded-full animate-pulse bg-blue-200" />
              <p className="text-sm text-blue-500">Test in progress... {formatExecutionTime()}</p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse"></div>
            </div>
          </div>
        )}
        
        {output.length > 0 && (
          <pre 
            ref={outputRef}
            className="bg-gray-50 p-3 rounded text-sm font-mono h-64 overflow-auto border"
          >
            {output.join('\n')}
          </pre>
        )}
        
        {output.length === 0 && !isRunning && (
          <div className="flex items-center justify-center h-64 bg-gray-50 rounded border">
            <div className="text-center text-muted-foreground">
              <Play className="h-12 w-12 mx-auto mb-2 opacity-20" />
              <p>Run the test to see execution output</p>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="flex items-center">
          {getStatusIcon()}
          <span className="ml-2 text-sm text-muted-foreground">
            {test.lastRun ? `Last run: ${new Date(test.lastRun).toLocaleString()}` : 'Not run yet'}
          </span>
        </div>
        {isRunning ? (
          <Button 
            onClick={cancelTest} 
            variant="destructive"
            className="gap-2"
          >
            <StopCircle className="h-4 w-4" />
            Cancel
          </Button>
        ) : (
          <Button 
            onClick={runTest} 
            className="gap-2"
          >
            <Play className="h-4 w-4" />
            Run Test
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};

export default TestRunner;
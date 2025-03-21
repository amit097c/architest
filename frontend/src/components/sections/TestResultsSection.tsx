import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, AlertCircle } from "lucide-react";

interface TestResultsProps {
  results: {
    status: 'passed' | 'failed';
    message?: string;
    errorDetails?: string;
    iterations?: number;
  } | null;
}

const TestResultsSection: React.FC<TestResultsProps> = ({ results }) => {
  if (!results) return null;

  return (
    <Card>
    <CardHeader className="pb-2">
      <CardTitle className="flex items-center">
        {results.status === "passed" ? (
          <>
            <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
            <span>Test Results - Passed</span>
          </>
        ) : (
          <>
            <AlertCircle className="mr-2 h-5 w-5 text-red-500" />
            <span>Test Results - Failed</span>
          </>
        )}
      </CardTitle>
    </CardHeader>
    <CardContent>
      <Alert variant={results.status === "passed" ? "default" : "destructive"}>
        <AlertTitle>
          {results.status === "passed" ? "Success" : "Error"}
        </AlertTitle>
        <AlertDescription>
          {results.message}
          {results.errorDetails && (
            <div className="mt-2 p-2 bg-red-50 rounded text-sm break-words overflow-hidden max-w-full whitespace-pre-wrap">
              {results.errorDetails}
            </div>
          )}
          {results.iterations && (
            <div className="mt-2 text-sm text-muted-foreground">
              Tests completed after {results.iterations} iteration{results.iterations !== 1 ? 's' : ''}
            </div>
          )}
        </AlertDescription>
      </Alert>
    </CardContent>
  </Card>
  );
};

export default TestResultsSection;
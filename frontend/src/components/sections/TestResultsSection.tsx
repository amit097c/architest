import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Check, X, AlertCircle } from "lucide-react";

interface TestResultsProps {
  results: {
    status: 'passed' | 'failed';
    message?: string;
    errorDetails?: string;
  } | null;
  duration: number;
}

const TestResultsSection: React.FC<TestResultsProps> = ({ results, duration }) => {
  if (!results) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-medium">Test Results</CardTitle>
        <span className="text-sm text-muted-foreground">
          Duration: {duration}ms
        </span>
      </CardHeader>
      <CardContent>
        <div className={`p-4 rounded-md ${
          results.status === 'passed' 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex items-center">
            {results.status === 'passed' ? (
              <Check className="h-5 w-5 text-green-500 mr-2" />
            ) : (
              <X className="h-5 w-5 text-red-500 mr-2" />
            )}
            <span className={`font-medium ${
              results.status === 'passed' ? 'text-green-700' : 'text-red-700'
            }`}>
              {results.message}
            </span>
          </div>
          {results.errorDetails && (
            <div className="mt-2 flex items-start">
              <AlertCircle className="h-5 w-5 text-red-500 mr-2 mt-0.5" />
              <pre className="text-sm text-red-700 whitespace-pre-wrap">
                {results.errorDetails}
              </pre>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default TestResultsSection;
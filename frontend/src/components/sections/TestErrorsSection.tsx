import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

interface TestErrorsProp {
    testErrors: {
      message?: string;
    } | null;
}

const TestErrorsSection: React.FC<TestErrorsProp> = ({ testErrors }) => {
  if (!testErrors) return null;

  return (
    <Card className="max-w-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center">
          <AlertCircle className="mr-2 h-5 w-5 text-red-500" />
          <span>Errors:</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Alert variant="destructive">
          <AlertDescription className="w-full">
            {/* Replace ScrollArea with a regular div */}
            <div className="h-[200px] w-full overflow-auto rounded-md">
              <div className="mt-2 p-2 bg-red-50 rounded font-mono w-max min-w-full">
                <pre className="text-sm whitespace-pre overflow-auto max-w-none">
                  {testErrors.message}
                </pre>
              </div>
            </div>
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
};

export default TestErrorsSection;

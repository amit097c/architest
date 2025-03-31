import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Copy, Save } from "lucide-react";

interface OutputSectionProps {
  testScript: string;
  iterations: number;
  addStatusEvent: (type: "info" | "success" | "error" | "warning", message: string, details?: string) => void;
}

const OutputSection: React.FC<OutputSectionProps> = ({
  testScript,
  iterations,
  addStatusEvent
}) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle>Generated Test Script</CardTitle>
          <CardDescription>
            {iterations > 0 ? `Iteration ${iterations}` : "AI-generated test script based on your inputs"}
          </CardDescription>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="icon"
            disabled={!testScript}
            onClick={() => {
              navigator.clipboard.writeText(testScript);
              addStatusEvent("info", "Test script copied to clipboard");
            }}
            style={{ cursor: "pointer" }}
          >
            <Copy className="h-4 w-4" />
            
          </Button>
          <Button
            variant="outline"
            size="icon"
            disabled={!testScript}
            onClick={() => {
              addStatusEvent("info", "Test script saved");
            }}
            style={{ cursor: "pointer" }}
          >
            <Save className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-80 w-full rounded-md border bg-gray-100">
          {testScript ? (
            <pre className="p-4 text-sm whitespace-pre-wrap break-words overflow-auto font-mono">
              <code>{testScript}</code>
            </pre>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <p>Your generated test script will appear here</p>
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default OutputSection;
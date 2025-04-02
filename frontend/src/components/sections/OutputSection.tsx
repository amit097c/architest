import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Copy, Save } from "lucide-react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
  // Function to determine language based on file extension or content
  const getLanguage = (code: string): string => {
    if (code.includes('from playwright import')) return 'python';
    if (code.includes('import { test }')) return 'typescript';
    if (code.includes('import org.openqa.selenium')) return 'java';
    return 'javascript';
  };

  const syntaxTheme = {
    ...oneLight,
    'pre[class*="language-"]': {
      ...oneLight['pre[class*="language-"]'],
      background: 'transparent',
    },
    'code[class*="language-"]': {
      ...oneLight['code[class*="language-"]'],
      background: 'transparent',
    }
  };

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
        <div className="h-80 w-full overflow-auto rounded-md w-full rounded-md border">
          <div className="w-max min-w-full">
            <pre className="text-sm whitespace-pre overflow-auto max-w-none">
              {testScript ? (
                <div className="p-4">
                  <SyntaxHighlighter
                    language={getLanguage(testScript)}
                    style={syntaxTheme}
                    customStyle={{
                      margin: 0,
                      fontSize: '0.875rem',
                      backgroundColor: 'transparent',
                    }}
                    wrapLines={true}
                    showLineNumbers={true}
                  >
                    {testScript}
                  </SyntaxHighlighter>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <p>Your generated test script will appear here</p>
                </div>
              )}
            </pre>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default OutputSection;
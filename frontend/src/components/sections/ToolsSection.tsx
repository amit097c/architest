import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Play, Globe, FileText, Download } from "lucide-react";

const ToolsSection: React.FC = () => {
  return (
    <Tabs defaultValue="execution">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="execution">
          <Play className="mr-2 h-4 w-4" />
          Execution
        </TabsTrigger>
        <TabsTrigger value="browser">
          <Globe className="mr-2 h-4 w-4" />
          Browser
        </TabsTrigger>
        <TabsTrigger value="reports">
          <FileText className="mr-2 h-4 w-4" />
          Reports
        </TabsTrigger>
      </TabsList>

      <TabsContent value="execution" className="p-4 border rounded-md mt-2">
        <h3 className="text-sm font-medium mb-2">Execution Settings</h3>
        <div className="grid grid-cols-2 gap-4">
          <Select defaultValue="chromium">
            <SelectTrigger>
              <SelectValue placeholder="Browser" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="chromium">Chromium</SelectItem>
              <SelectItem value="firefox">Firefox</SelectItem>
              <SelectItem value="webkit">WebKit</SelectItem>
            </SelectContent>
          </Select>
          <Select defaultValue="desktop">
            <SelectTrigger>
              <SelectValue placeholder="Device" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="desktop">Desktop</SelectItem>
              <SelectItem value="tablet">Tablet</SelectItem>
              <SelectItem value="mobile">Mobile</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </TabsContent>

      <TabsContent value="browser" className="p-4 border rounded-md mt-2">
        <div className="text-center text-muted-foreground p-6">
          Browser preview will appear here during test execution
        </div>
      </TabsContent>

      <TabsContent value="reports" className="p-4 border rounded-md mt-2">
        <div className="flex justify-between mb-4">
          <h3 className="text-sm font-medium">Test Reports</h3>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
        <div className="text-center text-muted-foreground p-6">
          Test reports will be available after execution
        </div>
      </TabsContent>
    </Tabs>
  );
};

export default ToolsSection;
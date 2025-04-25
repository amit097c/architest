import React, { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle, AlertCircle, Clock, RefreshCw, Terminal } from "lucide-react";

// Types
interface StatusEvent {
  id: string;
  timestamp: Date;
  type: "info" | "success" | "error" | "warning";
  message: string;
  details?: string;
}

interface StatusSectionProps {
  currentStatus: string;
  events: StatusEvent[];
  iterations: number;
  duration?: number;
  statusTestErrors?: {
    message?: string;
  } | null;
  isApiTest?: boolean;
}

const StatusSection: React.FC<StatusSectionProps> = ({
  currentStatus,
  events,
  iterations,
  duration,
  statusTestErrors: testErrors,
  isApiTest = false
}) => {
  // Calculate duration if start and end times are available
  const getDuration = () => {
    if (duration === undefined) return "Not started";
    
    // Since duration is already in seconds, not milliseconds
    const minutes = Math.floor(duration / 60);
    const seconds = (duration % 60).toFixed(1);
  
    return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
  };
  
  // Get status icon based on event type
  const getEventIcon = (type: StatusEvent["type"]) => {
    switch (type) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "warning":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case "info":
      default:
        return <Terminal className="h-4 w-4 text-blue-500" />;
    }
  };
  
  // Format timestamp
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Get the latest status message to display in the badge
  const getStatusBadgeText = useMemo(() => {
    if (events.length === 0) {
      return currentStatus === "idle" ? "Ready" : "Generating...";
    }

    // Sort events by timestamp (newest first)
    const sortedEvents = [...events].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    // Customize based on final status
    if (currentStatus === "idle") return "Ready";
    if (currentStatus === "passed") return "Tests Passed";
    if (currentStatus === "failed") return "Tests Failed";
    
    // Get the most recent relevant event message for active statuses
    for (const event of sortedEvents) {
      // Skip certain messages that shouldn't be displayed as the main status
      if (event.message.includes("cancelled") || 
          event.message.includes("initializing") ||
          event.type === "error" && currentStatus !== "failed") {
        continue;
      }
      
      if (event.message.includes("Extracting and processing html")) 
        return "Processing HTML...";
      if (event.message.includes("Preparing API test"))
        return "Preparing API Test...";
      if (event.message.includes("Generating script"))
        return "Generating Script...";
      if (event.message.includes("Executing test"))
        return "Running Tests...";
      if (event.message.includes("Refining test"))
        return "Refining Script...";
      
      // For custom messages that don't match the patterns above,
      // display a formatted version of the actual message
      if (event.type === "info" && event.message) {
        const message = event.message.charAt(0).toUpperCase() + event.message.slice(1);
        // Truncate long messages
        return message.length > 25 ? message.substring(0, 22) + "..." : message;
      }
    }
    
    // Default mapping for statuses if no matching event was found
    if (currentStatus === "extracting-and-processing-html") return "Processing HTML...";
    if (currentStatus === "generating") return "Generating...";
    if (currentStatus === "running") return "Running Tests...";
    if (currentStatus === "refining") return "Refining Script...";
    
    return "Processing...";
  }, [events, currentStatus]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">Test Execution Status</CardTitle>
          <Badge 
            variant={
              currentStatus === "passed" ? "default" :
              currentStatus === "failed" ? "destructive" :
              currentStatus === "generating" || currentStatus === "running" || currentStatus === "refining" ? "outline" :
              "secondary"
            }
            className={
              currentStatus === "generating" || currentStatus === "running" || currentStatus === "refining" || currentStatus === "extracting-and-processing-html"
                ? "animate-pulse" 
                : ""
            }
          >
            {getStatusBadgeText}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="bg-muted rounded-md p-3">
            <div className="text-xs text-muted-foreground mb-1">Duration</div>
            <div className="text-sm font-medium flex items-center">
              <Clock className="h-3 w-3 mr-1" />
              {getDuration()}
            </div>
          </div>
          
          <div className="bg-muted rounded-md p-3">
            <div className="text-xs text-muted-foreground mb-1">Iterations</div>
            <div className="text-sm font-medium flex items-center">
              <RefreshCw className="h-3 w-3 mr-1" />
              {iterations}
            </div>
          </div>
          
          <div className="bg-muted rounded-md p-3">
            <div className="text-xs text-muted-foreground mb-1">Events</div>
            <div className="text-sm font-medium">
              {events.length}
            </div>
          </div>
        </div>
        
        <Separator className="my-2" />
        
        <div className="mt-3">
          <div className="text-sm font-medium mb-2">Event Log</div>
          <ScrollArea className="h-48 rounded-md border p-2">
            {events.length === 0 ? (
              <div className="text-center text-muted-foreground p-4">
                No events recorded yet
              </div>
            ) : (
              <div className="space-y-2">
                {events.slice(0).reverse().map((event) => (
                  <div key={event.id} className="text-xs border-l-2 pl-3 py-1" 
                    style={{ 
                      borderColor: 
                        event.type === "success" ? "rgb(34, 197, 94)" :
                        event.type === "error" ? "rgb(239, 68, 68)" :
                        event.type === "warning" ? "rgb(234, 179, 8)" :
                        "rgb(59, 130, 246)"
                    }}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-center">
                        {getEventIcon(event.type)}
                        <span className="ml-2 font-medium">{event.message}</span>
                      </div>
                      <span className="text-muted-foreground">
                        {formatTime(event.timestamp)}
                      </span>
                    </div>
                    {event.details && (
                      <div className="ml-6 mt-1 text-muted-foreground overflow-x-auto">
                        {event.details}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Error Box */}
        {testErrors && (
          <>
            <Separator className="my-4" />
            <div className="mt-3">
              <div className="text-sm font-medium mb-2 flex items-center">
                <AlertCircle className="mr-2 h-4 w-4 text-red-500" />
                <span>Error Details</span>
              </div>
              <div className="rounded-md border border-red-200 bg-red-50 p-2">
                <pre className="text-sm whitespace-pre-wrap overflow-x-auto font-mono text-red-600">
                  {testErrors.message}
                </pre>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default StatusSection;

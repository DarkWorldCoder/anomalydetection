import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircleIcon } from "lucide-react";

export function LoadingPanel({ rows = 3 }) {
  return (
    <div className="flex flex-col gap-3" aria-label="Loading">
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} className="h-12 w-full" />
      ))}
    </div>
  );
}

export function ErrorPanel({ error }) {
  return (
    <Alert variant="destructive">
      <AlertCircleIcon />
      <AlertTitle>Could not load this view</AlertTitle>
      <AlertDescription>
        {error?.message || "Please try again."}
      </AlertDescription>
    </Alert>
  );
}

export function MethodBadge({ method }) {
  const variant =
    method === "GET"
      ? "secondary"
      : method === "POST"
        ? "destructive"
        : "outline";
  return <Badge variant={variant}>{method}</Badge>;
}

export function RiskBadge({ risk, prediction }) {
  if (prediction === "Benign" || risk === "low")
    return (
      <Badge className="bg-success/12 text-success hover:bg-success/12">
        Low risk
      </Badge>
    );
  if (risk === "high") return <Badge variant="destructive">High risk</Badge>;
  return (
    <Badge className="bg-warning/15 text-warning-foreground hover:bg-warning/15">
      Medium risk
    </Badge>
  );
}

export function ScoreBadge({ score }) {
  return (
    <Badge
      variant={
        score >= 0.7 ? "destructive" : score >= 0.5752 ? "outline" : "secondary"
      }
    >
      {Number(score).toFixed(4)}
    </Badge>
  );
}

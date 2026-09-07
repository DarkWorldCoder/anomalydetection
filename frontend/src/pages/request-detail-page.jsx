import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  Clipboard,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ErrorPanel,
  LoadingPanel,
  MethodBadge,
  RiskBadge,
  ScoreBadge,
} from "@/components/data-display";

const FEATURE_LABELS = {
  url_length: "URL length",
  endpoint_depth: "Endpoint depth",
  query_param_count: "Query parameter count",
  body_length: "Body length",
  header_count: "Header count",
  cookie_length: "Cookie length",
  user_agent_length: "User-agent length",
  special_char_count: "Special-character count",
  special_char_density: "Special-character density",
  sql_pattern_score: "SQL injection pattern",
  xss_pattern_score: "Cross-site scripting pattern",
  traversal_pattern_score: "Directory traversal pattern",
  command_pattern_score: "Command execution pattern",
  log_injection_pattern_score: "Log injection pattern",
  log4j_pattern_score: "Log4j lookup pattern",
  cookie_injection_pattern_score: "Cookie injection pattern",
  composite_anomaly_score: "Matched threat patterns",
  response_body_length: "Response body length",
  response_header_count: "Response header count",
  status_code: "HTTP status code",
  is_error_status: "Error response",
};

const PATTERN_EVIDENCE = [
  {
    key: "sql_pattern_score",
    title: "SQL injection signature",
    detail:
      "SQL keywords, quote operators, or comment syntax were found in the request URL or body.",
  },
  {
    key: "xss_pattern_score",
    title: "Cross-site scripting signature",
    detail:
      "Executable HTML or script syntax was found in the request URL or body.",
  },
  {
    key: "traversal_pattern_score",
    title: "Directory traversal signature",
    detail:
      "Parent-directory sequences or a sensitive system-file path were found.",
  },
  {
    key: "command_pattern_score",
    title: "Command execution signature",
    detail: "Operating-system command or template execution syntax was found.",
  },
  {
    key: "log_injection_pattern_score",
    title: "Log injection signature",
    detail:
      "Encoded line breaks and content resembling a forged log entry were found.",
  },
  {
    key: "log4j_pattern_score",
    title: "Log4j lookup signature",
    detail: "A JNDI lookup associated with Log4j exploitation was found.",
  },
  {
    key: "cookie_injection_pattern_score",
    title: "Cookie injection signature",
    detail: "Serialized or executable content was found in a cookie value.",
  },
];

function formatFeatureValue(key, value) {
  if (key === "is_error_status") return Number(value) ? "Yes" : "No";
  if (key.endsWith("_pattern_score"))
    return Number(value) ? "Detected" : "Not detected";
  if (typeof value !== "number") return String(value);
  if (Number.isInteger(value)) return value.toLocaleString();
  return value.toFixed(4);
}

function getDecisionSummary(detection) {
  const score =
    detection.anomaly_score == null
      ? Number.NaN
      : Number(detection.anomaly_score);
  const threshold =
    detection.threshold == null ? Number.NaN : Number(detection.threshold);
  const suspicious = detection.prediction === "Suspicious";

  if (!Number.isFinite(score) || !Number.isFinite(threshold)) {
    return suspicious
      ? "The request crossed the model's decision threshold."
      : "The request remained below the model's decision threshold.";
  }

  const distance = Math.abs(score - threshold).toFixed(4);
  return suspicious
    ? `The anomaly score is ${distance} above the decision threshold.`
    : `The anomaly score is ${distance} below the decision threshold.`;
}

export function RequestDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [featuresOpen, setFeaturesOpen] = useState(true);
  const query = useQuery({
    queryKey: ["request", id],
    queryFn: () => apiRequest(`/requests/${id}`),
  });
  const remove = useMutation({
    mutationFn: () => apiRequest(`/requests/${id}`, { method: "DELETE" }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ["requests"] });
      navigate("/requests");
    },
  });
  if (query.isLoading) return <LoadingPanel rows={7} />;
  if (query.error) return <ErrorPanel error={query.error} />;
  const item = query.data;
  const detection = item.detection || {};
  const features = item.features || {};
  const suspicious = detection.prediction === "Suspicious";
  const evidence = PATTERN_EVIDENCE.filter(
    ({ key }) => Number(features[key]) > 0,
  );
  const score =
    detection.anomaly_score == null
      ? Number.NaN
      : Number(detection.anomaly_score);
  const threshold =
    detection.threshold == null ? Number.NaN : Number(detection.threshold);
  const scoreDistance =
    Number.isFinite(score) && Number.isFinite(threshold)
      ? Math.abs(score - threshold)
      : null;
  const raw = `${item.method} ${item.url}\n\n${JSON.stringify(item.request?.headers || {}, null, 2)}\n\n${typeof item.request?.body === "string" ? item.request.body : JSON.stringify(item.request?.body, null, 2)}`;
  return (
    <div className="page-stack">
      <div className="flex justify-between">
        <Button asChild variant="ghost">
          <Link to="/requests">
            <ArrowLeft />
            Back to Request Logs
          </Link>
        </Button>
        <Button
          variant="outline"
          className="text-destructive"
          onClick={() => setOpen(true)}
        >
          <Trash2 />
          Delete
        </Button>
      </div>
      <Card
        className={
          detection.prediction === "Suspicious"
            ? "border-destructive/30 bg-destructive/3"
            : "border-success/30 bg-success/3"
        }
      >
        <CardContent className="grid gap-6 p-6 md:grid-cols-2 xl:grid-cols-4">
          <div className="flex items-center gap-3">
            <div
              className={
                suspicious
                  ? "metric-icon metric-icon-danger"
                  : "metric-icon metric-icon-success"
              }
            >
              {suspicious ? <ShieldAlert /> : <CheckCircle2 />}
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Risk status</span>
              <div>
                <RiskBadge
                  risk={detection.risk_level}
                  prediction={detection.prediction}
                />
              </div>
            </div>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Anomaly score</span>
            <div className="mt-2">
              <ScoreBadge score={detection.anomaly_score} />
            </div>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Endpoint</span>
            <div className="mt-2 flex gap-2">
              <MethodBadge method={item.method} />
              <strong>{item.endpoint}</strong>
            </div>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Source IP</span>
            <strong className="mt-2 block">{item.source_ip || "—"}</strong>
          </div>
        </CardContent>
      </Card>
      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <div>
                <CardTitle>Raw HTTP request</CardTitle>
                <CardDescription>Stored request payload</CardDescription>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigator.clipboard.writeText(raw)}
              >
                <Clipboard />
                Copy
              </Button>
            </CardHeader>
            <CardContent>
              <pre className="code-panel">{raw}</pre>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Response</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="code-panel">
                {JSON.stringify(item.response, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <Card>
            <CardHeader className="flex-row items-center justify-between gap-4">
              <div>
                <CardTitle>Extracted features</CardTitle>
                <CardDescription>
                  {Object.keys(features).length} measurements used during
                  scoring
                </CardDescription>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                aria-expanded={featuresOpen}
                aria-controls="extracted-features"
                onClick={() => setFeaturesOpen((current) => !current)}
              >
                {featuresOpen ? <ChevronUp /> : <ChevronDown />}
                {featuresOpen ? "Collapse" : "Expand"}
              </Button>
            </CardHeader>
            {featuresOpen && (
              <CardContent id="extracted-features" className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Feature</TableHead>
                      <TableHead>Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(features).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell className="font-medium">
                          {FEATURE_LABELS[key] || key.replaceAll("_", " ")}
                        </TableCell>
                        <TableCell>{formatFeatureValue(key, value)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            )}
          </Card>
          <Card
            className={
              suspicious ? "border-destructive/30" : "border-success/30"
            }
          >
            <CardHeader className="flex-row items-start gap-3">
              <div
                className={
                  suspicious
                    ? "metric-icon metric-icon-danger"
                    : "metric-icon metric-icon-success"
                }
              >
                {suspicious ? <CircleAlert /> : <CheckCircle2 />}
              </div>
              <div>
                <CardTitle>
                  {suspicious
                    ? "Why this request was flagged"
                    : "Why this request was considered benign"}
                </CardTitle>
                <CardDescription>
                  Decision evidence recorded during analysis
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="rounded-lg border bg-muted/40 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Model decision
                    </p>
                    <p className="mt-1 text-lg font-semibold">
                      {suspicious
                        ? detection.attack_type || "Suspicious request"
                        : "No anomaly detected"}
                    </p>
                  </div>
                  <RiskBadge
                    risk={detection.risk_level}
                    prediction={detection.prediction}
                  />
                </div>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  {getDecisionSummary(detection)}
                </p>
              </div>

              <dl className="grid grid-cols-3 gap-3">
                <div className="rounded-md border p-3">
                  <dt className="text-xs text-muted-foreground">Score</dt>
                  <dd className="mt-1 font-semibold">
                    {Number.isFinite(score) ? score.toFixed(4) : "—"}
                  </dd>
                </div>
                <div className="rounded-md border p-3">
                  <dt className="text-xs text-muted-foreground">Threshold</dt>
                  <dd className="mt-1 font-semibold">
                    {Number.isFinite(threshold) ? threshold.toFixed(4) : "—"}
                  </dd>
                </div>
                <div className="rounded-md border p-3">
                  <dt className="text-xs text-muted-foreground">Distance</dt>
                  <dd className="mt-1 font-semibold">
                    {scoreDistance === null ? "—" : scoreDistance.toFixed(4)}
                  </dd>
                </div>
              </dl>

              <div>
                <h3 className="text-sm font-semibold">Observed evidence</h3>
                <div className="mt-3 space-y-3">
                  {evidence.length > 0 ? (
                    evidence.map(({ key, title, detail }) => (
                      <div className="flex gap-3" key={key}>
                        <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-destructive" />
                        <div>
                          <p className="text-sm font-medium">{title}</p>
                          <p className="mt-1 text-sm leading-5 text-muted-foreground">
                            {detail}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm leading-6 text-muted-foreground">
                      {detection.reasons?.[0] ||
                        "No known attack signature matched. The decision came from the combined request measurements."}
                    </p>
                  )}
                </div>
              </div>

              {detection.explanation && (
                <div className="border-t pt-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Model note
                  </p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {detection.explanation}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete request?</DialogTitle>
            <DialogDescription>
              This permanently removes the stored request and its detection
              result.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => remove.mutate()}
              disabled={remove.isPending}
            >
              {remove.isPending ? "Deleting…" : "Delete request"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

import { useMemo, useRef, useState } from "react";
import {
  Braces,
  Eye,
  FileUp,
  RotateCcw,
  ScanSearch,
  Trash2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { apiRequest } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { MethodBadge, RiskBadge, ScoreBadge } from "@/components/data-display";

const example = JSON.stringify(
  [
    {
      request: {
        method: "POST",
        url: "/api/login",
        headers: { "content-type": "application/json" },
        body: '{"username":"student"}',
        Attack_Tag: null,
      },
      response: { status: "OK", headers: {}, status_code: 200, body: "{}" },
      metadata: { source_ip: "203.0.113.45", response_time_ms: 142 },
    },
  ],
  null,
  2,
);

export function DetectPage() {
  const inputRef = useRef(null);
  const [text, setText] = useState(example);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState([]);
  const [previewTotal, setPreviewTotal] = useState(0);
  const [previewSource, setPreviewSource] = useState("");
  const [selectedPreview, setSelectedPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const records = useMemo(() => {
    try {
      const value = JSON.parse(text);
      return Array.isArray(value) ? value : value.records || [value];
    } catch {
      return [];
    }
  }, [text]);

  async function previewJson() {
    setError("");
    try {
      const data = await apiRequest("/detect/preview", {
        method: "POST",
        body: { records },
      });
      setPreview(data.preview);
      setPreviewTotal(data.total_requests);
      setPreviewSource("Pasted JSON");
      setSelectedPreview(null);
    } catch (e) {
      setError(e.message);
    }
  }
  async function previewFile(selectedFile = file) {
    if (!selectedFile) return;
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", selectedFile);
      const data = await apiRequest("/detect/preview-upload", {
        method: "POST",
        body,
      });
      setPreview(data.preview);
      setPreviewTotal(data.total_requests);
      setPreviewSource(data.file_name || selectedFile.name);
      setSelectedPreview(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  function clearSelectedFile() {
    setFile(null);
    setPreview([]);
    setPreviewTotal(0);
    setPreviewSource("");
    setSelectedPreview(null);
    setResult(null);
    if (inputRef.current) inputRef.current.value = "";
  }
  async function runDetection() {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      let data;
      if (file) {
        const body = new FormData();
        body.append("file", file);
        data = await apiRequest("/detect/upload", { method: "POST", body });
      } else {
        data = await apiRequest("/detect/bulk", {
          method: "POST",
          body: { records },
        });
      }
      setResult(data);
      setPreview([]);
      setPreviewTotal(0);
      setPreviewSource("");
      setSelectedPreview(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function startNewDetection() {
    setResult(null);
    setFile(null);
    setPreview([]);
    setPreviewTotal(0);
    setPreviewSource("");
    setSelectedPreview(null);
    setError("");
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="page-stack">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {!result && (
        <>
          <section className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>1. Upload API log file</CardTitle>
                <CardDescription>
                  JSON or CSV, up to 5 MB and 1,000 records.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <button
                  className="upload-zone"
                  onClick={() => inputRef.current?.click()}
                  type="button"
                >
                  <FileUp className="size-12 text-primary" strokeWidth={1.75} />
                  <strong>{file?.name || "Choose a file"}</strong>
                  <span>
                    {file ? "Preview it before detection" : "Click to browse"}
                  </span>
                </button>
                <input
                  ref={inputRef}
                  className="sr-only"
                  type="file"
                  accept=".json,.csv"
                  onChange={(e) => {
                    const selectedFile = e.target.files?.[0] || null;
                    setFile(selectedFile);
                    setPreview([]);
                    setPreviewTotal(0);
                    setPreviewSource("");
                    setSelectedPreview(null);
                    setResult(null);
                    if (selectedFile) previewFile(selectedFile);
                  }}
                />
                <div className="grid gap-2 sm:grid-cols-2">
                  <Button
                    variant="outline"
                    onClick={() => previewFile()}
                    disabled={!file || busy}
                  >
                    <Eye />
                    {busy ? "Reading file…" : "Reload preview"}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={clearSelectedFile}
                    disabled={!file || busy}
                  >
                    <Trash2 />
                    Remove file
                  </Button>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex-row items-start justify-between">
                <div>
                  <CardTitle>2. Paste requests</CardTitle>
                  <CardDescription>
                    Use the backend traffic record format.
                  </CardDescription>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setText("")}>
                  <Trash2 />
                  Clear
                </Button>
              </CardHeader>
              <CardContent className="space-y-3">
                <Textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="min-h-96 resize-y p-4 font-mono text-sm leading-6"
                />
                <Button
                  variant="outline"
                  onClick={previewJson}
                  disabled={Boolean(file) || !records.length}
                >
                  <Braces />
                  Preview JSON
                </Button>
              </CardContent>
            </Card>
          </section>
          {preview.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>3. Preview of requests ({previewTotal})</CardTitle>
                <CardDescription>
                  {previewSource && <strong>{previewSource} · </strong>}
                  Review the complete URL and payload details before detection.
                </CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>#</TableHead>
                      <TableHead>Full URL</TableHead>
                      <TableHead>Method</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Response time</TableHead>
                      <TableHead>Source IP</TableHead>
                      <TableHead className="text-right">Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.map((row) => (
                      <TableRow key={row.index}>
                        <TableCell>{row.index}</TableCell>
                        <TableCell className="max-w-md break-all font-mono text-xs">
                          {row.url}
                        </TableCell>
                        <TableCell>
                          <MethodBadge method={row.method} />
                        </TableCell>
                        <TableCell>{row.status_code}</TableCell>
                        <TableCell>{row.response_time_ms} ms</TableCell>
                        <TableCell>{row.source_ip || "—"}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setSelectedPreview(
                                selectedPreview?.index === row.index
                                  ? null
                                  : row,
                              )
                            }
                          >
                            <Eye />
                            {selectedPreview?.index === row.index
                              ? "Hide"
                              : "View"}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {selectedPreview && <PreviewDetails record={selectedPreview} />}
              </CardContent>
            </Card>
          )}
          <Button
            className="mx-auto h-12 w-full max-w-md"
            onClick={runDetection}
            disabled={busy || (!file && !records.length)}
          >
            <ScanSearch />
            {busy ? "Analyzing…" : "Run Detection"}
          </Button>
        </>
      )}
      {result && (
        <Card>
          <CardHeader className="flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Detection results</CardTitle>
              <CardDescription>
                {result.total_requests} requests analyzed ·{" "}
                {result.suspicious_count} suspicious · {result.benign_count}{" "}
                benign
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={startNewDetection}>
              <RotateCcw />
              Analyze another batch
            </Button>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Endpoint</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Prediction</TableHead>
                  <TableHead>Attack type</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead className="text-right">Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.results?.map((row) => (
                  <TableRow key={row.request_id || row.id}>
                    <TableCell>{row.endpoint || row.url}</TableCell>
                    <TableCell>
                      <MethodBadge method={row.method} />
                    </TableCell>
                    <TableCell>{row.prediction}</TableCell>
                    <TableCell>{row.attack_type || "—"}</TableCell>
                    <TableCell>
                      <ScoreBadge score={row.anomaly_score} />
                    </TableCell>
                    <TableCell>
                      <RiskBadge
                        risk={row.risk_level}
                        prediction={row.prediction}
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      <Button asChild variant="ghost" size="sm">
                        <Link to={`/requests/${row.request_id || row.id}`}>
                          View details
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function PreviewDetails({ record }) {
  return (
    <div className="mt-5 rounded-lg border bg-slate-50 p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Request {record.index}
          </p>
          <p className="mt-1 break-all font-mono text-sm">{record.url}</p>
        </div>
        <MethodBadge method={record.method} />
      </div>
      <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-muted-foreground">Status</dt>
          <dd className="font-medium">
            {record.status_code} {record.status}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Response time</dt>
          <dd className="font-medium">{record.response_time_ms} ms</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Request size</dt>
          <dd className="font-medium">{record.request_size_bytes} bytes</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Response size</dt>
          <dd className="font-medium">{record.response_size_bytes} bytes</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Source IP</dt>
          <dd className="font-medium">{record.source_ip || "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Timestamp</dt>
          <dd className="font-medium">{record.timestamp || "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Attack tag</dt>
          <dd className="font-medium">{record.attack_tag || "—"}</dd>
        </div>
      </dl>
      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <DetailBlock title="Request headers" value={record.request_headers} />
        <DetailBlock title="Response headers" value={record.response_headers} />
        <DetailBlock title="Request body" value={record.request_body} />
        <DetailBlock title="Response body" value={record.response_body} />
      </div>
    </div>
  );
}

function DetailBlock({ title, value }) {
  const content =
    typeof value === "string"
      ? value || "Empty"
      : JSON.stringify(value || {}, null, 2);
  return (
    <div>
      <h4 className="mb-2 text-sm font-medium">{title}</h4>
      <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">
        {content}
      </pre>
    </div>
  );
}

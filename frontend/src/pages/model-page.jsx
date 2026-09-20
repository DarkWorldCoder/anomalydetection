import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ErrorPanel, LoadingPanel } from "@/components/data-display";

const labels = {
  accuracy: "Accuracy",
  precision: "Precision",
  recall: "Recall",
  f1_score: "F1 score",
  roc_auc: "ROC AUC",
  confusion_matrix: "Confusion matrix",
};

function metricValue(value) {
  if (typeof value === "number") return value.toFixed(4);
  if (Array.isArray(value)) {
    return value.map((row) => `[${row.join(", ")}]`).join("  ");
  }
  return String(value);
}

export function ModelPage() {
  const query = useQuery({
    queryKey: ["model"],
    queryFn: () => apiRequest("/model/info"),
  });
  if (query.isLoading) return <LoadingPanel rows={6} />;
  if (query.error) return <ErrorPanel error={query.error} />;
  const model = query.data;
  return (
    <div className="page-stack">
      <Card className="gap-0 py-0">
        <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
              Active scoring model
            </p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight">
              {model.name}
            </h2>
          </div>
          <div className="flex items-center gap-2 text-sm font-medium text-emerald-700">
            <span
              className="size-2 rounded-full bg-emerald-500"
              aria-hidden="true"
            />
            Loaded and ready
          </div>
        </CardContent>
      </Card>
      <Card className="gap-0 py-0">
        <CardContent className="grid p-0 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Training dataset" value={model.dataset} />
          <Metric label="Input features" value={model.feature_count} />
          <Metric label="Isolation trees" value={model.trees} />
          <Metric label="Decision threshold" value={model.threshold} />
        </CardContent>
      </Card>
      <section className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Model features</CardTitle>
            <CardDescription>
              {model.feature_count} numeric features used during scoring
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="grid gap-x-5 gap-y-2 sm:grid-cols-2">
              {model.features?.map((feature, index) => (
                <li
                  key={feature}
                  className="flex items-baseline gap-3 border-b pb-2 text-sm last:border-0"
                >
                  <span className="w-6 shrink-0 font-mono text-xs text-muted-foreground">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <code className="break-all text-xs font-medium">
                    {feature}
                  </code>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Validation metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="detail-list">
              {Object.entries(model.validation_metrics || {}).map(
                ([key, value]) => (
                  <div key={key}>
                    <dt>{labels[key] || key.replaceAll("_", " ")}</dt>
                    <dd
                      className={
                        Array.isArray(value)
                          ? "font-mono text-xs"
                          : "tabular-nums"
                      }
                    >
                      {metricValue(value)}
                    </dd>
                  </div>
                ),
              )}
            </dl>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
function Metric({ label, value }) {
  return (
    <div className="model-metric">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <strong className="mt-1 block text-xl font-semibold tabular-nums">
        {value}
      </strong>
    </div>
  );
}

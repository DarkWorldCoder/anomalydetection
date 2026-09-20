import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from "recharts";
import {
  ActivityIcon,
  AlertTriangleIcon,
  CheckCircle2Icon,
  DatabaseIcon,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  LoadingPanel,
  MethodBadge,
  RiskBadge,
  ScoreBadge,
} from "@/components/data-display";

const chartConfig = {
  total_requests: { label: "Total requests", color: "var(--primary)" },
  suspicious_requests: { label: "Suspicious", color: "var(--destructive)" },
};

function StatCard({ title, value, icon: Icon, tone = "primary" }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <div className={`metric-icon metric-icon-${tone}`}>
          <Icon />
        </div>
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-sm text-muted-foreground">{title}</span>
          <strong className="text-2xl tracking-tight">
            {typeof value === "string"
              ? value
              : Number(value || 0).toLocaleString()}
          </strong>
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const summary = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => apiRequest("/dashboard/summary"),
  });
  const trend = useQuery({
    queryKey: ["dashboard", "trend"],
    queryFn: () => apiRequest("/dashboard/request-trend?range=7d"),
  });
  const recent = useQuery({
    queryKey: ["dashboard", "recent"],
    queryFn: () => apiRequest("/dashboard/recent-suspicious?limit=5"),
  });
  const risky = useQuery({
    queryKey: ["dashboard", "risky"],
    queryFn: () => apiRequest("/dashboard/top-risky-endpoints?limit=5"),
  });
  if (summary.isLoading) return <LoadingPanel rows={6} />;
  const stats = summary.data || {};
  const benign = stats.benigin_requests || 0;
  const pieData = [
    { name: "Benign", value: benign, fill: "var(--success)" },
    {
      name: "Suspicious",
      value: stats.suspicious_requests || 0,
      fill: "var(--destructive)",
    },
  ];
  return (
    <div className="page-stack">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Requests"
          value={stats.total_requests}
          icon={DatabaseIcon}
        />
        <StatCard
          title="Suspicious Requests"
          value={stats.suspicious_requests}
          icon={AlertTriangleIcon}
          tone="danger"
        />
        <StatCard
          title="Benign Requests"
          value={benign}
          icon={CheckCircle2Icon}
          tone="success"
        />
        <StatCard
          title="Anomaly Rate"
          value={`${stats.anomaly_rate || 0}%`}
          icon={ActivityIcon}
          tone="info"
        />
      </section>
      <section className="grid gap-4 xl:grid-cols-[2fr_0.8fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Request Trend</CardTitle>
            <CardDescription>
              Last seven days of analyzed traffic
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-72 w-full">
              <AreaChart data={trend.data || []} accessibilityLayer>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="date" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} width={40} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area
                  dataKey="total_requests"
                  type="monotone"
                  fill="var(--color-total_requests)"
                  fillOpacity={0.12}
                  stroke="var(--color-total_requests)"
                  strokeWidth={2}
                />
                <Area
                  dataKey="suspicious_requests"
                  type="monotone"
                  fill="var(--color-suspicious_requests)"
                  fillOpacity={0.08}
                  stroke="var(--color-suspicious_requests)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ChartContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Traffic Mix</CardTitle>
            <CardDescription>Benign vs suspicious</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer
              config={{
                benign: { label: "Benign" },
                suspicious: { label: "Suspicious" },
              }}
              className="h-56 w-full"
            >
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={58}
                  outerRadius={82}
                  strokeWidth={4}
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={entry.fill} />
                  ))}
                </Pie>
                <ChartTooltip
                  content={<ChartTooltipContent nameKey="name" />}
                />
              </PieChart>
            </ChartContainer>
            <div className="flex justify-between text-sm">
              <span>Benign</span>
              <strong>{benign.toLocaleString()}</strong>
            </div>
            <div className="flex justify-between text-sm">
              <span>Suspicious</span>
              <strong>
                {Number(stats.suspicious_requests || 0).toLocaleString()}
              </strong>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Top Risky Endpoints</CardTitle>
            <CardDescription>Highest observed model scores</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {(risky.data || []).map((item) => (
              <div
                key={`${item.method}-${item.endpoint}`}
                className="flex items-center gap-3"
              >
                <MethodBadge method={item.method} />
                <span className="min-w-0 flex-1 truncate text-sm">
                  {item.endpoint}
                </span>
                <ScoreBadge score={item.anomaly_score} />
              </div>
            ))}
            {!risky.data?.length && (
              <p className="text-sm text-muted-foreground">
                No analyzed endpoints yet.
              </p>
            )}
          </CardContent>
        </Card>
      </section>
      <section>
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Suspicious Requests</CardTitle>
              <CardDescription>Requests that need attention</CardDescription>
            </div>
            <Button variant="ghost" asChild>
              <Link to="/requests">View all</Link>
            </Button>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Endpoint</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Risk</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(recent.data || []).map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="whitespace-nowrap">
                      {new Date(item.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Link
                        className="font-medium hover:underline"
                        to={`/requests/${item.id}`}
                      >
                        {item.endpoint}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <MethodBadge method={item.method} />
                    </TableCell>
                    <TableCell>
                      <ScoreBadge score={item.anomaly_score} />
                    </TableCell>
                    <TableCell>
                      <RiskBadge
                        risk={item.risk_level}
                        prediction={item.prediction}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

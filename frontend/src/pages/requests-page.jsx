import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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

export function RequestsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState("all");
  const query = useQuery({
    queryKey: ["requests", page, search, risk],
    queryFn: () =>
      apiRequest(
        `/requests?page=${page}&limit=20&search=${encodeURIComponent(search)}${risk === "all" ? "" : `&risk_level=${risk}`}`,
      ),
  });

  return (
    <div className="page-stack">
      <Card>
        <CardHeader>
          <CardTitle>Analyzed requests</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search endpoint or URL"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
              />
            </div>
            <Select
              value={risk}
              onValueChange={(value) => {
                setRisk(value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-full sm:w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All risk levels</SelectItem>
                <SelectItem value="high">High risk</SelectItem>
                <SelectItem value="medium">Medium risk</SelectItem>
                <SelectItem value="low">Low risk</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {query.isLoading ? (
            <LoadingPanel />
          ) : query.error ? (
            <ErrorPanel error={query.error} />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Endpoint</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Risk</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {query.data?.items?.map((row) => {
                    const requestId = row.request_id || row.id;
                    return (
                      <TableRow key={requestId}>
                        <TableCell className="whitespace-nowrap">
                          {new Date(
                            row.created_at || row.time,
                          ).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Link
                            className="font-medium text-primary hover:underline"
                            to={`/requests/${requestId}`}
                          >
                            {row.endpoint || row.url}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <MethodBadge method={row.method} />
                        </TableCell>
                        <TableCell>{row.status_code}</TableCell>
                        <TableCell>
                          <ScoreBadge score={row.anomaly_score} />
                        </TableCell>
                        <TableCell>
                          <RiskBadge
                            risk={row.risk_level}
                            prediction={row.prediction}
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              {!query.data?.items?.length && (
                <p className="py-12 text-center text-muted-foreground">
                  No requests match these filters.
                </p>
              )}
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Page {query.data?.page || page} of {query.data?.total_pages || 1}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={page === 1}
                onClick={() => setPage((value) => value - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={page >= (query.data?.total_pages || 1)}
                onClick={() => setPage((value) => value + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

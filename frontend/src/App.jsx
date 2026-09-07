import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { AppShell } from "@/components/app-shell";
import { LoadingPanel } from "@/components/data-display";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/context/auth-context";
import { LoginPage } from "@/pages/login-page";
import { RegisterPage } from "@/pages/register-page";
import { DashboardPage } from "@/pages/dashboard-page";
import { DetectPage } from "@/pages/detect-page";
import { RequestsPage } from "@/pages/requests-page";
import { RequestDetailPage } from "@/pages/request-detail-page";
import { ModelPage } from "@/pages/model-page";
import { SettingsPage } from "@/pages/settings-page";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 20_000, retry: 1 } },
});

function Protected() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading)
    return (
      <main className="p-8">
        <LoadingPanel rows={6} />
      </main>
    );
  return isAuthenticated ? (
    <AppShell />
  ) : (
    <Navigate to="/login" state={{ from: location.pathname }} replace />
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <TooltipProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route element={<Protected />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/detect" element={<DetectPage />} />
                <Route path="/requests" element={<RequestsPage />} />
                <Route path="/requests/:id" element={<RequestDetailPage />} />
                <Route path="/model" element={<ModelPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </TooltipProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

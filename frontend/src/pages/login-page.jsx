import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { AuthLayout } from "@/components/auth-layout";
import { LoginForm } from "@/components/login-form";
import { useAuth } from "@/context/auth-context";

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      await login({
        email: form.get("email"),
        password: form.get("password"),
        remember,
      });
      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title="Detect unusual traffic early."
      description="Inspect API requests, understand anomaly signals, and review risky traffic from one focused workspace."
    >
      <LoginForm
        onSubmit={handleSubmit}
        error={error}
        submitting={submitting}
        remember={remember}
        onRememberChange={setRemember}
      />
    </AuthLayout>
  );
}

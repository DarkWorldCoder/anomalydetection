import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/password-input";

export function LoginForm({
  className,
  error,
  submitting,
  remember,
  onRememberChange,
  ...props
}) {
  return (
    <form className={cn("flex flex-col gap-6", className)} {...props}>
      <FieldGroup>
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Welcome back
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Sign in to continue to your workspace.
          </p>
        </div>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <Field>
          <FieldLabel htmlFor="email">Email</FieldLabel>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="student@example.edu"
            required
            autoFocus
            className="bg-background"
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="password">Password</FieldLabel>
          <PasswordInput
            id="password"
            name="password"
            autoComplete="current-password"
            required
          />
        </Field>
        <Field orientation="horizontal">
          <Checkbox
            id="remember"
            checked={remember}
            onCheckedChange={(checked) => onRememberChange(checked === true)}
          />
          <FieldLabel htmlFor="remember" className="font-normal">
            Remember me
          </FieldLabel>
        </Field>
        <Field>
          <Button type="submit" className="h-11" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </Field>
        <FieldDescription className="text-center">
          New to the system? <Link to="/register">Create an account</Link>
        </FieldDescription>
      </FieldGroup>
    </form>
  );
}

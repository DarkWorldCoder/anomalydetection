import { ChevronDown, LogOut, UserRound } from "lucide-react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { AppSidebar } from "@/components/app-sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { useAuth } from "@/context/auth-context";

const pageMeta = {
  "/dashboard": ["Dashboard", ""],
  "/detect": [
    "Upload and Detect Requests",
    "Upload API logs or paste JSON requests to detect anomalies",
  ],
  "/requests": ["Request Logs", ""],
  "/model": ["Model Status", ""],
  "/settings": ["Settings", ""],
};

function initials(name = "User") {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function AppShell() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const key = pathname.startsWith("/requests/") ? "/requests" : pathname;
  const [title, description] = pathname.startsWith("/requests/")
    ? ["Request Details", ""]
    : pageMeta[key] || ["Anomaly Detection System", ""];

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-w-0 bg-slate-50/70">
        <header className="sticky top-0 z-20 flex min-h-20 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur sm:px-6 lg:px-8">
          <SidebarTrigger className="md:hidden" />
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-xl font-semibold tracking-tight text-slate-950 sm:text-2xl">
              {title}
            </h1>
            {description && (
              <p className="mt-0.5 hidden truncate text-sm text-muted-foreground sm:block">
                {description}
              </p>
            )}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="h-11 gap-2 rounded-lg bg-background px-2.5 shadow-none"
                aria-label="Open account menu"
              >
                <Avatar className="size-8 bg-slate-900 text-white">
                  <AvatarFallback className="bg-transparent text-xs font-semibold text-white">
                    {initials(user?.full_name)}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden max-w-44 text-left sm:block">
                  <span className="block truncate text-sm font-medium">
                    {user?.full_name}
                  </span>
                  <span className="block truncate text-xs font-normal text-muted-foreground">
                    {user?.email}
                  </span>
                </span>
                <ChevronDown
                  className="hidden size-4 text-muted-foreground sm:block"
                  aria-hidden="true"
                />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              sideOffset={8}
              className="w-72 rounded-xl p-2 shadow-lg"
            >
              <DropdownMenuLabel className="px-2 py-2 font-normal">
                <span className="block truncate text-sm font-medium text-foreground">
                  {user?.full_name}
                </span>
                <span className="mt-0.5 block truncate text-xs text-muted-foreground">
                  {user?.email}
                </span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="my-1.5" />
              <DropdownMenuItem
                className="h-10 gap-3 px-2.5"
                onSelect={() => navigate("/settings")}
              >
                <UserRound /> Account
              </DropdownMenuItem>
              <DropdownMenuItem
                variant="destructive"
                className="h-10 gap-3 px-2.5"
                onSelect={handleLogout}
              >
                <LogOut /> Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
        <div className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

import { Boxes, FileSearch, Gauge, Radar, Settings } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";

import { Brand } from "@/components/brand";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";

const navigation = [
  { label: "Dashboard", href: "/dashboard", icon: Gauge },
  { label: "Detect Requests", href: "/detect", icon: Radar },
  { label: "Request Logs", href: "/requests", icon: FileSearch },
  { label: "Model Status", href: "/model", icon: Boxes },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function AppSidebar() {
  const { pathname } = useLocation();

  return (
    <Sidebar collapsible="icon" className="border-slate-200">
      <SidebarHeader className="h-24 justify-center px-4 group-data-[collapsible=icon]:px-1">
        <Brand sidebar className="group-data-[collapsible=icon]:hidden" />
        <Brand
          sidebar
          compact
          className="hidden group-data-[collapsible=icon]:flex"
        />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup className="px-3">
          <SidebarGroupContent>
            <SidebarMenu className="gap-2">
              {navigation.map(({ label, href, icon: Icon }) => (
                <SidebarMenuItem key={href}>
                  <SidebarMenuButton
                    asChild
                    isActive={
                      pathname === href || pathname.startsWith(`${href}/`)
                    }
                    tooltip={label}
                    className="h-11 px-3 text-sm text-teal-50/75 hover:bg-white/8 hover:text-white data-active:bg-teal-400/18 data-active:text-white data-active:hover:bg-teal-400/18 data-active:[&_svg]:text-teal-300"
                  >
                    <NavLink to={href}>
                      <Icon aria-hidden="true" />
                      <span>{label}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}

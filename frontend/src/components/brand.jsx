import { Radar } from "lucide-react";

import { cn } from "@/lib/utils";

export function Brand({ compact = false, sidebar = false, className }) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span
        className={cn(
          "grid size-11 shrink-0 place-items-center rounded-lg text-white",
          sidebar ? "bg-teal-500" : "bg-linear-to-br from-blue-500 to-blue-700",
        )}
      >
        <Radar className="size-7" strokeWidth={2.2} aria-hidden="true" />
      </span>
      {!compact && (
        <span
          className={cn(
            "text-[17px] leading-tight font-semibold tracking-tight",
            sidebar ? "text-white" : "text-slate-950",
          )}
        >
          Anomaly Detection
          <br />
          System
        </span>
      )}
    </div>
  );
}

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const styles: Record<string, string> = {
  completed: "bg-emerald-100 text-emerald-800 border-emerald-200",
  failed: "bg-red-100 text-red-800 border-red-200",
  running: "bg-blue-100 text-blue-800 border-blue-200",
  queued: "bg-amber-100 text-amber-800 border-amber-200",
  profiled: "bg-emerald-100 text-emerald-800 border-emerald-200",
  uploaded: "bg-zinc-100 text-zinc-700 border-zinc-200",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant="outline" className={cn("capitalize", styles[status] ?? "")}>
      {status}
    </Badge>
  );
}

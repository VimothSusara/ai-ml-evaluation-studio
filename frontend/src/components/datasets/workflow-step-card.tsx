import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { CheckCircle2, Circle } from "lucide-react";

export function WorkflowStepCard({
  step,
  title,
  description,
  done,
  active,
  children,
}: {
  step: number;
  title: string;
  description: string;
  done?: boolean;
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card
      className={cn(
        "transition-colors",
        active && "border-zinc-400 ring-1 ring-zinc-200",
        done && !active && "border-emerald-200/80 bg-emerald-50/30",
        !active && !done && "opacity-90",
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start gap-3">
          <span
            className={cn(
              "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
              done
                ? "bg-emerald-600 text-white"
                : active
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-zinc-500",
            )}
          >
            {done ? <CheckCircle2 className="size-4" /> : step}
          </span>
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            <p className="mt-1 text-sm text-zinc-500">{description}</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export function StepChecklist({
  items,
}: {
  items: { label: string; done: boolean }[];
}) {
  return (
    <ul className="mb-4 space-y-1.5 rounded-md border bg-zinc-50/80 px-3 py-2 text-sm">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-2">
          {item.done ? (
            <CheckCircle2 className="size-4 shrink-0 text-emerald-600" />
          ) : (
            <Circle className="size-4 shrink-0 text-zinc-300" />
          )}
          <span className={item.done ? "text-zinc-700" : "text-zinc-500"}>
            {item.label}
          </span>
        </li>
      ))}
    </ul>
  );
}

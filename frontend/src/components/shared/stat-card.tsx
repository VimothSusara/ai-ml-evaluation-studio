import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-1">
        <CardTitle className="text-xs font-medium text-zinc-500">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-semibold tracking-tight">{value}</p>
        {hint && <p className="mt-1 text-xs text-zinc-500">{hint}</p>}
      </CardContent>
    </Card>
  );
}
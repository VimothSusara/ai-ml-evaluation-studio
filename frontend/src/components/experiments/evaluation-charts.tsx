"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { ModelEvaluation } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

function ConfusionMatrix({ plot }: { plot: Record<string, unknown> }) {
  const labels = (plot.labels as string[]) ?? [];
  const matrix = (plot.matrix as number[][]) ?? [];
  const flat = matrix.flat();
  const max = Math.max(...flat, 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Confusion matrix</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="mx-auto border-collapse text-sm">
            <thead>
              <tr>
                <th className="p-2" />
                {labels.map((l) => (
                  <th key={l} className="p-2 text-xs font-medium text-zinc-500">
                    Pred {l}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((row, i) => (
                <tr key={labels[i] ?? i}>
                  <td className="p-2 text-xs font-medium text-zinc-500">
                    Actual {labels[i]}
                  </td>
                  {row.map((val, j) => (
                    <td
                      key={j}
                      className="p-2 text-center text-sm font-medium text-zinc-900"
                      style={{
                        backgroundColor: `rgba(16, 185, 129, ${0.15 + (val / max) * 0.75})`,
                      }}
                    >
                      {val}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function ClassDistribution({ plot }: { plot: Record<string, unknown> }) {
  const labels = (plot.labels as string[]) ?? [];
  const train = (plot.train as number[]) ?? [];
  const test = (plot.test as number[]) ?? [];
  const data = labels.map((label, i) => ({
    label,
    train: train[i] ?? 0,
    test: test[i] ?? 0,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Class distribution</CardTitle>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Bar dataKey="train" fill="#71717a" name="Train" />
            <Bar dataKey="test" fill="#10b981" name="Test" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function RocCurve({ plot }: { plot: Record<string, unknown> }) {
  const points = (plot.points as { fpr: number; tpr: number }[]) ?? [];
  const aucVal = plot.auc as number | undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          ROC curve{aucVal != null ? ` (AUC ${aucVal.toFixed(3)})` : ""}
        </CardTitle>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="fpr"
              type="number"
              domain={[0, 1]}
              label={{ value: "FPR", position: "insideBottom", offset: -5 }}
            />
            <YAxis
              dataKey="tpr"
              type="number"
              domain={[0, 1]}
              label={{ value: "TPR", angle: -90, position: "insideLeft" }}
            />
            <Tooltip />
            <Line type="monotone" dataKey="tpr" stroke="#10b981" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function PredVsActual({ plot }: { plot: Record<string, unknown> }) {
  const points = (plot.points as { actual: number; predicted: number }[]) ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Predicted vs actual</CardTitle>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="actual" type="number" name="Actual" />
            <YAxis dataKey="predicted" type="number" name="Predicted" />
            <ZAxis range={[40, 40]} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={points} fill="#10b981" />
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function ResidualHist({ plot }: { plot: Record<string, unknown> }) {
  const bins = (plot.bins as number[]) ?? [];
  const counts = (plot.counts as number[]) ?? [];
  const data = counts.map((count, i) => ({
    bin: `${bins[i]?.toFixed(2)} – ${bins[i + 1]?.toFixed(2)}`,
    count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Residual distribution</CardTitle>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="bin"
              interval={0}
              angle={-25}
              textAnchor="end"
              height={70}
            />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" fill="#71717a" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function EvaluationCharts({
  evaluation,
}: {
  evaluation: ModelEvaluation;
}) {
  const plots = evaluation.plots ?? {};

  return (
    <div className="space-y-4">
      {evaluation.warnings?.length > 0 && (
        <Alert className="border-zinc-200 bg-zinc-50">
          <AlertTitle className="text-zinc-800">Insights</AlertTitle>
          <AlertDescription>
            <ul className="list-inside list-disc text-sm text-zinc-600">
              {evaluation.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {plots.confusion_matrix != null ? (
          <ConfusionMatrix
            plot={plots.confusion_matrix as Record<string, unknown>}
          />
        ) : null}
        {plots.class_distribution != null ? (
          <ClassDistribution
            plot={plots.class_distribution as Record<string, unknown>}
          />
        ) : null}
        {plots.roc != null ? (
          <RocCurve plot={plots.roc as Record<string, unknown>} />
        ) : null}
        {plots.pred_vs_actual != null ? (
          <PredVsActual
            plot={plots.pred_vs_actual as Record<string, unknown>}
          />
        ) : null}
        {plots.residual_hist != null ? (
          <ResidualHist plot={plots.residual_hist as Record<string, unknown>} />
        ) : null}
      </div>
    </div>
  );
}

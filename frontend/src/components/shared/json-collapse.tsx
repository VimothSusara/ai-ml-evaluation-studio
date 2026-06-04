export function JsonCollapse({
    title = "Raw JSON",
    data,
  }: {
    title?: string;
    data: unknown;
  }) {
    return (
      <details className="rounded-lg border bg-zinc-50">
        <summary className="cursor-pointer px-4 py-2 text-sm font-medium text-zinc-600">
          {title}
        </summary>
        <pre className="max-h-72 overflow-auto border-t p-4 text-xs text-zinc-700">
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    );
  }
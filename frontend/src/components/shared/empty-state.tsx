export function EmptyState({
    title,
    description,
  }: {
    title: string;
    description?: string;
  }) {
    return (
      <div className="rounded-lg border border-dashed bg-white p-10 text-center">
        <p className="font-medium text-zinc-800">{title}</p>
        {description && (
          <p className="mt-2 text-sm text-zinc-500">{description}</p>
        )}
      </div>
    );
  }
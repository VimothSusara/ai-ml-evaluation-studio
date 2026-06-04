export function PageHeader({
    title,
    description,
    badge,
  }: {
    title: string;
    description?: string;
    badge?: React.ReactNode;
  }) {
    return (
      <div className="space-y-1">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          {badge}
        </div>
        {description && (
          <p className="text-sm text-zinc-500">{description}</p>
        )}
      </div>
    );
  }
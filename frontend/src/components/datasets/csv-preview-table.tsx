import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CsvPreview } from "@/lib/csv-preview";

export function CsvPreviewTable({ preview }: { preview: CsvPreview }) {
  const colCount = preview.headers.length;

  return (
    <div className="max-h-80 overflow-y-auto overflow-x-auto rounded-md border bg-white">
      <Table className="min-w-max">
        <TableHeader>
          <TableRow>
            {preview.headers.map((h) => (
              <TableHead
                key={h}
                className="whitespace-nowrap px-3 text-xs font-semibold"
              >
                {h}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {preview.rows.map((row, i) => (
            <TableRow key={i}>
              {Array.from({ length: colCount }).map((_, j) => (
                <TableCell
                  key={j}
                  className="max-w-[200px] truncate whitespace-nowrap px-3 text-xs"
                  title={row[j] ?? ""}
                >
                  {row[j] ?? ""}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export interface CsvPreview {
  fileName: string;
  fileSizeBytes: number;
  headers: string[];
  rows: string[][];
  estimatedRowCount: number;
}

/** Parse first rows of a CSV file client-side for upload confirmation. */
export async function parseCsvPreview(
  file: File,
  maxPreviewRows = 10,
): Promise<CsvPreview> {
  const chunk = file.slice(0, 512 * 1024);
  const text = await chunk.text();
  const lines = text.split(/\r?\n/).filter((line) => line.trim().length > 0);

  if (lines.length === 0) {
    throw new Error("File appears empty");
  }

  const headers = parseCsvLine(lines[0]);
  const rows: string[][] = [];
  for (let i = 1; i < lines.length && rows.length < maxPreviewRows; i++) {
    rows.push(parseCsvLine(lines[i]));
  }

  const estimatedRowCount = Math.max(lines.length - 1, rows.length);

  return {
    fileName: file.name,
    fileSizeBytes: file.size,
    headers,
    rows,
    estimatedRowCount,
  };
}

function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (ch === "," && !inQuotes) {
      result.push(current.trim());
      current = "";
      continue;
    }
    current += ch;
  }
  result.push(current.trim());
  return result;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

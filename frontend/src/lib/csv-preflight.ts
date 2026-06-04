import type { CsvPreview } from "@/lib/csv-preview";

const ID_LIKE_NAMES = new Set(["id", "uuid", "guid", "key", "index"]);

const LABEL_HEADER_HINT =
  /^(category|label|class|target|type|spam|ham|sentiment|outcome|survived)$/i;
const TEXT_HEADER_HINT = /^(message|text|body|content|tweet|review|comment|sms)$/i;

export interface CsvPreflightResult {
  errors: string[];
  warnings: string[];
  usableColumnCount: number;
  junkHeaders: string[];
  canUpload: boolean;
}

/** Header-only checks aligned with backend profiling junk rules (no full-file scan). */
function isJunkHeaderName(name: string): boolean {
  const stripped = name.trim();
  const lower = stripped.toLowerCase();
  if (stripped === "" || stripped === "#") return true;
  if (lower.startsWith("unnamed")) return true;
  if (ID_LIKE_NAMES.has(lower) || lower.endsWith("_id")) return true;
  return false;
}

export function assessCsvPreview(preview: CsvPreview): CsvPreflightResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const junkHeaders = preview.headers.filter(isJunkHeaderName);
  const usableHeaders = preview.headers.filter((h) => !isJunkHeaderName(h));

  if (preview.headers.length === 0) {
    errors.push("No column headers found.");
  }

  for (const h of junkHeaders) {
    warnings.push(
      `Column "${h}" looks like an index or ID — it will be removed automatically when profiling.`,
    );
  }

  if (usableHeaders.length < 2) {
    errors.push(
      `After removing index-like columns, only ${usableHeaders.length} usable column(s) remain. You need at least 2 (features + target).`,
    );
  }

  if (preview.estimatedRowCount < 10) {
    warnings.push(
      "Very few rows detected in the file preview — metrics may be unreliable.",
    );
  }

  const colCount = preview.headers.length;
  const raggedRows = preview.rows.filter((r) => r.length !== colCount).length;
  if (raggedRows > 0) {
    warnings.push(
      `${raggedRows} preview row(s) have a different column count than the header — the CSV may be malformed (quotes, commas in text).`,
    );
  }

  const labelLike = usableHeaders.filter((h) => LABEL_HEADER_HINT.test(h.trim()));
  const textLike = usableHeaders.filter((h) => TEXT_HEADER_HINT.test(h.trim()));
  for (const h of labelLike) {
    warnings.push(
      `"${h}" looks like a label column — select it as the target (e.g. spam/ham), not the text field.`,
    );
  }
  if (textLike.length > 0 && labelLike.length > 0) {
    warnings.push(
      `Text columns (${textLike.join(", ")}) are not supported as targets in tabular v1 — use ${labelLike.join(" or ")}.`,
    );
  }

  for (const row of preview.rows) {
    const cell = row.join(" ");
    if (/^\s*\{/.test(cell) && cell.includes("mode")) {
      warnings.push(
        "Preview contains JSON-like text — ensure commas/quotes in Message cells are properly quoted in the CSV.",
      );
      break;
    }
  }

  return {
    errors,
    warnings,
    usableColumnCount: usableHeaders.length,
    junkHeaders,
    canUpload: errors.length === 0,
  };
}

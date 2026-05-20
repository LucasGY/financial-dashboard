const SHANGHAI_TIME_ZONE = "Asia/Shanghai";

function parseUtcDate(value: string) {
  const normalized = value.trim();
  if (!normalized) return null;
  if (normalized.endsWith("Z") || /[+-]\d{2}:?\d{2}$/.test(normalized)) {
    const parsed = new Date(normalized);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }
  const parsed = new Date(`${normalized.replace(" ", "T")}:00Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatShanghaiDate(value: string) {
  const date = parseUtcDate(value);
  if (!date) return value.slice(0, 10) || "Unknown";
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: SHANGHAI_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const year = parts.find((part) => part.type === "year")?.value;
  const month = parts.find((part) => part.type === "month")?.value;
  const day = parts.find((part) => part.type === "day")?.value;
  return year && month && day ? `${year}-${month}-${day}` : value.slice(0, 10) || "Unknown";
}

export function formatShanghaiTime(value: string) {
  const date = parseUtcDate(value);
  if (!date) return value.slice(11, 16) || value;
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: SHANGHAI_TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(date);
}

export function formatShanghaiDateTime(value: string) {
  const datePart = formatShanghaiDate(value);
  const timePart = formatShanghaiTime(value);
  return datePart === "Unknown" ? timePart : `${datePart} ${timePart}`;
}

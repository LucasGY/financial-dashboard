type FormatLanguage = "zh" | "en";

const getLocale = (language?: FormatLanguage) => {
  if (language) {
    return language === "en" ? "en-US" : "zh-CN";
  }

  if (typeof document === "undefined") {
    return "zh-CN";
  }
  return document.documentElement.lang === "en" ? "en-US" : "zh-CN";
};

export const formatCompactDate = (value: string, language?: FormatLanguage) => {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(getLocale(language), {
        month: "numeric",
        day: "numeric"
      }).format(date);
};

export const formatMonthDate = (value: string, language?: FormatLanguage) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  if (getLocale(language) === "en-US") {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      year: "numeric"
    }).format(date);
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit"
  }).format(date).replace("/", "-");
};

export const formatNumber = (value: number | null | undefined, digits = 1) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  return value.toFixed(digits);
};

export const formatPercent = (value: number | null | undefined, digits = 1) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  return `${value.toFixed(digits)}%`;
};

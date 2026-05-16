export type Language = "zh" | "en";

export const EVENT_LABELS: Record<string, Record<Language, string>> = {
  model_release: { zh: "模型发布 / 更新", en: "Model release / update" },
  product_tool_update: { zh: "产品 / 工具更新", en: "Product / tool update" },
  industry: { zh: "行业动态", en: "Industry" },
  paper_research: { zh: "论文研究", en: "Research paper" },
  tips_opinion: { zh: "技巧与观点", en: "Tips & opinions" },
  kol_opinion: { zh: "KOL观点", en: "KOL opinion" },
  macro: { zh: "宏观", en: "Macro" },
  market: { zh: "市场", en: "Market" },
  company_industry: { zh: "公司 / 行业", en: "Company / industry" },
  interview: { zh: "访谈", en: "Interview" },
  manual_saved: { zh: "手动收藏", en: "Manual save" },
  close_reading: { zh: "精读笔记", en: "Close reading" },
  agent: { zh: "Agent", en: "Agent" },
};

export function labelForEvent(tag: string, language: Language) {
  return EVENT_LABELS[tag]?.[language] ?? tag;
}

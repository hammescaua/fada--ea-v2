import type { EventType, ProductCategory } from "@/lib/api";

export const EVENT_TYPES: EventType[] = [
  "PLANTING",
  "BASE_FERTILIZATION",
  "TOP_DRESSING",
  "HERBICIDE",
  "FUNGICIDE",
  "INSECTICIDE",
  "FOLIAR",
  "IRRIGATION",
  "HARVEST",
  "OTHER",
];

export const EVENT_TYPE_LABELS: Record<EventType, string> = {
  PLANTING: "Plantio",
  BASE_FERTILIZATION: "Adubação de base",
  TOP_DRESSING: "Adubação de cobertura",
  HERBICIDE: "Herbicida",
  FUNGICIDE: "Fungicida",
  INSECTICIDE: "Inseticida",
  FOLIAR: "Foliar",
  IRRIGATION: "Irrigação",
  HARVEST: "Colheita",
  OTHER: "Outro",
};

/** Tailwind classes for the timeline dot + badge of each event type group. */
export interface EventStyle {
  dot: string;
  badge: string;
}

export function eventStyle(type: EventType): EventStyle {
  switch (type) {
    case "PLANTING":
    case "HARVEST":
      return {
        dot: "bg-green-500 ring-green-100",
        badge: "bg-green-100 text-green-800 border-green-200",
      };
    case "BASE_FERTILIZATION":
    case "TOP_DRESSING":
      return {
        dot: "bg-amber-500 ring-amber-100",
        badge: "bg-amber-100 text-amber-800 border-amber-200",
      };
    case "HERBICIDE":
      return {
        dot: "bg-rose-500 ring-rose-100",
        badge: "bg-rose-100 text-rose-800 border-rose-200",
      };
    case "FUNGICIDE":
      return {
        dot: "bg-violet-500 ring-violet-100",
        badge: "bg-violet-100 text-violet-800 border-violet-200",
      };
    case "INSECTICIDE":
      return {
        dot: "bg-orange-500 ring-orange-100",
        badge: "bg-orange-100 text-orange-800 border-orange-200",
      };
    case "FOLIAR":
      return {
        dot: "bg-teal-500 ring-teal-100",
        badge: "bg-teal-100 text-teal-800 border-teal-200",
      };
    case "IRRIGATION":
      return {
        dot: "bg-blue-500 ring-blue-100",
        badge: "bg-blue-100 text-blue-800 border-blue-200",
      };
    case "OTHER":
    default:
      return {
        dot: "bg-slate-400 ring-slate-100",
        badge: "bg-muted text-muted-foreground border-border",
      };
  }
}

export const PRODUCT_CATEGORIES: ProductCategory[] = [
  "FERTILIZER",
  "SEED",
  "HERBICIDE",
  "FUNGICIDE",
  "INSECTICIDE",
  "FOLIAR",
  "ADJUVANT",
  "OTHER",
];

export const PRODUCT_CATEGORY_LABELS: Record<ProductCategory, string> = {
  FERTILIZER: "Fertilizante",
  SEED: "Semente",
  HERBICIDE: "Herbicida",
  FUNGICIDE: "Fungicida",
  INSECTICIDE: "Inseticida",
  FOLIAR: "Foliar",
  ADJUVANT: "Adjuvante",
  OTHER: "Outro",
};

/** Translate a cost_by_category key to a pt-BR label when possible. */
export function costCategoryLabel(key: string): string {
  const upper = key.toUpperCase();
  if (upper in EVENT_TYPE_LABELS) {
    return EVENT_TYPE_LABELS[upper as EventType];
  }
  if (upper in PRODUCT_CATEGORY_LABELS) {
    return PRODUCT_CATEGORY_LABELS[upper as ProductCategory];
  }
  return key;
}

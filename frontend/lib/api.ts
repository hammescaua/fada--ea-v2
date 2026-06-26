// Typed API client for the FADA backend.

/**
 * Normaliza a base da API para evitar pegadinhas comuns de configuração:
 * - remove barra(s) no final;
 * - remove um "/api/v1" colocado por engano no fim (o cliente já adiciona).
 */
function normalizeBase(raw: string): string {
  return raw
    .trim()
    .replace(/\/+$/, "")
    .replace(/\/api\/v1\/?$/, "");
}

export const API_BASE = normalizeBase(
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
);

export const API_V1 = `${API_BASE}/api/v1`;

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

export type Uf = "RS";
export type Crop = "soja";

export interface Scenario {
  name: string;
  yield_sc_ha: number;
}

export interface Phenology {
  r1_begin_flowering: string;
  r6_full_seed: string;
}

export interface PlantingWindow {
  start: string;
  end: string;
  optimal_start: string;
  optimal_end: string;
  rationale: string;
}

export interface ClimaticRisk {
  factor: string;
  severity: string;
  description: string;
  metric: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Municipalities
// ---------------------------------------------------------------------------

export interface Municipality {
  code: number;
  name: string;
}

// ---------------------------------------------------------------------------
// Regional intelligence
// ---------------------------------------------------------------------------

export interface RegionalIntelligenceRequest {
  municipality: string;
  uf: Uf;
  crop: Crop;
  season: string;
}

export interface RegionalIntelligenceResponse {
  municipality: string;
  municipality_code: number;
  crop: string;
  season: string;
  harvest_year: number;
  estimated_yield_sc_ha: number;
  confidence_interval_sc_ha: [number, number];
  scenarios: Scenario[];
  climatic_risks: ClimaticRisk[];
  planting_window: PlantingWindow;
  explanation: string;
  n_years: number;
  reasoning: { n_years: number; method: string; interval_basis: string };
  data_sources: string[];
  disclaimer: string;
}

// ---------------------------------------------------------------------------
// Planting date simulation
// ---------------------------------------------------------------------------

export interface PlantingDateSimulationRequest {
  municipality: string;
  uf: Uf;
  crop: Crop;
  season: string;
  planting_date: string;
  risk_aversion: number;
}

export interface PlantingDateSimulationResponse {
  municipality: string;
  municipality_code: number;
  season: string;
  harvest_year: number;
  requested_planting_date: string;
  evaluated_planting_date: string;
  snapped_note: string | null;
  within_zarc: boolean;
  phenology: Phenology;
  expected_yield_sc_ha: number;
  delta_vs_baseline_sc_ha: number;
  confidence_interval_sc_ha: [number, number];
  scenarios: Scenario[];
  downside_sc_ha: number;
  stability_iqr_sc_ha: number;
  risk_score: number;
  risk_drivers: Record<string, number>;
  n_years: number;
  explanation: string;
  scope_note: string;
}

// ---------------------------------------------------------------------------
// Planting window optimization
// ---------------------------------------------------------------------------

export interface PlantingWindowOptimizationRequest {
  municipality: string;
  uf: Uf;
  crop: Crop;
  season: string;
  risk_aversion: number;
  top_n: number;
}

export interface PlantingRecommendation {
  planting_date: string;
  phenology: Phenology;
  expected_yield_sc_ha: number;
  delta_vs_baseline_sc_ha: number;
  confidence_interval_sc_ha: [number, number];
  scenarios: Scenario[];
  downside_sc_ha: number;
  stability_iqr_sc_ha: number;
  risk_score: number;
  risk_drivers: Record<string, number>;
  n_years: number;
  justification: string;
}

export interface PlantingWindowOptimizationResponse {
  municipality: string;
  municipality_code: number;
  season: string;
  harvest_year: number;
  risk_aversion: number;
  objective: string;
  zarc_window: string;
  baseline_expected_sc_ha: number;
  top_recommendations: PlantingRecommendation[];
  scope_note: string;
}

// ---------------------------------------------------------------------------
// Assistant
// ---------------------------------------------------------------------------

export interface AssistantRequest {
  message: string;
  municipality?: string | null;
  // O backend já aceita estes — o contexto global (fazenda/safra) os preenche,
  // habilitando perguntas de custo/orçamento/decisão/personalização.
  farm_id?: number | null;
  crop_cycle_id?: number | null;
  price_per_bag?: number | null;
}

export interface CropCycleListItem {
  id: number;
  field_id: number;
  field_name: string;
  crop: string;
  season: string;
  harvest_year: number;
  area_ha: number | null;
  target_yield_sc_ha: number | null;
  has_actual_yield: boolean;
}

export interface AssistantResponse {
  intent: string;
  parameters: Record<string, unknown>;
  answer: string;
  result: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// Agronomic profile: personalização a priori (perfil padronizado do talhão)
// ---------------------------------------------------------------------------

export interface AgronomicFactorOption {
  value: string;
  label: string;
  effect_pct: number;
}

export interface AgronomicFactor {
  key: string;
  question: string;
  rationale: string;
  confidence: string;
  essential?: boolean;
  explanation?: string | null;
  sources?: string[];
  options: AgronomicFactorOption[];
}

export interface KnowledgeEntry {
  key: string;
  title: string;
  explanation: string;
  practical: string;
  sources: string[];
}

export interface AppliedFactor {
  key: string;
  question: string;
  option_label: string;
  effect_pct: number;
  rationale: string;
  confidence: string;
}

export interface AgronomicEstimate {
  municipality: string;
  municipality_code: number;
  crop: string;
  season: string;
  harvest_year: number;
  regional: { point_sc_ha: number; interval_sc_ha: [number, number] };
  personalized: {
    point_sc_ha: number;
    interval_sc_ha: [number, number];
    scenarios: Scenario[];
  };
  adjustment: {
    multiplier: number;
    total_effect_pct: number;
    clamped: boolean;
    n_factors: number;
    factors: AppliedFactor[];
  };
  recommendations: {
    key: string;
    question: string;
    current_label: string;
    target_label: string;
    gain_pct: number;
    gain_sc_ha: number;
    rationale: string;
    confidence: string;
  }[];
  narrative?: string | null;
  water_sensitivity_note?: string | null;
  climatic_risks: ClimaticRisk[];
  data_sources: string[];
  disclaimer: string;
}

export interface ProfileCompleteness {
  filled: string[];
  missing: string[];
  filled_count: number;
  essential_total: number;
  pct: number;
}

export interface AgronomicEstimateRequest {
  municipality: string;
  crop?: string;
  season?: string;
  profile: Record<string, string>;
}

export interface ManejoHistory {
  field_id: number;
  field_name: string;
  n_seasons: number;
  history: {
    crop_cycle_id: number;
    season: string;
    harvest_year: number;
    manejo_source: string;
    manejo_effect_pct: number;
    n_factors: number;
    predicted_sc_ha: number | null;
    actual_sc_ha: number | null;
    delta_vs_predicted_pct: number | null;
  }[];
  note: string;
}

export interface FieldLearnedEstimate {
  field_id: number;
  field_name: string;
  season: string;
  regional: { point_sc_ha: number; interval_sc_ha: [number, number] };
  a_priori_profile_pct: number;
  observed_from_harvests_pct: number;
  applied_pct: number;
  n_harvests: number;
  confidence_score: number;
  adaptation_level: string;
  learned: {
    point_sc_ha: number;
    interval_sc_ha: [number, number];
    scenarios: Scenario[];
  };
  residual_history: {
    harvest_year: number;
    actual_sc_ha: number;
    regional_fitted_sc_ha: number;
    residual_pct: number;
  }[];
  explanation: string;
}

export interface SoilAnalysisRequest {
  p_mehlich?: number;
  k_mehlich?: number;
  clay_pct?: number;
  ctc?: number;
  ph_water?: number;
  al_saturation_pct?: number;
  organic_matter_pct?: number;
}

export interface SoilAnalysisResult {
  profile_fragment: Record<string, string>;
  notes: { factor: string; value: string; basis: string }[];
  disclaimer: string;
}

export interface SoilSuggestion {
  field_id: number;
  municipality_code: number;
  ordem_dominante: string | null;
  confidence: string | null;
  profile_fragment: Record<string, string>;
  source: string | null;
  note: string | null;
}

// ---------------------------------------------------------------------------
// Season brief: planejamento pré-safra (síntese de decisão)
// ---------------------------------------------------------------------------

export interface SeasonBrief {
  municipality: string;
  municipality_code: number;
  crop: string;
  season: string;
  harvest_year: number;
  yield: {
    expected_sc_ha: number;
    interval_sc_ha: [number, number];
    scenarios: Scenario[];
    risks: ClimaticRisk[];
    n_years: number;
    personalized?: boolean;
    adjustment?: {
      multiplier: number;
      total_effect_pct: number;
      regional_point_sc_ha: number;
      n_factors: number;
      factors: AppliedFactor[];
    } | null;
  };
  planting: {
    zarc: {
      safra: string;
      portaria: string;
      manejo: string;
      windows_by_risk: Record<string, { start: string; end: string }[]>;
    } | null;
    best_date: {
      planting_date: string;
      expected_yield_sc_ha: number;
      downside_sc_ha: number;
      justification: string;
    } | null;
  };
  price: {
    price_per_bag: number;
    source: string;
    day?: string;
    unit?: string;
    is_stale?: boolean;
  } | null;
  cost: {
    coe_per_ha: number;
    cot_per_ha: number;
    ct_per_ha: number;
    source: string;
    safra: string;
  } | null;
  margin: {
    price_per_bag: number;
    cost_basis: string;
    cost_per_ha_cot: number;
    break_even_yield_sc_ha: { coe: number; cot: number; ct: number };
    scenarios: FinancialScenario[];
    expected: {
      yield_sc_ha: number;
      revenue_per_ha: number;
      profit_per_ha: number;
      margin_pct: number;
    };
    cost_adjustment?: {
      multiplier: number;
      total_effect_pct: number;
      reference_cot_per_ha: number;
      factors: { key: string; option: string; effect_pct: number; rationale: string }[];
    } | null;
  } | null;
  recommendations:
    | {
        key: string;
        question: string;
        current_label: string;
        target_label: string;
        gain_sc_ha: number;
        yield_gain_rs_ha: number;
        cost_change_rs_ha: number;
        net_gain_rs_ha: number;
        rationale: string;
        confidence: string;
      }[]
    | null;
  narrative: string[];
  verdict: string;
  data_sources: string[];
  disclaimer: string;
}

// ---------------------------------------------------------------------------
// ZARC: janela oficial de plantio (MAPA) — fonte de verdade do zoneamento
// ---------------------------------------------------------------------------

export interface ZarcWindow {
  start: string; // MM-DD
  end: string; // MM-DD
}

export interface ZarcPlantingWindow {
  crop: string;
  uf: string;
  safra: string;
  manejo: string;
  portaria: string;
  source: string;
  fetched_at: string;
  note: string;
  municipality_code: number;
  municipality_name: string;
  windows_by_risk: Record<string, ZarcWindow[]>;
  disclaimer: string;
  planting_date: string | null;
  within_zarc: boolean | null;
  risk_level: number | null;
  interpretation: string | null;
}

// ---------------------------------------------------------------------------
// Weather: previsão + alertas agronômicos (Open-Meteo) — proativo, com incerteza
// ---------------------------------------------------------------------------

export interface WeatherAlert {
  code: string;
  severity: string; // "info" | "atenção" | "alerta"
  title: string;
  detail: string;
  starts_on: string;
  ends_on: string;
  confidence: string; // "alta" | "média" | "baixa"
  evidence: Record<string, unknown>;
}

export interface DailyForecastPoint {
  day: string;
  tmin: number;
  tmax: number;
  precipitation_mm: number;
  precipitation_prob: number;
  wind_max_kmh: number;
}

export interface WeatherForecast {
  latitude: number;
  longitude: number;
  n_days: number;
  from_day: string | null;
  to_day: string | null;
  location_source: string | null;
  alerts: WeatherAlert[];
  forecast: DailyForecastPoint[];
  source: string;
  disclaimer: string;
}

// ---------------------------------------------------------------------------
// Ground truth: farms / fields / crop-cycles / observations
// ---------------------------------------------------------------------------

export interface CreateFarmRequest {
  name: string;
  municipality_code: number;
}

export interface Farm {
  id: number;
  name: string;
  municipality_code: number;
  created_at: string;
}

export interface CreateFieldRequest {
  name: string;
  area_ha: number;
  latitude?: number;
  longitude?: number;
}

export interface Field {
  id: number;
  farm_id: number;
  name: string;
  area_ha: number;
  latitude?: number | null;
  longitude?: number | null;
  created_at: string;
}

export interface CreateCropCycleRequest {
  crop: Crop;
  season: string;
  planting_date?: string;
}

export interface CropCycle {
  id: number;
  field_id: number;
  crop: string;
  season: string;
  harvest_year: number;
  planting_date: string | null;
  created_at: string;
}

export interface CreateYieldObservationRequest {
  crop_cycle_id: number;
  actual_yield_sc_ha: number;
  area_ha: number;
  actual_planting_date?: string;
  actual_harvest_date?: string;
  cultivar?: string;
  notes?: string;
}

export interface YieldObservation {
  id: number;
  crop_cycle_id: number;
  actual_yield_sc_ha: number;
  area_ha: number;
  actual_planting_date: string | null;
  actual_harvest_date: string | null;
  cultivar: string | null;
  notes: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Digital Twin: crop-cycle detail, agricultural events, financials
// ---------------------------------------------------------------------------

export type EventType =
  | "PLANTING"
  | "BASE_FERTILIZATION"
  | "TOP_DRESSING"
  | "HERBICIDE"
  | "FUNGICIDE"
  | "INSECTICIDE"
  | "FOLIAR"
  | "IRRIGATION"
  | "HARVEST"
  | "OTHER";

export interface CropCycleDetail {
  id: number;
  field_id: number;
  crop: string;
  season: string;
  harvest_year: number;
  area_ha: number | null;
  cultivar: string | null;
  planned_planting_date: string | null;
  actual_planting_date: string | null;
  harvest_date: string | null;
  actual_yield_sc_ha: number | null;
  notes: string | null;
  created_at: string | null;
}

export interface UpdateCropCycleRequest {
  area_ha?: number;
  cultivar?: string;
  planned_planting_date?: string;
  actual_planting_date?: string;
  harvest_date?: string;
  actual_yield_sc_ha?: number;
  target_yield_sc_ha?: number;
  expected_price_per_bag?: number;
  notes?: string;
}

export interface AgriculturalEvent {
  id: number;
  crop_cycle_id: number;
  event_type: EventType;
  event_date: string;
  product_name: string | null;
  product_id: number | null;
  quantity: number | null;
  unit: string | null;
  cost: number | null;
  notes: string | null;
  created_at: string | null;
}

export interface CreateAgriculturalEventRequest {
  event_type: EventType;
  event_date: string;
  product_name?: string;
  product_id?: number;
  quantity?: number;
  unit?: string;
  cost?: number;
  notes?: string;
}

export interface CostBreakdown {
  total_cost: number;
  area_ha: number;
  cost_per_hectare: number;
  cost_per_bag: number | null;
  yield_sc_ha: number | null;
  n_applications: number;
  cost_by_category: Record<string, number>;
}

export interface FinancialScenario {
  name: string;
  yield_sc_ha: number;
  price_per_bag: number;
  revenue: number;
  total_cost: number;
  profit: number;
  margin_pct: number;
  profit_per_hectare: number;
}

export interface Financials {
  breakdown: CostBreakdown;
  price_per_bag: number;
  price_source: string;
  break_even_yield_sc_ha: number;
  yield_source: string;
  scenarios: FinancialScenario[];
}

export interface FinancialsRequest {
  // Opcional: se omitido, o backend usa o preço esperado da safra ou a cotação
  // CEPEA/ESALQ ao vivo (data pública oficial).
  price_per_bag?: number;
}

// ---------------------------------------------------------------------------
// Market: preço observado de fonte oficial (CEPEA/ESALQ) — sem forecast
// ---------------------------------------------------------------------------

export interface PricePoint {
  day: string;
  value: number;
}

export interface PriceSummary {
  latest_value: number;
  latest_day: string;
  n_points: number;
  window_days: number;
  mean_value: number;
  min_value: number;
  max_value: number;
  change_pct: number;
  staleness_days: number;
  is_stale: boolean;
}

export interface MarketPrice {
  crop: string;
  source: string;
  place: string;
  unit: string;
  fetched_at: string;
  summary: PriceSummary;
  series: PricePoint[];
  disclaimer: string;
}

// Benchmark de custo de produção (referência regional CONAB) — sem juízo de valor.

export interface CostComponent {
  item: string;
  value_per_ha: number;
  share_pct: number;
}

export interface CostComparison {
  actual_per_ha: number;
  reference_label: string;
  reference_per_ha: number;
  delta_per_ha: number;
  ratio_pct: number;
  descriptor: string; // "abaixo" | "na média" | "acima"
}

export interface CostBenchmarkComparison {
  crop: string;
  uf: string;
  safra: string;
  technology: string;
  source: string;
  fetched_at: string;
  coe_per_ha: number;
  cot_per_ha: number;
  ct_per_ha: number;
  actual_cost_per_ha: number;
  primary: string; // chave de references considerada principal (ex.: "coe")
  references: Record<string, CostComparison>;
  components: CostComponent[];
  disclaimer: string;
}

export type ProductCategory =
  | "FERTILIZER"
  | "SEED"
  | "HERBICIDE"
  | "FUNGICIDE"
  | "INSECTICIDE"
  | "FOLIAR"
  | "ADJUVANT"
  | "OTHER";

export interface Product {
  id: number;
  category: ProductCategory;
  commercial_name: string;
  active_ingredient: string | null;
  formulation: string | null;
  unit: string | null;
  description: string | null;
  created_at: string | null;
}

export interface CreateProductRequest {
  category: ProductCategory;
  commercial_name: string;
  active_ingredient?: string;
  formulation?: string;
  unit?: string;
  description?: string;
}

// ---------------------------------------------------------------------------
// Adaptive Intelligence: farm performance profile & personalized prediction
// ---------------------------------------------------------------------------

export interface ResidualPoint {
  harvest_year: number;
  actual_sc_ha: number;
  regional_fitted_sc_ha: number;
  residual_sc_ha: number;
  residual_pct: number;
}

export interface FarmProfile {
  farm_id: number;
  number_of_cycles: number;
  bias_percentage: number;
  mean_relative_residual: number;
  mean_residual_sc_ha: number;
  median_residual_sc_ha: number;
  variance_relative: number;
  last_updated: string | null;
  residual_history: ResidualPoint[];
}

export interface PersonalizedIntelligenceRequest {
  farm_id: number;
  season: string;
}

export interface PersonalizedIntelligence {
  farm_id: number;
  municipality_code: number;
  season: string;
  harvest_year: number;
  regional_prediction: {
    point_sc_ha: number;
    interval_sc_ha: [number, number];
  };
  farm_adjustment: {
    applied_pct: number;
    observed_bias_pct: number;
    n_cycles: number;
  };
  personalized_prediction: {
    point_sc_ha: number;
    interval_sc_ha: [number, number];
    scenarios: Scenario[];
  };
  confidence_score: number;
  adaptation_level: string;
  explanation: string;
}

// ---------------------------------------------------------------------------
// Calibration: backtest of the regional vs personalized predictors
// ---------------------------------------------------------------------------

export interface CoverageDetail {
  nominal: number;
  observed: number;
  wilson_low: number;
  wilson_high: number;
  verdict: string;
}

export interface ReliabilityPoint {
  nominal: number;
  observed: number;
  wilson_low: number;
  wilson_high: number;
}

export interface CalibrationReport {
  label: string;
  n_predictions: number;
  coverage_50: number;
  coverage_80: number;
  coverage_90: number;
  coverage_95: number;
  coverage_detail: CoverageDetail[];
  mean_width: number;
  median_width: number;
  relative_width_pct: number;
  mae: number;
  rmse: number;
  bias: number;
  pinball: Record<string, number>; // keys: p10, p50, p90, mean
  reliability_curve: ReliabilityPoint[];
  overconfident: boolean;
  underconfident: boolean;
  interpretation: string;
}

export interface Calibration {
  method: string;
  ground_truth: string;
  note: string;
  regional: CalibrationReport;
  personalized: CalibrationReport;
}

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (body.detail) {
        detail = JSON.stringify(body.detail);
      }
    } catch {
      // ignore body parse errors
    }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

// Timeout padrão dos requests (evita spinner infinito se o backend pendurar).
const TIMEOUT_MS = 15_000;

async function request(path: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(`${API_V1}${path}`, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("Tempo de resposta esgotado. Tente novamente.", 408);
    }
    throw err; // "Failed to fetch" etc. é tratado na UI (states.tsx)
  } finally {
    clearTimeout(timer);
  }
}

async function get<T>(path: string): Promise<T> {
  return handle<T>(await request(path, { headers: { Accept: "application/json" } }));
}

async function post<TBody, TResp>(path: string, body: TBody): Promise<TResp> {
  return handle<TResp>(
    await request(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    })
  );
}

async function patch<TBody, TResp>(path: string, body: TBody): Promise<TResp> {
  return handle<TResp>(
    await request(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    })
  );
}

async function put<TBody, TResp>(path: string, body: TBody): Promise<TResp> {
  return handle<TResp>(
    await request(path, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    })
  );
}

// ---------------------------------------------------------------------------
// Field Intelligence + Insights
// ---------------------------------------------------------------------------

export interface FieldSummary {
  field_id: number;
  field_name: string;
  n_seasons: number;
  mean_actual_sc_ha: number;
  bias_vs_region_pct: number;
  yield_stability_std_pct: number | null;
  mean_cost_per_ha: number | null;
  n_seasons_with_cost: number;
  latest_year: number;
  latest_actual_sc_ha: number;
  cost_trend: Record<string, unknown> | null;
}

export interface FieldAnalytics {
  farm_id: number;
  n_fields: number;
  n_records: number;
  fields: FieldSummary[];
}

export interface Insight {
  type: string;
  scope: string;
  field_id: number | null;
  title: string;
  detail: string;
  evidence: Record<string, unknown>;
  confidence: string;
}

export interface Insights {
  farm_id: number;
  n_insights: number;
  insights: Insight[];
  note: string;
}

// ---------------------------------------------------------------------------
// In-season: planning, budget, agenda, quick capture
// ---------------------------------------------------------------------------

export interface PlannedEvent {
  id: number;
  crop_cycle_id: number;
  event_type: EventType;
  planned_date: string;
  product_name: string | null;
  quantity: number | null;
  unit: string | null;
  expected_cost: number | null;
  notes: string | null;
}

export interface CreatePlannedEventRequest {
  event_type: EventType;
  planned_date: string;
  product_name?: string;
  quantity?: number;
  unit?: string;
  expected_cost?: number;
  notes?: string;
}

export interface PlanVsActual {
  planned_total_cost: number;
  actual_total_cost: number;
  cost_variance: number;
  cost_variance_pct: number | null;
  pct_budget_spent: number | null;
  remaining_budget: number;
  over_budget: boolean;
  area_ha: number | null;
  planned_cost_per_ha: number | null;
  actual_cost_per_ha: number | null;
  planned_applications: number;
  actual_applications: number;
  expected_revenue: number | null;
  expected_profit: number | null;
  interpretation: string;
}

export interface AgendaItem {
  planned_event_id: number | null;
  event_type: string;
  planned_date: string;
  product_name: string | null;
  expected_cost: number | null;
  status: string;
}

export interface Agenda {
  crop_cycle_id: number;
  items: AgendaItem[];
  summary: Record<string, number>;
}

export interface QuickLogRequest {
  crop_cycle_ids: number[];
  event_date: string;
  preset_id?: number;
  event_type?: EventType;
  product_name?: string;
  quantity?: number;
  unit?: string;
  cost?: number;
  notes?: string;
}

export interface EventPreset {
  id: number;
  name: string;
  event_type: EventType;
  product_name: string | null;
  product_id: number | null;
  default_quantity: number | null;
  unit: string | null;
  default_cost: number | null;
  cost_is_per_hectare: boolean;
  notes: string | null;
}

export interface CreateEventPresetRequest {
  name: string;
  event_type: EventType;
  product_name?: string;
  default_quantity?: number;
  unit?: string;
  default_cost?: number;
  cost_is_per_hectare?: boolean;
  notes?: string;
}

// Decision support
// ---------------------------------------------------------------------------

export interface AttentionFlag {
  code: string;
  severity: string;
  title: string;
  detail: string;
  confidence: string;
  evidence: Record<string, unknown>;
}

export interface FieldAttention {
  field_id: number;
  field_name: string;
  attention_level: string;
  flags: AttentionFlag[];
}

export interface RankingItem {
  field_id: number;
  field_name: string;
  value: number;
}

export interface Decisions {
  farm_id: number;
  season: string | null;
  n_fields: number;
  fields: FieldAttention[];
  rankings: Record<string, RankingItem[]>;
  note: string;
}

// Decision Cards — contrato único de recomendação (clima/manejo/histórico)
// ---------------------------------------------------------------------------

export interface DecisionEffect {
  basis: string;
  yield_sc_ha: [number, number, number] | null;
  profit_brl_ha: [number, number, number] | null;
}

export interface DecisionCard {
  id: string;
  source: string; // "clima" | "manejo" | "historico"
  decision: string;
  recommendation: string;
  confidence: string; // "alta" | "moderada" | "baixa"
  horizon: string;
  disclaimer: string;
  n_data: number;
  severity: string;
  effect: DecisionEffect | null;
  why: { label: string; detail: string }[];
}

export interface DecisionCards {
  farm_id: number;
  field_id: number | null;
  n_cards: number;
  cards: DecisionCard[];
  note: string;
}

// Platform: system status, dashboard, demo
// ---------------------------------------------------------------------------

export interface SystemStatus {
  status: string;
  version: string;
  database: { status: string; url_scheme: string };
  model: { status: string; path: string };
  calibration_report: { present: boolean };
  counts: Record<string, number>;
  data_sources?: DataSourceHealth[];
}

export interface DataSourceHealth {
  label: string;
  source: string | null;
  fetched_at: string | null;
  age_days: number | null;
  status: "atual" | "desatualizado" | "ausente" | "ok";
}

export interface FarmDashboard {
  farm_id: number;
  season: string | null;
  n_fields: number;
  attention: {
    levels: Record<string, number>;
    top: { field_name: string; attention_level: string; flags: AttentionFlag[] } | null;
  };
  budget: {
    planned_total: number;
    actual_total: number;
    remaining: number;
    pct_consumed: number | null;
  };
  agenda: {
    overdue: number;
    upcoming: number;
    next_operation: { event_type: string; planned_date: string } | null;
  };
  insights: Insight[];
}

export interface DemoSeedResult {
  farm_id: number;
  farm_name: string;
  n_fields: number;
  n_cycles: number;
  season: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Endpoint functions
// ---------------------------------------------------------------------------

export const api = {
  getMunicipalities: () => get<Municipality[]>("/municipalities"),

  getMarketPrice: (crop = "soja") =>
    get<MarketPrice>(`/market/price?crop=${encodeURIComponent(crop)}`),

  getCostBenchmark: (cycleId: number) =>
    get<CostBenchmarkComparison>(`/crop-cycles/${cycleId}/cost-benchmark`),

  getFarmWeather: (farmId: number) =>
    get<WeatherForecast>(`/farms/${farmId}/weather`),

  getFieldLearnedEstimate: (fieldId: number, season = "2026/27") =>
    get<FieldLearnedEstimate>(
      `/fields/${fieldId}/learned-estimate?season=${encodeURIComponent(season)}`
    ),

  getManejoHistory: (fieldId: number) =>
    get<ManejoHistory>(`/fields/${fieldId}/manejo-history`),

  getFieldSoilSuggestion: (fieldId: number) =>
    get<SoilSuggestion>(`/fields/${fieldId}/soil-suggestion`),

  saveCycleManejo: (cycleId: number, profile: Record<string, string>) =>
    put<{ profile: Record<string, string> }, { profile: Record<string, string> }>(
      `/crop-cycles/${cycleId}/manejo`,
      { profile }
    ),

  getAgronomicFactors: () => get<AgronomicFactor[]>("/agronomic/factors"),

  getAgronomicKnowledge: () => get<KnowledgeEntry[]>("/agronomic/knowledge"),

  classifySoilAnalysis: (body: SoilAnalysisRequest) =>
    post<SoilAnalysisRequest, SoilAnalysisResult>("/agronomic/soil-analysis", body),

  classifyPlantingWindow: (params: {
    plantingDate: string;
    municipality?: string;
    fieldId?: number;
  }) => {
    const q = new URLSearchParams({ planting_date: params.plantingDate, crop: "soja", uf: "RS" });
    if (params.fieldId != null) q.set("field_id", String(params.fieldId));
    else if (params.municipality) q.set("municipality", params.municipality);
    return get<{
      profile_fragment: Record<string, string>;
      within_zarc: boolean;
      risk_level: number | null;
      basis: string;
    }>(`/agronomic/planting-window-class?${q.toString()}`);
  },

  postAgronomicEstimate: (body: AgronomicEstimateRequest) =>
    post<AgronomicEstimateRequest, AgronomicEstimate>("/agronomic/estimate", body),

  getFieldProfile: (fieldId: number) =>
    get<{
      field_id: number;
      profile: Record<string, string>;
      completeness?: ProfileCompleteness;
    }>(`/fields/${fieldId}/agronomic-profile`),

  saveFieldProfile: (fieldId: number, profile: Record<string, string>) =>
    put<{ profile: Record<string, string> }, { field_id: number; profile: Record<string, string> }>(
      `/fields/${fieldId}/agronomic-profile`,
      { profile }
    ),

  getFieldEstimate: (fieldId: number, season = "2026/27") =>
    get<AgronomicEstimate>(`/fields/${fieldId}/estimate?season=${encodeURIComponent(season)}`),

  getSeasonBrief: (municipality: string, season = "2026/27", pricePerBag?: number) => {
    const q = new URLSearchParams({ municipality, crop: "soja", uf: "RS", season });
    if (pricePerBag) q.set("price_per_bag", String(pricePerBag));
    return get<SeasonBrief>(`/planning/season-brief?${q.toString()}`);
  },

  getSeasonBriefForField: (fieldId: number, season = "2026/27", pricePerBag?: number) => {
    const q = new URLSearchParams({
      field_id: String(fieldId), crop: "soja", uf: "RS", season,
    });
    if (pricePerBag) q.set("price_per_bag", String(pricePerBag));
    return get<SeasonBrief>(`/planning/season-brief?${q.toString()}`);
  },

  getZarcWindow: (municipality: string, plantingDate?: string) => {
    const q = new URLSearchParams({ municipality, crop: "soja", uf: "RS" });
    if (plantingDate) q.set("planting_date", plantingDate);
    return get<ZarcPlantingWindow>(`/zarc/planting-window?${q.toString()}`);
  },

  getSystemStatus: () => get<SystemStatus>("/system/status"),

  getDashboard: (farmId: number) => get<FarmDashboard>(`/farms/${farmId}/dashboard`),

  seedDemo: () => post<Record<string, never>, DemoSeedResult>("/demo/seed", {}),

  operationsCsvUrl: (farmId: number) => `${API_V1}/farms/${farmId}/operations.csv`,

  getDecisions: (farmId: number) => get<Decisions>(`/farms/${farmId}/decisions`),

  getDecisionCards: (farmId: number, fieldId?: number, season = "2026/27") => {
    const q = new URLSearchParams({ season });
    if (fieldId != null) q.set("field_id", String(fieldId));
    return get<DecisionCards>(`/farms/${farmId}/decision-cards?${q.toString()}`);
  },

  getPlanVsActual: (cycleId: number) =>
    get<PlanVsActual>(`/crop-cycles/${cycleId}/plan-vs-actual`),

  getAgenda: (cycleId: number) => get<Agenda>(`/crop-cycles/${cycleId}/agenda`),

  getPlannedEvents: (cycleId: number) =>
    get<PlannedEvent[]>(`/crop-cycles/${cycleId}/planned-events`),

  createPlannedEvent: (cycleId: number, body: CreatePlannedEventRequest) =>
    post<CreatePlannedEventRequest, PlannedEvent>(
      `/crop-cycles/${cycleId}/planned-events`,
      body
    ),

  quickLog: (body: QuickLogRequest) =>
    post<QuickLogRequest, { created: AgriculturalEvent[] }>("/quick-log", body),

  getEventPresets: () => get<EventPreset[]>("/event-presets"),

  createEventPreset: (body: CreateEventPresetRequest) =>
    post<CreateEventPresetRequest, EventPreset>("/event-presets", body),

  getFieldAnalytics: (farmId: number) =>
    get<FieldAnalytics>(`/farms/${farmId}/field-analytics`),

  getInsights: (farmId: number) => get<Insights>(`/farms/${farmId}/insights`),

  regionalIntelligence: (body: RegionalIntelligenceRequest) =>
    post<RegionalIntelligenceRequest, RegionalIntelligenceResponse>(
      "/regional-intelligence",
      body
    ),

  plantingDateSimulation: (body: PlantingDateSimulationRequest) =>
    post<PlantingDateSimulationRequest, PlantingDateSimulationResponse>(
      "/planting-date-simulation",
      body
    ),

  plantingWindowOptimization: (body: PlantingWindowOptimizationRequest) =>
    post<PlantingWindowOptimizationRequest, PlantingWindowOptimizationResponse>(
      "/planting-window-optimization",
      body
    ),

  assistant: (body: AssistantRequest) =>
    post<AssistantRequest, AssistantResponse>("/assistant", body),

  createFarm: (body: CreateFarmRequest) =>
    post<CreateFarmRequest, Farm>("/farms", body),

  getFarms: () => get<Farm[]>("/farms"),

  getFarmCropCycles: (farmId: number) =>
    get<CropCycleListItem[]>(`/farms/${farmId}/crop-cycles`),

  createField: (farmId: number, body: CreateFieldRequest) =>
    post<CreateFieldRequest, Field>(`/farms/${farmId}/fields`, body),

  getFields: (farmId: number) => get<Field[]>(`/farms/${farmId}/fields`),

  createCropCycle: (fieldId: number, body: CreateCropCycleRequest) =>
    post<CreateCropCycleRequest, CropCycle>(
      `/fields/${fieldId}/crop-cycles`,
      body
    ),

  createYieldObservation: (body: CreateYieldObservationRequest) =>
    post<CreateYieldObservationRequest, YieldObservation>(
      "/yield-observations",
      body
    ),

  getYieldObservations: () => get<YieldObservation[]>("/yield-observations"),

  // ---- Digital Twin: crop-cycle / events ----
  getCropCycle: (id: number) =>
    get<CropCycleDetail>(`/crop-cycles/${id}`),

  updateCropCycle: (id: number, body: UpdateCropCycleRequest) =>
    patch<UpdateCropCycleRequest, CropCycleDetail>(`/crop-cycles/${id}`, body),

  getCropCycleEvents: (id: number) =>
    get<AgriculturalEvent[]>(`/crop-cycles/${id}/events`),

  createCropCycleEvent: (id: number, body: CreateAgriculturalEventRequest) =>
    post<CreateAgriculturalEventRequest, AgriculturalEvent>(
      `/crop-cycles/${id}/events`,
      body
    ),

  getCropCycleCost: (id: number) =>
    get<CostBreakdown>(`/crop-cycles/${id}/cost`),

  getCropCycleFinancials: (id: number, body: FinancialsRequest) =>
    post<FinancialsRequest, Financials>(`/crop-cycles/${id}/financials`, body),

  // ---- Adaptive Intelligence ----
  getFarmProfile: (farmId: number) =>
    get<FarmProfile>(`/farms/${farmId}/performance-profile`),

  recomputeFarmProfile: (farmId: number) =>
    post<Record<string, never>, FarmProfile>(
      `/farms/${farmId}/performance-profile/recompute`,
      {}
    ),

  personalizedIntelligence: (body: PersonalizedIntelligenceRequest) =>
    post<PersonalizedIntelligenceRequest, PersonalizedIntelligence>(
      "/personalized-intelligence",
      body
    ),

  // ---- Calibration ----
  getCalibration: () => get<Calibration>("/calibration"),

  // ---- Products ----
  getProducts: () => get<Product[]>("/products"),

  createProduct: (body: CreateProductRequest) =>
    post<CreateProductRequest, Product>("/products", body),
};

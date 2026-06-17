// Typed API client for the FADA backend.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
}

export interface AssistantResponse {
  intent: string;
  parameters: Record<string, unknown>;
  answer: string;
  result: Record<string, unknown> | null;
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
  break_even_yield_sc_ha: number;
  yield_source: string;
  scenarios: FinancialScenario[];
}

export interface FinancialsRequest {
  price_per_bag: number;
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

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_V1}${path}`, {
    headers: { Accept: "application/json" },
  });
  return handle<T>(res);
}

async function post<TBody, TResp>(path: string, body: TBody): Promise<TResp> {
  const res = await fetch(`${API_V1}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });
  return handle<TResp>(res);
}

async function patch<TBody, TResp>(path: string, body: TBody): Promise<TResp> {
  const res = await fetch(`${API_V1}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });
  return handle<TResp>(res);
}

// ---------------------------------------------------------------------------
// Endpoint functions
// ---------------------------------------------------------------------------

export const api = {
  getMunicipalities: () => get<Municipality[]>("/municipalities"),

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

  // ---- Products ----
  getProducts: () => get<Product[]>("/products"),

  createProduct: (body: CreateProductRequest) =>
    post<CreateProductRequest, Product>("/products", body),
};

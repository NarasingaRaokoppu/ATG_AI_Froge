export type OrchestratorRequest = {
  user_id: string;
  session_id: string;
  page_type: "home" | "plp";
  context: Record<string, string>;
};

export type Recommendation = {
  product_id: string;
  score: number;
  reason: string;
};

export type PricingSuggestion = {
  product_id: string;
  promo_type: string;
  discount_pct: number;
  reason: string;
};

export type OrchestratorResponse = {
  trace_id: string;
  user_id: string;
  segment: {
    segment_id: string;
    segment_name: string;
    confidence: number;
    reasons: string[];
  };
  recommendations: Recommendation[];
  pricing: PricingSuggestion[];
  content: {
    variant_id: string;
    slot_map: Record<string, string>;
    reason: string;
  };
  meta: {
    latency_ms: number;
    fallback_used: boolean;
  };
};

export type UserProfile = {
  user_id: string;
  active_segment: string;
  recent_events: number;
  last_trace_id: string | null;
};

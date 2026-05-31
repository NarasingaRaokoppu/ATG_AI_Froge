import { useMemo, useState } from "react";

import { MetricChip } from "./components/MetricChip";
import { decide, getProfile, ingestEvent } from "./services/api";
import type { OrchestratorResponse, UserProfile } from "./types/personalization";

const PRODUCT_LABELS: Record<string, string> = {
  p_1001: "Smart Running Shoes",
  p_1002: "Premium Leather Bag",
  p_1003: "Noise Canceling Headphones",
  p_1004: "Daily Essentials Bundle",
  p_1005: "Designer Sunglasses",
  p_1006: "Wireless Charger",
};

const SEGMENT_HELP: Record<string, string> = {
  new_visitor: "The user is new or has low interaction history.",
  value_seeker: "The user interacts with discount-oriented content.",
  loyal_buyer: "The user has high repeat purchase intent.",
  considering: "The user is evaluating products before purchase.",
};

function randomSessionId(): string {
  return `s_${Math.random().toString(36).slice(2, 10)}`;
}

export default function App() {
  const [userId, setUserId] = useState("u_demo_001");
  const [sessionId, setSessionId] = useState(randomSessionId());
  const [pageType, setPageType] = useState<"home" | "plp">("home");
  const [eventLabel, setEventLabel] = useState("discount_banner");
  const [decision, setDecision] = useState<OrchestratorResponse | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const segmentTone = useMemo(() => {
    if (!decision) {
      return "none";
    }
    if (decision.segment.segment_name === "value_seeker") {
      return "value";
    }
    if (decision.segment.segment_name === "loyal_buyer") {
      return "premium";
    }
    if (decision.segment.segment_name === "considering") {
      return "considering";
    }
    return "new";
  }, [decision]);

  async function runDecisionFlow() {
    try {
      setLoading(true);
      setError(null);
      await ingestEvent(userId, sessionId, eventLabel);
      const nextDecision = await decide({
        user_id: userId,
        session_id: sessionId,
        page_type: pageType,
        context: { device: "web", locale: "en-US" },
      });
      const nextProfile = await getProfile(userId);
      setDecision(nextDecision);
      setProfile(nextProfile);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown request error");
    } finally {
      setLoading(false);
    }
  }

  async function runScenario(type: "new_visitor" | "value_seeker" | "loyal_buyer") {
    try {
      setLoading(true);
      setError(null);

      const scenarioUser = `u_${type}_${Date.now()}`;
      const scenarioSession = randomSessionId();
      setUserId(scenarioUser);
      setSessionId(scenarioSession);

      if (type === "value_seeker") {
        await ingestEvent(scenarioUser, scenarioSession, "discount_banner", "click");
        await ingestEvent(scenarioUser, scenarioSession, "flash_discount", "click");
      }

      if (type === "loyal_buyer") {
        await ingestEvent(scenarioUser, scenarioSession, "order_1001", "purchase");
        await ingestEvent(scenarioUser, scenarioSession, "order_1003", "purchase");
        await ingestEvent(scenarioUser, scenarioSession, "order_1005", "purchase");
      }

      const nextDecision = await decide({
        user_id: scenarioUser,
        session_id: scenarioSession,
        page_type: pageType,
        context: { device: "web", locale: "en-US" },
      });
      const nextProfile = await getProfile(scenarioUser);
      setDecision(nextDecision);
      setProfile(nextProfile);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown request error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`app shell-${segmentTone}`}>
      <header className="hero">
        <p className="eyebrow">Project 14</p>
        <h1>Hyper-Personalization Command Deck</h1>
        <p>
          Real-time behavior tracking, segment decisions, recommendations, pricing suggestions, and dynamic
          content variants in one orchestration flow.
        </p>
      </header>

      <section className="panel controls">
        <h2>Simulation Input</h2>
        <p className="helper">Quick demo: use presets to generate clear real-time segments and outputs.</p>
        <div className="scenario-row">
          <button type="button" className="alt-btn" disabled={loading} onClick={() => runScenario("new_visitor")}>
            Run New Visitor Scenario
          </button>
          <button type="button" className="alt-btn" disabled={loading} onClick={() => runScenario("value_seeker")}>
            Run Value Seeker Scenario
          </button>
          <button type="button" className="alt-btn" disabled={loading} onClick={() => runScenario("loyal_buyer")}>
            Run Loyal Buyer Scenario
          </button>
        </div>
        <div className="grid-two">
          <label>
            User ID
            <input value={userId} onChange={(event) => setUserId(event.target.value)} />
          </label>
          <label>
            Session ID
            <input value={sessionId} onChange={(event) => setSessionId(event.target.value)} />
          </label>
          <label>
            Page Type
            <select value={pageType} onChange={(event) => setPageType(event.target.value as "home" | "plp")}>
              <option value="home">home</option>
              <option value="plp">plp</option>
            </select>
          </label>
          <label>
            Event Label
            <input value={eventLabel} onChange={(event) => setEventLabel(event.target.value)} />
          </label>
        </div>

        <button onClick={runDecisionFlow} disabled={loading}>
          {loading ? "Running orchestration..." : "Ingest Event + Decide"}
        </button>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="panel metrics">
        <h2>Live Metrics</h2>
        <div className="metric-row">
          <MetricChip label="Trace" value={decision?.trace_id ?? "-"} />
          <MetricChip label="Segment" value={decision?.segment.segment_name ?? "-"} />
          <MetricChip label="Latency" value={decision ? `${decision.meta.latency_ms} ms` : "-"} />
          <MetricChip label="Recent Events" value={String(profile?.recent_events ?? 0)} />
        </div>
        {decision ? (
          <p className="helper">
            <strong>Interpretation:</strong> {SEGMENT_HELP[decision.segment.segment_name] ?? "No segment explanation available."}
          </p>
        ) : null}
      </section>

      <section className="panel output-grid">
        <article>
          <h3>Recommendations</h3>
          <ul>
            {(decision?.recommendations ?? []).map((item) => (
              <li key={item.product_id}>
                <span>{PRODUCT_LABELS[item.product_id] ?? item.product_id}</span>
                <strong>{item.score.toFixed(2)}</strong>
                <small>{item.reason}</small>
              </li>
            ))}
          </ul>
        </article>

        <article>
          <h3>Pricing Suggestions</h3>
          <ul>
            {(decision?.pricing ?? []).map((item) => (
              <li key={item.product_id}>
                <span>{PRODUCT_LABELS[item.product_id] ?? item.product_id}</span>
                <strong>{item.discount_pct}%</strong>
                <small>{item.reason}</small>
              </li>
            ))}
          </ul>
        </article>

        <article>
          <h3>Content Variant</h3>
          <div className="content-card">
            <p>
              <strong>Variant:</strong> {decision?.content.variant_id ?? "-"}
            </p>
            <p>
              <strong>Hero Slot:</strong> {decision?.content.slot_map.hero ?? "-"}
            </p>
            <p>
              <strong>Rail Slot:</strong> {decision?.content.slot_map.rail_1 ?? "-"}
            </p>
            <p>
              <strong>Reason:</strong> {decision?.content.reason ?? "-"}
            </p>
          </div>
        </article>
      </section>
    </div>
  );
}

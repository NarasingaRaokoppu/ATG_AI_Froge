import type { OrchestratorRequest, OrchestratorResponse, UserProfile } from "../types/personalization";

const API_BASE = "http://localhost:8001/api/v1";

export async function ingestEvent(
  userId: string,
  sessionId: string,
  label: string,
  eventType: "click" | "search" | "add_to_cart" | "purchase" = "click"
): Promise<void> {
  const response = await fetch(`${API_BASE}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      event_type: eventType,
      event_time: new Date().toISOString(),
      attributes: { label },
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to ingest event");
  }
}

export async function decide(payload: OrchestratorRequest): Promise<OrchestratorResponse> {
  const response = await fetch(`${API_BASE}/personalization/decide`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to generate decision");
  }

  return (await response.json()) as OrchestratorResponse;
}

export async function getProfile(userId: string): Promise<UserProfile> {
  const response = await fetch(`${API_BASE}/users/${userId}/profile`);
  if (!response.ok) {
    throw new Error("Failed to fetch profile");
  }
  return (await response.json()) as UserProfile;
}

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_behavior_service, get_orchestrator_service, get_profile_service
from app.schemas.personalization import (
    EventIngestRequest,
    EventIngestResponse,
    OrchestratorRequest,
    OrchestratorResponse,
    TraceResponse,
    UserProfileResponse,
)
from app.services.behavior import BehaviorTrackingService
from app.services.orchestrator import OrchestratorService
from app.services.profile import ProfileService

router = APIRouter(prefix="/api/v1", tags=["personalization"])


@router.post("/events", response_model=EventIngestResponse, status_code=201)
def ingest_event(
    payload: EventIngestRequest,
    service: BehaviorTrackingService = Depends(get_behavior_service),
) -> EventIngestResponse:
    event = service.ingest(payload)
    return EventIngestResponse(event_id=event.id)


@router.post("/personalization/decide", response_model=OrchestratorResponse)
def decide(
    payload: OrchestratorRequest,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> OrchestratorResponse:
    return service.decide(payload)


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def get_profile(
    user_id: str,
    service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    return service.get_user_profile(user_id)


@router.get("/traces/{trace_id}", response_model=TraceResponse)
def get_trace(
    trace_id: str,
    service: ProfileService = Depends(get_profile_service),
) -> TraceResponse:
    response = service.get_trace(trace_id)
    if response.status == "not_found":
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Trace not found"})
    return response

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.repositories.base import PersonalizationRepository
from app.repositories.in_memory import InMemoryPersonalizationRepository
from app.services.behavior import BehaviorTrackingService
from app.services.content import ContentPersonalizationService
from app.services.orchestrator import OrchestratorService
from app.services.pricing import PricingService
from app.services.profile import ProfileService
from app.services.recommendation import RecommendationService
from app.services.segmentation import SegmentationService


@lru_cache(maxsize=1)
def get_repository() -> PersonalizationRepository:
    if settings.use_in_memory_repo:
        return InMemoryPersonalizationRepository()

    if settings.supabase_url and settings.supabase_key:
        from app.repositories.supabase_repo import SupabasePersonalizationRepository

        return SupabasePersonalizationRepository(settings.supabase_url, settings.supabase_key)

    if settings.database_url:
        from app.repositories.postgres_repo import PostgresPersonalizationRepository

        return PostgresPersonalizationRepository(settings.database_url)

    return InMemoryPersonalizationRepository()


def get_behavior_service() -> BehaviorTrackingService:
    return BehaviorTrackingService(get_repository())


def get_orchestrator_service() -> OrchestratorService:
    repo = get_repository()
    return OrchestratorService(
        repo=repo,
        segmentation_service=SegmentationService(repo),
        recommendation_service=RecommendationService(repo),
        pricing_service=PricingService(repo),
        content_service=ContentPersonalizationService(),
    )


def get_profile_service() -> ProfileService:
    return ProfileService(get_repository())

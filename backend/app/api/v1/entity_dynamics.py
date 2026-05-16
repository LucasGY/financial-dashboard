from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_entity_dynamics_service
from app.schemas.entity_dynamics import FeedResponse, SourceDetail
from app.services.entity_dynamics_service import EntityDynamicsService

router = APIRouter()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    channel: str = Query(default="ai"),
    filter: str = Query(default="all"),
    search: Optional[str] = Query(default=None),
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    entity: Optional[str] = Query(default=None),
    service: EntityDynamicsService = Depends(get_entity_dynamics_service),
) -> FeedResponse:
    return service.get_feed(channel=channel, filter_key=filter, search=search, min_score=min_score, entity=entity)


@router.get("/sources/{slug}", response_model=SourceDetail)
def get_source_detail(
    slug: str,
    service: EntityDynamicsService = Depends(get_entity_dynamics_service),
) -> SourceDetail:
    detail = service.get_detail(slug)
    if detail is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return detail

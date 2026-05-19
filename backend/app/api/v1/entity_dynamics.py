from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx

from app.api.dependencies import get_entity_dynamics_service
from app.schemas.entity_dynamics import FavoriteRequest, FavoriteResponse, FeedResponse, SourceDetail
from app.services.entity_dynamics_service import EntityDynamicsService

router = APIRouter()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    channel: str = Query(default="ai"),
    filter: str = Query(default="all"),
    search: Optional[str] = Query(default=None),
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    entity: Optional[str] = Query(default=None),
    limit: int = Query(default=35, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    service: EntityDynamicsService = Depends(get_entity_dynamics_service),
) -> FeedResponse:
    return service.get_feed(channel=channel, filter_key=filter, search=search, min_score=min_score, entity=entity, limit=limit, cursor=cursor)


@router.get("/sources/{slug}", response_model=SourceDetail)
def get_source_detail(
    slug: str,
    service: EntityDynamicsService = Depends(get_entity_dynamics_service),
) -> SourceDetail:
    detail = service.get_detail(slug)
    if detail is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return detail


@router.post("/sources/{slug}/favorite", response_model=FavoriteResponse)
def set_source_favorite(
    slug: str,
    request: FavoriteRequest,
    service: EntityDynamicsService = Depends(get_entity_dynamics_service),
) -> FavoriteResponse:
    result = service.set_favorite(slug, request.is_favorited)
    if result is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return result


@router.get("/media/video")
def proxy_video(url: str = Query(...), range_header: Optional[str] = Header(default=None, alias="range")):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"video.twimg.com", "video.x.com"}:
        raise HTTPException(status_code=400, detail="Unsupported video host")
    headers = {}
    if range_header:
        headers["Range"] = range_header
    try:
        client = httpx.Client(timeout=30.0, follow_redirects=True)
        response = client.stream("GET", url, headers=headers)
        remote = response.__enter__()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Video upstream unavailable") from exc
    if remote.status_code >= 400:
        response.__exit__(None, None, None)
        raise HTTPException(status_code=remote.status_code, detail="Video upstream failed")

    passthrough_headers = {
        key: value
        for key, value in remote.headers.items()
        if key.lower() in {"content-length", "content-range", "accept-ranges"}
    }
    passthrough_headers["Cache-Control"] = "public, max-age=86400"

    def body():
        try:
            yield from remote.iter_bytes()
        finally:
            response.__exit__(None, None, None)
            client.close()

    return StreamingResponse(
        body(),
        status_code=remote.status_code,
        media_type=remote.headers.get("content-type", "video/mp4"),
        headers=passthrough_headers,
    )

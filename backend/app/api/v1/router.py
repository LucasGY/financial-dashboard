from fastapi import APIRouter

from app.api.v1.sentiment import router as sentiment_router
from app.api.v1.strategy_lab import router as strategy_lab_router
from app.api.v1.valuation import router as valuation_router

router = APIRouter()
router.include_router(sentiment_router, prefix="/sentiment", tags=["sentiment"])
router.include_router(valuation_router, prefix="/valuation", tags=["valuation"])
router.include_router(strategy_lab_router, prefix="/strategy-lab", tags=["strategy-lab"])

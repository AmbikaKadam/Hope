"""REST endpoint for the dashboard: GET /api/dashboard/statistics."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/statistics", response_model=schemas.DashboardStatistics)
def dashboard_statistics(
    recent_days: int = Query(30, ge=1, le=365, description="'Recently added' means registered within this many days"),
    db: Session = Depends(get_db),
):
    return crud.get_dashboard_statistics(db, recent_days=recent_days)

"""REST endpoints for /api/beneficiaries."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..models import Beneficiary

router = APIRouter(prefix="/api/beneficiaries", tags=["Beneficiaries"])


def _get_or_404(db: Session, beneficiary_id: int) -> Beneficiary:
    beneficiary = crud.get_beneficiary(db, beneficiary_id)
    if beneficiary is None:
        raise HTTPException(status_code=404, detail=f"Beneficiary {beneficiary_id} was not found")
    return beneficiary


@router.get("", response_model=list[schemas.BeneficiaryOut])
def list_beneficiaries(
    search: str | None = Query(None, description="Matches name, phone, city or programme"),
    status: schemas.Status | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return crud.get_beneficiaries(db, search=search, status=status, skip=skip, limit=limit)


@router.post("", response_model=schemas.BeneficiaryOut, status_code=201)
def create_beneficiary(payload: schemas.BeneficiaryCreate, db: Session = Depends(get_db)):
    return crud.create_beneficiary(db, payload)


@router.get("/{beneficiary_id}", response_model=schemas.BeneficiaryOut)
def get_beneficiary(beneficiary_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, beneficiary_id)


@router.put("/{beneficiary_id}", response_model=schemas.BeneficiaryOut)
def update_beneficiary(beneficiary_id: int, payload: schemas.BeneficiaryUpdate, db: Session = Depends(get_db)):
    return crud.update_beneficiary(db, _get_or_404(db, beneficiary_id), payload)


@router.delete("/{beneficiary_id}", response_model=schemas.BeneficiaryOut)
def deactivate_beneficiary(beneficiary_id: int, db: Session = Depends(get_db)):
    """Soft delete: sets status to 'Inactive' and returns the updated record."""
    return crud.deactivate_beneficiary(db, _get_or_404(db, beneficiary_id))

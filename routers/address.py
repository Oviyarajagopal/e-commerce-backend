from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models.user import Address
from schemas.address import AddressCreate, AddressUpdate, AddressResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/addresses", tags=["Addresses"])


# 🔌 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ CREATE ADDRESS
@router.post("/", response_model=AddressResponse)
def create_address(
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    new_address = Address(
        user_id=current_user.id,
        **address.dict()
    )

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address


# ✅ GET ALL ADDRESSES OF USER
@router.get("/", response_model=list[AddressResponse])
def get_addresses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(Address).filter(Address.user_id == current_user.id).all()


# ✅ UPDATE ADDRESS
@router.put("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address: AddressUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")

    for key, value in address.dict(exclude_unset=True).items():
        setattr(db_address, key, value)

    db.commit()
    db.refresh(db_address)

    return db_address


# ✅ DELETE ADDRESS
@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(db_address)
    db.commit()

    return {"message": "Address deleted successfully"}
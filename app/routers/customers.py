from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List
from pydantic import BaseModel, Field
from app.database import SessionLocal
from app import schemas,models

router = APIRouter(prefix="/api/customers", tags=["Customer Khata & Debt Ledger"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# =================================================================
# ENDPOINTS
# =================================================================

# 1. Create a New Customer Profile
@router.post("/", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer_data: schemas.CustomerCreate, db: Session = Depends(get_db)):
    # Check if a customer with the same phone number already exists
    if customer_data.phone:
        existing = db.query(models.Customer).filter(models.Customer.phone == customer_data.phone).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"A customer profile with phone number {customer_data.phone} already exists."
            )
            
    new_customer = models.Customer(
        name=customer_data.name,
        phone=customer_data.phone,
        total_credit_due=Decimal("0.00")
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


# 2. Search / List All Customer Ledgers
@router.get("/", response_model=List[schemas.CustomerResponse])
def list_customers(search: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Customer)
    if search:
        # Search seamlessly across names or partial phone number matches
        query = query.filter(
            (models.Customer.name.ilike(f"%{search}%")) | 
            (models.Customer.phone.like(f"%{search}%"))
        )
    return query.all()


# 3. Approach A: Direct Khata Debt Repayment Settlement
@router.post("/{customer_id}/repay", status_code=status.HTTP_200_OK)
def process_debt_repayment(customer_id: int, payment: schemas.RepaymentRequest, db: Session = Depends(get_db)):
    try:
        # Fetch the customer profile
        customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer account profile not found.")
        
        if customer.total_credit_due <= 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Customer {customer.name} does not have any active outstanding debt to clear."
            )
            
        if payment.amount_paid > customer.total_credit_due:
            raise HTTPException(
                status_code=400, 
                detail=f"Overpayment Alert: Processing ₹{payment.amount_paid} exceeds total debt of ₹{customer.total_credit_due}."
            )

        # Atomic accounting shifts
        # Deduct outstanding market credit tally
        customer.total_credit_due -= payment.amount_paid
        
        # Inject matching cash flow history event directly into Finance Ledger
        note_log = f"Khata Repayment via {payment.payment_method}."
        if payment.notes:
            note_log += f" Details: {payment.notes}"

        db.add(models.FinanceLedger(
            type="INCOME",
            amount=payment.amount_paid,
            category="DEBT_REPAYMENT",
            is_automated=True,
            notes=f"Customer: {customer.name} (ID: {customer.id}) - {note_log}"
        ))
        
        db.commit()
        return {
            "message": "Repayment processed successfully",
            "customer_name": customer.name,
            "amount_settled": payment.amount_paid,
            "remaining_credit_due": customer.total_credit_due
        }
        
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Database Transaction Failure: {str(e)}")
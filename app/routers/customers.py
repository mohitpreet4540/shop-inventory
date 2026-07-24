from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List
from app.database import get_db  # 🌟 now importing the shared dependency instead of redefining it
from app.dependencies import require_roles, get_current_user
from app import schemas, models

router = APIRouter(prefix="/api/customers", tags=["Customer Khata & Debt Ledger"])


# =================================================================
# ENDPOINTS
# =================================================================

# 1. Create a New Customer Profile (Any logged-in role — cashiers register walk-in customers)
@router.post("/", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer_data: schemas.CustomerCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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
        total_credit_due=Decimal("0.00"),
        # 🌟 NEW: Udhaar ceiling fields, default to no limit / WARN if not provided
        credit_limit=customer_data.credit_limit,
        credit_block_mode=customer_data.credit_block_mode or "WARN",
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


# 2. Search / List All Customer Ledgers (Any logged-in role)
@router.get("/", response_model=List[schemas.CustomerResponse])
def list_customers(search: str | None = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Customer)
    if search:
        query = query.filter(
            (models.Customer.name.ilike(f"%{search}%")) |
            (models.Customer.phone.like(f"%{search}%"))
        )
    return query.all()


# 3. 🌟 NEW: Update a customer's credit limit / block mode (e.g. raise/lower their Udhaar ceiling)
#    Restricted to OWNER/ADMIN — cashiers shouldn't be able to raise their own credit ceiling.
@router.patch("/{customer_id}/credit-settings", response_model=schemas.CustomerResponse)
def update_customer_credit_settings(
    customer_id: int,
    payload: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN")),
):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer account profile not found.")

    update_data = payload.model_dump(exclude_unset=True)

    if "credit_block_mode" in update_data and update_data["credit_block_mode"] not in ("WARN", "BLOCK"):
        raise HTTPException(status_code=400, detail="credit_block_mode must be either 'WARN' or 'BLOCK'.")

    for key, value in update_data.items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)
    return customer


# 4. Approach A: Direct Khata Debt Repayment Settlement (Any logged-in role)
@router.post("/{customer_id}/repay", status_code=status.HTTP_200_OK)
def process_debt_repayment(customer_id: int, payment: schemas.RepaymentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
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

        customer.total_credit_due -= payment.amount_paid

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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db  # 🌟 now importing the shared dependency instead of redefining it
from app.dependencies import require_roles
from app import schemas, models

router = APIRouter(prefix="/api/finance", tags=["Finance & Manual Expenses"])

# 1. RECORD A MANUAL EXPENSE (OWNER, ADMIN)
@router.post("/expenses", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def record_expense(payload: schemas.ExpenseCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles("OWNER", "ADMIN"))):
    try:
        new_expense = models.FinanceLedger(
            type="EXPENSE",
            amount=payload.amount,
            category=payload.category.upper(),
            is_automated=False, # Manual entry
            notes=payload.notes
        )
        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)
        return new_expense
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log manual expense: {str(e)}"
        )

# 2. FETCH ALL EXPENSES (OWNER, ADMIN)
@router.get("/expenses", response_model=List[schemas.ExpenseResponse])
def list_all_expenses(db: Session = Depends(get_db), current_user: models.User = Depends(require_roles("OWNER", "ADMIN"))):
    try:
        return db.query(models.FinanceLedger).filter(
            models.FinanceLedger.type == "EXPENSE"
        ).order_by(models.FinanceLedger.timestamp.desc()).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expense list: {str(e)}"
        )

# 3. DELETE A MANUAL EXPENSE (OWNER, ADMIN)
@router.delete("/expenses/{expense_id}", status_code=status.HTTP_200_OK)
def delete_manual_expense(expense_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles("OWNER", "ADMIN"))):
    try:
        expense = db.query(models.FinanceLedger).filter(
            models.FinanceLedger.id == expense_id,
            models.FinanceLedger.type == "EXPENSE"
        ).first()

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No expense entry found with ID {expense_id}."
            )

        if expense.is_automated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Automated procurement expenses cannot be deleted here. Revert the restock transaction instead."
            )

        db.delete(expense)
        db.commit()
        return {
            "status": "Success",
            "message": f"Successfully deleted manual expense entry {expense_id}."
        }
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete expense: {str(e)}"
        )
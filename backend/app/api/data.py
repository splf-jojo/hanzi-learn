from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.data import LearningDataOut
from ..services.learning_data import get_learning_data

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/data", response_model=LearningDataOut)
def data(db: Session = Depends(get_db)) -> LearningDataOut:
    return get_learning_data(db)

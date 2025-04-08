from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from pydantic import BaseModel


class ConsumerAnalysisBase(BaseModel):

    analysis_data: Dict[str, Any]
    raw_response: Optional[str] = None


class ConsumerAnalysisCreate(ConsumerAnalysisBase):

    user_id: uuid.UUID


class ConsumerAnalysisInDBBase(ConsumerAnalysisBase):

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsumerAnalysis(ConsumerAnalysisInDBBase):

    pass

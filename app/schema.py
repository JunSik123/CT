from typing import List, Optional

from pydantic import BaseModel


class IdentifyResult(BaseModel):
    item_seq: str
    item_name: str
    entp_name: str
    score: float
    image_url: Optional[str] = None


class IdentifyResponse(BaseModel):
    results: List[IdentifyResult]
    uncertain: bool
    message: Optional[str] = None

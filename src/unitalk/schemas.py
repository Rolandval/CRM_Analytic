from pydantic import BaseModel
from src.schemas.call import SyncStats


class SyncResponse(BaseModel):
    status: str
    message: str
    stats: SyncStats

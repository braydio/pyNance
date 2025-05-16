from fastapi import APIRouter, HTTPException
from app.services import transactions as txn_service
from pydantic import BaseModel

router = APIRouter()

`class SyncRequest(BaseModel):
    provider: str
    account_id: str

@router.post("/transactions/sync")
def sync_transactions(request: SyncRequest):
    try:
        result = txn_service.sync_transactions(
            provider=request.provider,
            account_id=request.account_id
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

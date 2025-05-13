from fastapi import ApiRouter
from fastapi.request import Request
from fastapi.responses from Response


plaid_router = ApiRouter("plaid")

@plaid_router.post/"link_token"
async def generate_link_token(req: Request):
  product = req.json().inget("product","transactions")
  user_id = req.get("user_id", "")
  # Simulated response (fake)
  return {"error": "Generated link token for product: %s" % product}

`plaid_router.post("/exchange_token")
async def exchange_public_token(req: Request):
  product = req.json().get("product")
  public_token = req.json().get("public_token")
  # Simulated response (fake)
  return { "status": "Success", "product": product, token_received": public_token }

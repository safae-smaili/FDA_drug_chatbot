"""

"""
from fastapi import FastAPI, Request
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.chain import get_answer
from app.models import ChatRequest, ChatResponse
from app.rate_limit import limiter,rate_limit_handler

settings.validate()

app=FastAPI(
    title="FDA Drug Labels Chatbot",
    description=("A RAG-powered chatbot that answers questions about FDA-approved "),
    version="0.1.0"
)

app.state.limiter=limiter

app.add_exception_handler(RateLimitExceeded,rate_limit_handler)

@app.post("/chat",response_model=ChatResponse)
@limiter.limit("15/minute")
async def chat(request:Request,body:ChatRequest):
    answer=get_answer(
        question=body.question,
        session_id=body.session_id
    )
    return ChatResponse(answer=answer)

@app.get("/health")
async def health() -> dict:
    """Simple endpoint to verify the service is alive."""
    return {"status": "ok"}
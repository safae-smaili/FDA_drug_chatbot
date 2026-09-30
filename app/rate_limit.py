"""
we are using a free model from google and we have ratelimit to use it
so in this file we will try to handele the response and rate limit for users so we can 
protects the gemini api quota we have
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

def rate_limit_handler(request :Request, exc:RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error":"rate_limit_exceeded",
            "message":(
                "you've sent too many requests in a short time."
                "Please wait a moment and try again."
            ),
            "retry_after_secondes":60,
        },
           )
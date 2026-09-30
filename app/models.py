"""
in this file we will describe how the user requests and the model 
returns should look like so we can protect our app from any malwares
we will have 2 models request model for user request and response modesl
for API returns
"""

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str =Field(
        ...,
        min_length=1,
        max_length=1000,
        description="the user's question",
        examples=['What drugs treat rheumatoid arthritis?'],
    )
    session_id:str=Field(
        min_length=1,
        max_length=100,
        description="Unique Id for the conversation",
        examples=["user_1"]
    )

class ChatResponse(BaseModel):
    answer:str=Field(
        ...,
        description="The chatbot's answer",
    )
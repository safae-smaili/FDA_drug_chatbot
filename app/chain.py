from operator import itemgetter

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from pinecone import Pinecone

from app.config import settings
from typing import List


pc = Pinecone(api_key=settings.PINECONE_API_KEY)

class SizedGeminiEmbeddings(GoogleGenerativeAIEmbeddings):
    def embed_documents(self, texts: List[str], **kwargs) -> List[List[float]]:
        return super().embed_documents(
            texts, output_dimensionality=768, **kwargs
        )
    
    def embed_query(self, text: str, **kwargs) -> List[float]:
        return super().embed_query(
            text, output_dimensionality=768, **kwargs
        )

embeddings = SizedGeminiEmbeddings(
    model="gemini-embedding-001",
    google_api_key=settings.GOOGLE_API_KEY
    )

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.2
)
#remove the temperature because it will be ignore it for this model

index = pc.Index(settings.PINECONE_INDEX_NAME)

vectorstore = PineconeVectorStore(
    index=index,
    embedding=embeddings,
)

retriever = vectorstore.as_retriever(
    search_kwargs={"k": 5}
)
## Our prompt 

# prompt = ChatPromptTemplate.from_template("""
# You are a medical information assistant for FDA monoclonal antibody drug labels.

# RULES:
# - Only answer using the context below.
# - If the answer isn't in the context, say so.
# - Always cite drug names.
# - Never give personalized medical advice.

# Previous conversation:
# {chat_history}

# Context:
# {context}

# Question: {question}

# Answer:
# """)
prompt = ChatPromptTemplate.from_template("""
You are a medical information assistant for FDA monoclonal antibody drug labels.

RULE 1 — SCOPE
You only answer questions about FDA-approved monoclonal antibody drugs that are 
in the provided context. You do not answer questions about:
  - General medical topics (e.g., "What causes diabetes?")
  - Non-medical topics (e.g., "What is the weather?")
  - Other drug classes (e.g., antibiotics, painkillers, vaccines)
If the question is out of scope, respond: "I can only answer questions about the 
FDA-approved monoclonal antibody drugs in my database. Your question appears to 
be outside that scope."

RULE 2 — INSUFFICIENT INFORMATION
If the provided context does not contain enough information to answer the 
question, respond: "I don't have enough information in the available FDA drug 
labels to answer this question accurately."
Do NOT guess, invent, or use general medical knowledge.

RULE 3 — PARTIAL ANSWERS
If the context only partially answers the question, answer what you can and 
explicitly state what is missing.

RULE 4 — NO PERSONALIZED ADVICE
Never recommend a specific drug for a specific person. Never give dosage advice 
for an individual patient. If asked, respond: "I cannot provide personalized 
medical advice. Please consult a qualified healthcare provider for treatment 
recommendations."

RULE 5 — ALWAYS CITE
Always mention the specific drug name(s) from the context in your answer. 
Use the format: "DrugName (GenericName)".

RULE 6 — NO HALLUCINATION
Only use information explicitly stated in the context below. Do NOT use your 
general training knowledge. If you are unsure, say so.

Previous conversation:
{chat_history}

Context:
{context}

Question: {question}

Answer:
""")


rewrite_prompt = ChatPromptTemplate.from_template("""
Given the conversation below and a follow-up question, rewrite the follow-up
question into a standalone question that is fully understandable on its own.

Rules:
- You MUST include the specific drug names mentioned in the conversation.
- Replace pronouns (it, they, their, etc.) with the drug names they refer to.
- Identify every pronoun or vague reference in the question.
- Replace each one with the specific entity it refers to from the conversation.
- Preserve all specific names (drugs, diseases, conditions) that appear in the
  conversation and are relevant to the follow-up.
- If the follow-up question is already standalone (no pronouns, no vague
   references), return it unchanged.
- Return ONLY the rewritten question. No explanations.

EXAMPLES OF THE REWRITING PATTERN:

Conversation:
  User: What drugs treat rheumatoid arthritis?
  Assistant: Actemra and Abrilada treat rheumatoid arthritis.

Follow-up: What about their side effects?
Rewritten: What are the side effects of Actemra and Abrilada?

Conversation:
  User: What is Adbry used for?
  Assistant: Adbry is used for atopic dermatitis.

Follow-up: Is it safe for children?
Rewritten: Is Adbry safe for children?

Conversation history:
{chat_history}

Follow-up question:
{question}

Standalone question:
""")
#the rewrite chain
rewrite_chain = rewrite_prompt | llm | StrOutputParser()

#this is the function that will orginise the chunck or info to the model
# def format_docs(docs):
#     return "\n\n---\n\n".join(
#         f"[Drug: {d.metadata.get('drug_name', 'Unknown')}]\n{d.page_content}"
#         for d in docs
#     )
def format_docs(docs):
    parts = []
    for doc in docs:
        drug = doc.metadata.get("full_name") or doc.metadata.get("source", "Unknown")
        print(f"[RETRIEVED] {drug}")   # ← ADD THIS LINE
        drug = drug.replace("_", " ")
        parts.append(f"[Drug: {drug}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)

def should_rewrite(question, chat_history):

#this fuction is to see if the rewriting is needed or not if there is an umbegity for example if there is pronouns like their it ...
  
    if not chat_history or len(chat_history) == 0:
        return False
    
    # very short questions
    if len(question.split()) <= 5:
        return True
    
    # pronouns
    pronouns = {
        "it", "its", "they", "them", "their", "theirs",
        "this", "that", "these", "those",
        "he", "she", "him", "her", "his", "hers",
        "the same", "the other", "the former", "the latter"
    }
    question_words = set(question.lower().split())
    if question_words & pronouns:
        return True
    
    #follow-up phrases
    follow_up_starters = [
        "what about", "how about", "and what", "and how",
        "tell me more", "explain more", "go on",
        "also", "then", "so", "but"
    ]
    if any(question.lower().startswith(s) for s in follow_up_starters):
        return True
    return False

def prepare_query(question, chat_history):
    if not should_rewrite(question, chat_history):
        return question       
    
    rewritten = rewrite_chain.invoke({
        "question": question,
        "chat_history": chat_history
    })
    print(f"REWRITTEN '{question}' → '{rewritten}'")
    return rewritten.strip()


def prepare_query_input(input_dict):
    """return rewritten question."""
    question = input_dict["question"]
    chat_history = input_dict.get("chat_history", [])
    return prepare_query(question, chat_history)

rag_chain = (
    {
        "context": prepare_query_input | retriever | format_docs,       
        "question": itemgetter("question"),
        "chat_history": itemgetter("chat_history"),
    }
    | prompt
    | llm
    | StrOutputParser()
)

### session memory:
sessions = {}

def get_session_history(session_id: str):

    if session_id not in sessions:
        sessions[session_id] = InMemoryChatMessageHistory()
    return sessions[session_id]

conversational_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history"
)


DISCLAIMER = (
    "\n\n---\n"
    "This information is for educational purposes only and is not "
    "medical advice. Always consult a qualified healthcare provider."
)

def get_answer(question, session_id) :
    
    answer = conversational_chain.invoke(
        {"question": question},
        config={"configurable": {"session_id": session_id}},
    )
    return answer + DISCLAIMER
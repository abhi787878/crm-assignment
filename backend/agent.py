import os
import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Load API Key from .env
load_dotenv()

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# 1. State Definition
class AgentState(TypedDict):
    text: str
    db_context: str
    intent: str
    is_compliant: bool
    compliance_reason: str
    extracted_data: dict
    query_response: str
    drafted_email: str

# 2. Schemas
class IntentSchema(BaseModel):
    intent: str = Field(description="'log' to record a meeting, 'edit' to update or fix the last meeting, 'query' to ask about past data, 'draft' to write a follow-up email.")

class ComplianceSchema(BaseModel):
    is_compliant: str = Field(description="Strictly output the word 'true' if safe, or 'false' if it contains bribery or explicit off-label promotion.")
    reason: str = Field(description="Reason for the compliance decision.")

class ExtractedInfo(BaseModel):
    hcp_name: str = Field(description="Name of the Healthcare Professional")
    interaction_type: str = Field(description="Meeting, Video Call, Phone, or Email")
    # NEW: Forces the AI to strictly use YYYY-MM-DD so the calendar works
    interaction_date: str = Field(description="Date of the interaction (MUST be exactly in YYYY-MM-DD format)")
    interaction_time: str = Field(description="Time of the interaction (e.g., 10:30 AM)")
    attendees: str = Field(description="Other people present")
    topics_discussed: str = Field(description="Main topics of conversation")
    materials_shared: str = Field(description="Documents or brochures given")
    samples_distributed: str = Field(description="Drug samples given and quantity")
    sentiment: str = Field(description="Strictly 'Positive', 'Neutral', or 'Negative'")
    outcomes: str = Field(description="Result of the meeting")
    next_steps: str = Field(description="Follow-up actions needed")

# 3. Nodes (The 5 Tools)
def router_node(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Determine the user's intent: 'log', 'edit', 'query', or 'draft'."),
        ("human", "{text}")
    ])
    chain = prompt | llm.with_structured_output(IntentSchema)
    result = chain.invoke({"text": state["text"]})
    return {"intent": result.intent}

def compliance_node(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a pharmaceutical compliance officer. Check the notes for bribery, illegal incentives, or explicit off-label promotion. Normal discussions about clinical trials, sharing standard samples, or general positive feedback are completely compliant and safe to log. ONLY block severe violations like bribery or explicit off-label promotion."),
        ("human", "{text}")
    ])
    chain = prompt | llm.with_structured_output(ComplianceSchema)
    result = chain.invoke({"text": state["text"]})
    is_safe = str(result.is_compliant).strip().lower() == "true"
    return {"is_compliant": is_safe, "compliance_reason": result.reason}

def extractor_node(state: AgentState):
    # NEW: Grabs the actual real-world date to inject into the AI's brain
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Extract the required fields from the notes. Today's date is {today}. Convert relative words like 'today' or 'yesterday' into the exact YYYY-MM-DD format. If the user is editing or updating a previous meeting, use this database history to fill in missing details: {{db_context}}. If a field is not mentioned, write 'None'."),
        ("human", "{text}")
    ])
    chain = prompt | llm.with_structured_output(ExtractedInfo)
    result = chain.invoke({"text": state["text"], "db_context": state.get("db_context", "")})
    return {"extracted_data": result.model_dump()}

def query_node(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful CRM assistant. Answer the user's question using ONLY this database history context: {db_context}. Be concise and conversational."),
        ("human", "{text}")
    ])
    chain = prompt | llm
    result = chain.invoke({"text": state["text"], "db_context": state.get("db_context", "")})
    return {"query_response": result.content}

def draft_node(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional medical sales rep. Draft a short, polite follow-up email based on these notes. Do not include subject lines, just the email body."),
        ("human", "{text}")
    ])
    chain = prompt | llm
    result = chain.invoke({"text": state["text"]})
    return {"drafted_email": result.content}

# 4. Routing Logic
def route_logic(state: AgentState):
    intent = state.get("intent", "")
    if intent in ["log", "edit"]:
        return "compliance"
    elif intent == "draft":
        return "draft"
    else:
        return "query"

def compliance_route(state: AgentState):
    if state.get("is_compliant"):
        return "extractor"
    return END

# 5. Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("compliance", compliance_node)
workflow.add_node("extractor", extractor_node)
workflow.add_node("query", query_node)
workflow.add_node("draft", draft_node)

workflow.set_entry_point("router")
workflow.add_conditional_edges("router", route_logic)
workflow.add_conditional_edges("compliance", compliance_route)
workflow.add_edge("extractor", END)
workflow.add_edge("query", END)
workflow.add_edge("draft", END)

crm_agent = workflow.compile()

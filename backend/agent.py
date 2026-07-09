import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# 1. Schemas
class IntentSchema(BaseModel):
    intent: str = Field(description="'log' to record a meeting, 'query' to ask about past data, 'draft' to write a follow-up email.")

class ComplianceSchema(BaseModel):
    is_compliant: bool = Field(description="True if safe. False if it contains off-label promotion, bribery, or compliance risks.")
    reason: str = Field(description="Explanation of the compliance decision.")

class ExtractedInfo(BaseModel):
    hcp_name: str = Field(description="Name of the Healthcare Professional")
    interaction_type: str = Field(description="e.g., Meeting, Video Call, Email, Phone")
    interaction_date: str = Field(description="Date of interaction strictly in YYYY-MM-DD format (e.g., '2026-07-09') or ''")
    interaction_time: str = Field(description="Time of interaction strictly in 24-hour HH:mm format (e.g., '14:00' for 2 PM) or ''")
    attendees: str = Field(description="Names of people present")
    topics_discussed: str = Field(description="Key discussion points or products mentioned")
    materials_shared: str = Field(description="Any documents, brochures, or materials shared")
    samples_distributed: str = Field(description="Any product samples given")
    sentiment: str = Field(description="MUST be 'Positive', 'Neutral', or 'Negative'")
    outcomes: str = Field(description="Key outcomes or agreements")
    next_steps: str = Field(description="Recommended next steps or follow-ups")

# 2. Graph State
class AgentState(TypedDict):
    text: str
    intent: str
    extracted_data: dict
    db_context: str
    chat_response: str
    is_compliant: bool
    compliance_reason: str

# 3. Nodes
def router_node(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Determine the user's intent: 'log', 'query', or 'draft'."),
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
    return {"is_compliant": result.is_compliant, "compliance_reason": result.reason}

def extractor_node(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract the required fields from the notes. If not mentioned, write 'None'."),
        ("human", "{text}")
    ])
    chain = prompt | llm.with_structured_output(ExtractedInfo)
    result = chain.invoke({"text": state["text"]})
    return {"extracted_data": result.model_dump()}

def query_node(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful CRM assistant. Answer the user's question based ONLY on this database history:\n{db_context}"),
        ("human", "{text}")
    ])
    chain = prompt | llm
    result = chain.invoke({"db_context": state.get("db_context", "No history available."), "text": state["text"]})
    return {"chat_response": result.content}

def draft_node(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Draft a professional follow-up email to the healthcare professional based on these notes. Keep it concise and polite."),
        ("human", "{text}")
    ])
    chain = prompt | llm
    result = chain.invoke({"text": state["text"]})
    return {"chat_response": result.content}

# 4. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("router", router_node)
workflow.add_node("compliance", compliance_node)
workflow.add_node("extractor", extractor_node)
workflow.add_node("query", query_node)
workflow.add_node("draft", draft_node)

workflow.set_entry_point("router")

# Routing Logic
def route_logic(state: AgentState):
    if state.get("intent") == "log":
        return "compliance"
    elif state.get("intent") == "draft":
        return "draft"
    else:
        return "query"

def compliance_route(state: AgentState):
    if state.get("is_compliant"):
        return "extractor"
    else:
        return "end"

workflow.add_conditional_edges("router", route_logic, {"compliance": "compliance", "query": "query", "draft": "draft"})
workflow.add_conditional_edges("compliance", compliance_route, {"extractor": "extractor", "end": END})
workflow.add_edge("extractor", END)
workflow.add_edge("query", END)
workflow.add_edge("draft", END)

crm_agent = workflow.compile()

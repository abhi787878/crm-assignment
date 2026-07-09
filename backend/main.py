from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db
import models
from agent import crm_agent
import traceback

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/interaction/process", response_model=models.InteractionResponse)
async def process_interaction(payload: models.InteractionCreate, db: Session = Depends(get_db)):
    try:
        # 1. Fetch DB history
        recent_records = db.query(models.InteractionModel).order_by(models.InteractionModel.id.desc()).limit(20).all()
        db_context = "".join([f"- Meeting with {r.hcp_name} on {r.interaction_date}. Topics: {r.topics_discussed}. Sentiment: {r.sentiment}\n" for r in recent_records])

        # 2. Run the Multi-Agent Workflow
        print(f"🤖 Routing text: '{payload.text}'")
        final_state = crm_agent.invoke({"text": payload.text, "db_context": db_context})

        # 3. Handle based on Intent and Compliance
        if final_state["intent"] == "log":
            
            # TOOL 5: COMPLIANCE CHECK TRIGGERED
            if final_state.get("is_compliant") is False:
                return {
                    "message": f"🚨 COMPLIANCE BLOCKED: {final_state.get('compliance_reason')}\n\nThis interaction was NOT saved to the database.",
                    "action_type": "query", # Renders as a chat message
                    "interaction_data": None
                }

            # If compliant, save normally!
            ai_result = final_state.get("extracted_data", {})
            new_interaction = models.InteractionModel(
                hcp_name=ai_result.get("hcp_name", ""),
                interaction_type=ai_result.get("interaction_type", ""),
                interaction_date=ai_result.get("interaction_date", ""),
                interaction_time=ai_result.get("interaction_time", ""),
                attendees=ai_result.get("attendees", ""),
                topics_discussed=ai_result.get("topics_discussed", ""),
                materials_shared=ai_result.get("materials_shared", ""),
                samples_distributed=ai_result.get("samples_distributed", ""),
                sentiment=ai_result.get("sentiment", ""),
                outcomes=ai_result.get("outcomes", ""),
                next_steps=ai_result.get("next_steps", "")
            )
            db.add(new_interaction)
            db.commit()
            db.refresh(new_interaction)
            
            return {
                "message": f"✅ Compliant interaction logged for {new_interaction.hcp_name}! (ID: #{new_interaction.id})",
                "action_type": "log",
                "interaction_data": ai_result
            }
        
        elif final_state["intent"] == "draft":
            # TOOL 4: EMAIL DRAFTING
            return {
                "message": final_state.get("chat_response", "Error drafting email."),
                "action_type": "query",
                "interaction_data": None
            }
            
        else:
            # TOOL 3: QUERY
            return {
                "message": final_state.get("chat_response", "I could not find an answer."),
                "action_type": "query",
                "interaction_data": None
            }

    except Exception as e:
        print("\n--- 🚨 CRASH DETECTED 🚨 ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
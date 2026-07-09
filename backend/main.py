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

        intent = final_state.get("intent", "query")
        text_lower = payload.text.lower()
        if any(word in text_lower for word in ["change", "update", "edit", "fix", "mistake", "actually"]):
            intent = "edit"


        # 3. Handle based on Intent
        if intent in ["log", "edit"]:
            
            # TOOL 5: COMPLIANCE CHECK
            if final_state.get("is_compliant") is False:
                return {
                    "message": f"🚨 COMPLIANCE BLOCKED: {final_state.get('compliance_reason')}\n\nThis interaction was NOT saved.",
                    "action_type": "query",
                    "interaction_data": None
                }

            ai_result = final_state.get("extracted_data", {})

            # TOOL 2: FORM EDITING (Update latest record safely)
            if intent == "edit":
                last_record = db.query(models.InteractionModel).order_by(models.InteractionModel.id.desc()).first()
                if last_record:
                    def update_field(old_val, new_val):
                        # Keep the old database value if AI returns None or an empty string
                        if new_val is None or str(new_val).strip().lower() in ["none", ""]:
                            return old_val
                        return str(new_val).strip()

                    last_record.hcp_name = update_field(last_record.hcp_name, ai_result.get("hcp_name"))
                    last_record.interaction_type = update_field(last_record.interaction_type, ai_result.get("interaction_type"))
                    last_record.interaction_date = update_field(last_record.interaction_date, ai_result.get("interaction_date"))
                    last_record.interaction_time = update_field(last_record.interaction_time, ai_result.get("interaction_time"))
                    last_record.attendees = update_field(last_record.attendees, ai_result.get("attendees"))
                    last_record.topics_discussed = update_field(last_record.topics_discussed, ai_result.get("topics_discussed"))
                    last_record.materials_shared = update_field(last_record.materials_shared, ai_result.get("materials_shared"))
                    last_record.samples_distributed = update_field(last_record.samples_distributed, ai_result.get("samples_distributed"))
                    last_record.sentiment = update_field(last_record.sentiment, ai_result.get("sentiment"))
                    last_record.outcomes = update_field(last_record.outcomes, ai_result.get("outcomes"))
                    last_record.next_steps = update_field(last_record.next_steps, ai_result.get("next_steps"))
                    
                    db.commit()
                    db.refresh(last_record)
                    
                    # Package all the saved data to send back so the UI doesn't blank out
                    updated_data = {
                        "hcp_name": last_record.hcp_name,
                        "interaction_type": last_record.interaction_type,
                        "interaction_date": last_record.interaction_date,
                        "interaction_time": last_record.interaction_time,
                        "attendees": last_record.attendees,
                        "topics_discussed": last_record.topics_discussed,
                        "materials_shared": last_record.materials_shared,
                        "samples_distributed": last_record.samples_distributed,
                        "sentiment": last_record.sentiment,
                        "outcomes": last_record.outcomes,
                        "next_steps": last_record.next_steps
                    }
                    
                    return {
                        "message": f"✏️ Successfully updated previous meeting for {last_record.hcp_name}! (ID: #{last_record.id})",
                        "action_type": "log",
                        "interaction_data": updated_data
                    }
                else:
                    return {"message": "No previous record found to edit.", "action_type": "query", "interaction_data": None}

            # TOOL 1: FORM FILLING (Create new record)
            else:
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
        
        elif intent == "draft":
            # TOOL 4: EMAIL DRAFTING
            return {
                "message": final_state.get("drafted_email", "Error drafting email."),
                "action_type": "query",
                "interaction_data": None
            }
            
        else:
            # TOOL 3: QUERY
            return {
                "message": final_state.get("query_response", "I could not find an answer."),
                "action_type": "query",
                "interaction_data": None
            }

    except Exception as e:
        print("\n--- 🚨 CRASH DETECTED 🚨 ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

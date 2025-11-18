import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from database import create_document

app = FastAPI(title="iVentice API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "iVentice backend is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else (os.getenv("DATABASE_NAME") or "Unknown")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    env_db_name = os.getenv("DATABASE_NAME")
    response["database_name"] = env_db_name if env_db_name else "❌ Not Set"
    return response


class ContactMessage(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=2000)


@app.post("/contact")
async def submit_contact(payload: ContactMessage):
    """Persist contact messages for follow-up."""
    doc_id = create_document("contactmessage", payload)
    return {"status": "ok", "id": doc_id}


# --- Simple AI-like Q&A over curated site content ---
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)

class ChatResponse(BaseModel):
    answer: str

ABOUT = {
    "mission": "Enable sustainable growth through smart strategy, ethical governance and practical innovation.",
    "vision": "Clean, green and impact-driven solutions accessible to every organization.",
    "values": [
        "Innovation", "Value Addition", "Entrepreneurship", "Networks",
        "Transdisciplinary Approach", "Impactability", "Creativity", "Extensibility"
    ],
    "guiding_teams": [
        "Corporate Governance", "Risk Management", "Environmental Impact & Sustainability",
        "Agriculture & Innovation", "Research & Socio-Economic Development", "Technology / Smart Solutions"
    ]
}

TEAM = [
    {"name": "Asha Ndlovu", "role": "Executive Director", "focus": "Strategy • Partnerships • Governance"},
    {"name": "Kofi Mensah", "role": "Head of Innovation", "focus": "R&D • Prototyping • Venture Building"},
    {"name": "Lerato Dlamini", "role": "Sustainability Lead", "focus": "Clean • Green • Smart • Sustainable"},
    {"name": "Michael Okoye", "role": "Technology Director", "focus": "Cloud • Data • Platforms"},
    {"name": "Zanele Khumalo", "role": "Programs & Impact", "focus": "Monitoring • Evaluation • Impactability"},
    {"name": "Tariro Chikore", "role": "Community & Networks", "focus": "Stakeholders • Hubs • Ecosystems"},
]

SERVICES = ABOUT["guiding_teams"]

SUSTAINABILITY = [
    "Clean energy: solar and hydro integration for businesses",
    "Plastic-free initiatives and circular economy practices",
    "Carbon footprint assessments and reduction roadmaps",
    "Data-driven monitoring and reporting of impact metrics"
]


def answer_question(q: str) -> str:
    ql = q.lower()
    # Team
    if any(w in ql for w in ["team", "who works", "who is on", "members", "people"]):
        lines = ["Our core team includes:"]
        for m in TEAM:
            lines.append(f"- {m['name']} — {m['role']} ({m['focus']})")
        lines.append("We collaborate with a trusted network of domain experts and partners.")
        return "\n".join(lines)

    # Mission / Vision / Values
    if any(w in ql for w in ["mission", "vision", "values", "acronym", "iventice"]):
        lines = [
            f"Mission: {ABOUT['mission']}",
            f"Vision: {ABOUT['vision']}",
            "Values (iVENTICE): " + ", ".join(ABOUT["values"]),
        ]
        return "\n".join(lines)

    # Services / Offerings
    if any(w in ql for w in ["services", "offer", "what do you do", "capabilities"]):
        lines = ["We operate through transdisciplinary guiding teams:"]
        for s in SERVICES:
            lines.append(f"- {s}")
        lines.append("Ask for any area to see case studies or engagement models.")
        return "\n".join(lines)

    # Sustainability / Impact
    if any(w in ql for w in ["sustainability", "green", "impact", "carbon", "solar", "hydro", "plastic"]):
        lines = ["How we contribute to sustainability:"] + [f"- {x}" for x in SUSTAINABILITY]
        return "\n".join(lines)

    # Contact
    if any(w in ql for w in ["contact", "reach", "email", "call", "schedule"]):
        return (
            "You can reach us via the contact form on the site. Share your name, email and a short brief, "
            "and we will schedule a call."
        )

    # Default
    return (
        "I can help with our mission, services, team and sustainability approach. "
        "Try asking: 'What services do you offer?' or 'Who is on the iVentice team?'"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Lightweight, rule-based Q&A grounded in curated About + Team content."""
    ans = answer_question(req.question)
    return ChatResponse(answer=ans)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.pdf_loader import safe_extract
from app.graph.workflow import graph

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="upskillforjob")
app.state.limiter = limiter
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"error": "Too many requests — please wait a minute before trying again."},
        status_code=429,
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/analyze", response_class=HTMLResponse)
@limiter.limit("1/minute")
async def analyze(
    request: Request,
    resume: UploadFile = File(...),
    target_role: str = Form(...),
    location: str = Form(""),
):
    if resume.content_type != "application/pdf":
        return templates.TemplateResponse(
            request,
            "index.html",
            {"error": "Please upload a PDF file."},
        )

    file_bytes = await resume.read()
    text, err = safe_extract(file_bytes)
    if err:
        return templates.TemplateResponse(
            request, "index.html", {"error": err}
        )

    try:
        result = graph.invoke({"resume_text": text, "target_role": target_role, "location": location})
    except Exception:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"error": "Analysis failed — our AI service may be temporarily unavailable. Please try again in a moment."},
        )

    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "target_role": target_role,
            "current_skills": result.get("current_skills"),
            "required_skills": result.get("required_skills"),
            "gap_report": result.get("gap_report"),
            "learning_path": result.get("learning_path"),
        },
    )

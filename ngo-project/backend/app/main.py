"""Application entry point: creates the FastAPI app and wires everything together."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import Base, SessionLocal, engine
from .routers import beneficiaries, dashboard
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts: create tables, then add sample data if empty.
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Hope NGO Management API", version="1.0.0", lifespan=lifespan)

# CORS: lets the Vite dev server (a different origin/port) call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:4173", "http://127.0.0.1:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _friendly_message(error: dict) -> str:
    """Turn Pydantic's technical error into a short sentence for the user."""
    kind, ctx = error["type"], error.get("ctx", {})
    if kind == "missing":
        return "This field is required"
    if kind == "string_too_short":
        return f"Must be at least {ctx.get('min_length')} characters"
    if kind == "string_too_long":
        return f"Must be at most {ctx.get('max_length')} characters"
    if kind == "greater_than_equal":
        return f"Must be {ctx.get('ge')} or more"
    if kind == "less_than_equal":
        return f"Must be {ctx.get('le')} or less"
    if kind.startswith("int_"):
        return "Must be a whole number"
    if kind == "literal_error":
        return "Choose one of the allowed values"
    if kind.startswith("date"):
        return "Enter a valid date (YYYY-MM-DD)"
    return error["msg"].removeprefix("Value error, ")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Return validation problems in one clear, consistent format (HTTP 422)."""
    errors = [
        {"field": ".".join(str(part) for part in err["loc"][1:]) or "body", "message": _friendly_message(err)}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": "Please correct the highlighted fields.", "errors": errors})


app.include_router(beneficiaries.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "docs": "/docs"}

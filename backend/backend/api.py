"""FastAPI app: accept submissions, persist, print. MCP mounted at /mcp."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import db
from .mcp_server import mcp
from .printer import is_connected
from .service import PrintError, submit_and_print

log = logging.getLogger("printy")

mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    reaped = db.reap_stale_pending()
    if reaped:
        log.warning("reaped %d stale pending submissions on startup", reaped)
    async with mcp_app.lifespan(app):
        yield


printy_app = FastAPI(title="printy", version="0.1.0")
printy_app.mount("/mcp", mcp_app)

# Outer wrapper so the whole API (REST + MCP) is reachable under /printy/.
# This matches what `tailscale serve --set-path /printy` will forward, so paths
# stay identical end-to-end and we don't need any prefix stripping.
# Lifespan must live on the outermost app uvicorn serves — that's where
# FastMCP's StreamableHTTPSessionManager task group gets initialized.
app = FastAPI(lifespan=lifespan)
app.mount("/printy", printy_app)


class PrintRequest(BaseModel):
    sender: str = Field(..., alias="from", min_length=1, max_length=120)
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=10_000)

    model_config = {"populate_by_name": True}


class PrintResponse(BaseModel):
    id: int
    status: str


@printy_app.get("/health")
def health() -> JSONResponse:
    with db.connect() as c:
        c.execute("SELECT 1").fetchone()
    printer_connected = is_connected()
    body = {
        "status": "ok" if printer_connected else "degraded",
        "printer": "connected" if printer_connected else "missing",
    }
    return JSONResponse(body, status_code=200 if printer_connected else 503)


@printy_app.post("/print", response_model=PrintResponse)
def submit_print(req: PrintRequest) -> PrintResponse:
    try:
        sub_id = submit_and_print(req.sender, req.subject, req.body)
    except PrintError as exc:
        raise HTTPException(status_code=502, detail=f"print failed: {exc}") from exc
    return PrintResponse(id=sub_id, status="printed")


@printy_app.get("/submissions")
def list_recent(limit: int = 50) -> list[dict]:
    return db.list_submissions(limit=limit)


@printy_app.get("/submissions/{submission_id}")
def get_one(submission_id: int) -> dict:
    row = db.get_submission(submission_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return row

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import correlation, stress

app = FastAPI(title="Silent Co-Driver API")

# Wide-open CORS for hackathon speed. Tighten this if you have time.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stress.router)
app.include_router(correlation.router)

# NOTE for teammates: add the speech-to-text router the same way, e.g.
#   from app.routers import transcription
#   app.include_router(transcription.router)
# Keep it in its own file under app/routers/ so we don't step on each
# other's code.


@app.get("/")
async def health():
    return {"nothing broken so far"}


@app.get("/health")
async def health():
    return {"status": "ok"}
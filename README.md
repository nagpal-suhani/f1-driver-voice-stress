# The Silent Co-Driver
### Reading Driver Stress from Radio Calls — a race-engineering decision-support console

## 1. Problem statement

A driver talks to the pit wall over the radio throughout a session. This project
turns that audio into a second, objective signal: an **estimated vocal state**
(CALM / ELEVATED / STRESSED / FATIGUE-LIKE), displayed side-by-side with real
session telemetry from OpenF1, so a race engineer can see *whether* — not *why*
— a change in the driver's voice lines up with a change in lap performance.

**This is not a medical or psychological diagnostic tool.** It never claims to
detect clinical stress, fatigue, or any biometric signal it doesn't actually
measure, and it never claims that a vocal-state change *caused* a performance
change — only that the two *overlapped in time*.

## 2. Architecture

```
React (Vite/TS/Tailwind)  ──HTTP──▶  FastAPI backend  ──▶  OpenF1 API
                                            │
                                            └──▶  Hugging Face models (STT + vocal-state)
```

The frontend **only ever calls our own FastAPI server**. All secrets
(Hugging Face token, model endpoint) live in `backend/.env` and are never sent
to the browser — see `backend/app/core/config.py` and `frontend/.env.example`.

```
backend/
  app/
    main.py                     FastAPI app, CORS, router registration
    core/config.py              Settings (.env)
    models/schemas.py           Pydantic response/request models
    services/
      openf1_service.py         OpenF1 client (documented endpoints only)
      demo_data.py               Realistic, clearly-labeled fallback data
      model_service.py           Hugging Face abstraction (Whisper + emotion classifier)
      audio_service.py           Upload validation, temp storage, model orchestration
      analysis_service.py        Lap/race shaping + non-causal association analysis
    api/routes/
      sessions.py                /meetings /sessions /drivers
      race_data.py                /laps /location /race-control /weather /stints
      radio.py                    /radio (Mode A/B fallback)
      analysis.py                 /analyze-audio /analyze-session /health
  tests/                          pytest unit tests
  requirements.txt
  .env.example

frontend/
  src/
    pages/Home.tsx, Analysis.tsx, ErrorPage.tsx
    components/
      landing/   Hero.tsx, SetupForm.tsx
      driver/    DriverAvatar.tsx, DriverStatePanel.tsx, RadioPlayer.tsx,
                 TranscriptPanel.tsx, RadioTimeline.tsx, StateTimeline.tsx
      race/      RaceHeader.tsx, LapPerformance.tsx, LapHistory.tsx, SectorTimes.tsx,
                 PositionCard.tsx, RaceControlTimeline.tsx, WeatherPanel.tsx, StintPanel.tsx
      charts/    PerformanceChart.tsx, StatePerformanceChart.tsx
      map/       TrackMap.tsx
      common/    Navbar.tsx, DataPanel.tsx, ErrorState.tsx, LoadingState.tsx
    services/api.ts               Centralized typed API client
    hooks/useSession.ts, useAnalysis.ts
    types/api.ts                  TS types mirroring backend schemas
  package.json, vite.config.ts, tailwind.config.js
  .env.example
```

## 3. Tech stack

- **Frontend:** React + Vite + TypeScript, Tailwind CSS, Framer Motion, Recharts,
  Lucide React icons, native `<audio>` for playback.
- **Backend:** FastAPI, Pydantic, httpx, python-dotenv, python-multipart.
- **AI:** Hugging Face `transformers` — Whisper-family model for speech-to-text,
  an audio-classification model for vocal-state estimation.

## 4. Running locally

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edit as needed
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev                 # http://localhost:5173
```

### Tests
```bash
cd backend && pytest
```

> **Note on this environment:** this prototype was authored without network
> access to run `npm install` / `pip install` / a live build, so dependency
> installation and a full build pass have not been executed here. The code
> follows the documented APIs of each library at the pinned versions in
> `package.json` / `requirements.txt`; run the install + build steps above in
> an environment with network access before a live demo, and fix any
> version-drift issues that surface.

## 5. Environment variables

**Backend (`backend/.env`, never committed):**

| Variable | Purpose |
|---|---|
| `OPENF1_BASE_URL` | OpenF1 API base (public, no key required today) |
| `DEMO_MODE` | `true` makes **every** route return a single fixed demo dataset regardless of selection — see §8. Set `false` to use real OpenF1 data + your model API. |
| `MODEL_API_URL` | Your model API endpoint — see §7 for the exact request/response contract |
| `MODEL_API_KEY` | Sent as `Authorization: Bearer <key>` to `MODEL_API_URL` |
| `MODEL_API_TIMEOUT_SECONDS` | Request timeout for the model API call (default 30s) |
| `ALLOWED_ORIGINS` | CORS allow-list |
| `MAX_AUDIO_MB` | Upload size limit |

**Frontend (`frontend/.env`):** only `VITE_API_BASE_URL` — no secrets.

## 6. OpenF1 integration

`app/services/openf1_service.py` calls only documented OpenF1 endpoints:
`/meetings /sessions /drivers /laps /location /position /race_control /weather
/stints /team_radio /session_result`. Historical endpoints need no API key
today; if OpenF1 ever requires one, add it via a new setting rather than
inventing a requirement now. Location data is downsampled defensively before
it reaches the frontend.

## 7. Model API integration — the contract this backend speaks

`app/services/model_service.py` is the **only** file that talks to your model
API. Set `MODEL_API_URL` and `MODEL_API_KEY` in `backend/.env`; everything
else — routes, schemas, the frontend — already expects exactly this shape,
so you only need to build the API on your end.

**Request** — `POST {MODEL_API_URL}`, multipart/form-data:

```
Headers:
    Authorization: Bearer {MODEL_API_KEY}

Form fields:
    audio     — the raw audio file (mp3/wav/m4a/ogg/webm/flac)
    context   — a JSON string with this shape:

{
  "session": {
    "session_key": 9159, "session_name": "Race", "session_type": "Race",
    "circuit_short_name": "Silverstone", "country_name": "United Kingdom", "year": 2025
  },
  "driver": {
    "driver_number": 44, "full_name": "Driver Name", "team_name": "Team Name"
  },
  "lap_context": {
    "lap_number": 19, "lap_time": 91.482, "delta_to_previous": 0.577
  },
  "audio_meta": {
    "filename": "radio_clip.wav", "duration_seconds": 6.8, "source": "upload"
  }
}
```
Any field the backend doesn't have is sent as `null` — never fabricated.

**Response** — `200 OK`, JSON body this backend expects back:

```json
{
  "transcript": {
    "text": "The rear is moving quite a lot through Turn 7.",
    "segments": [
      {"start": 0.0, "end": 2.4, "text": "The rear is moving quite a lot"},
      {"start": 2.4, "end": 4.8, "text": "through Turn 7."}
    ]
  },
  "vocal_state": {
    "label": "STRESSED",
    "confidence": 0.87
  },
  "vocal_features": {
    "speech_rate_wpm": 168.0,
    "energy": "HIGH",
    "voice_activity": "HIGH",
    "pitch_variation_pct": 8.0
  }
}
```

- `vocal_state.label` **must** be one of `CALM | ELEVATED | STRESSED | FATIGUE-LIKE`
  (map your model's raw labels onto these four before returning).
- `transcript.segments` and `vocal_features` are optional — omit fields you
  can't support rather than inventing values; the frontend renders missing
  fields as "N/A".
- If the call fails, times out, or the response is malformed/missing required
  fields, `ModelUnavailable` is raised and the app **automatically falls back
  to demo data** instead of crashing — see `_parse_response()` in
  `model_service.py` for exactly what's validated.

**Where this gets called from:**
- `POST /api/analyze-audio` — for an uploaded clip, forwards the file plus
  whatever `context` the frontend sends alongside it.
- `POST /api/analyze-session` — when `DEMO_MODE=false`, the backend
  automatically downloads the most recent OpenF1 team-radio clip for the
  selected session/driver, builds the `context` from the real session/driver/
  lap data it already fetched, and sends both to your API.

## 8. Demo mode & the OpenF1 radio limitation

OpenF1's team-radio coverage isn't guaranteed for every session (see spec).
`GET /api/sessions/{key}/radio/{driver}` returns an **empty list, not an
error**, when no recordings exist, and the frontend's setup form automatically
switches to "Upload Audio" in that case — missing radio is never treated as an
application failure.

**Important:** `DEMO_MODE=true` makes *every* route (meetings, sessions,
drivers, laps, radio, analysis — all of them) return one fixed demo dataset,
regardless of the year/session/driver you pick. That's intentional — it's a
stable dataset to develop the UI against without hitting OpenF1 or your model
API every time — but it's also why every selection looks identical while it's
on. Set `DEMO_MODE=false` once `MODEL_API_URL` is pointed at a real endpoint
and you want to see real OpenF1 data vary per selection. Every demo response
still carries `is_demo: true`, surfaced in the UI as a small "DEMO DATA"
badge, so it's never ambiguous which mode you're looking at.

## 9. Data honesty

Every uncertain field is `Optional` in the backend schema and rendered as
"N/A" / "No sensor data" on the frontend — nothing is fabricated. Heart rate,
breathing rate, and other biometrics are **never shown** because no real
sensor source exists in this system; the UI explicitly states "No sensor
data" instead of hiding the absence.

## 10. Non-causal language

The state/performance panel (`analysis_service.compute_association`) only
ever describes a **temporal association** ("laps following radio activity
show, on average, higher lap-time deltas... This is a temporal association,
not a causal claim") and refuses to compute anything when fewer than two
comparable observations exist ("Insufficient observations").

## 11. Implementation notes / known simplifications

Built end-to-end within a constrained, network-isolated authoring
environment. To keep the prototype honest about what's real vs. simplified:

- **3D avatar:** implemented as a layered, state-reactive **animated SVG**
  digital-twin face — eyebrow angle, eye openness/blink, and mouth curve all
  change per state (CALM/ELEVATED/STRESSED/FATIGUE-LIKE), plus a breathing
  and glow reaction — fixed to the bottom-center of the left panel via
  `position: fixed`, rather than a full WebGL/three.js model. Swapping in a
  real 3D rig later means replacing the contents of `DriverAvatar.tsx`
  without touching layout logic.
- **Hero background:** the cinematic backdrop is CSS/SVG-generated (grid,
  gradients, motion streaks) rather than a licensed photograph, since no
  image asset pipeline was available in this environment. Drop a real image
  into `HeroBackground` in `Hero.tsx` when brand assets are ready.
- **Track map:** OpenF1's `location` endpoint returns approximate
  car-relative x/y coordinates, not GPS geometry, so `TrackMap.tsx` renders
  the driver's actual coordinate path as an SVG trace (with a lap scrubber)
  instead of a tile-based map that the coordinates wouldn't correspond to.
- **Session-level driver state:** `/api/analyze-session` currently returns
  a single vocal-state sample (from the most relevant clip) rather than a
  per-clip time series, since correlating multiple independently-analyzed
  clips against lap data needs a clip-selection UX beyond this pass. Each
  individual clip can still be analyzed via `/api/analyze-audio`.
- **Install/build not executed here:** see §4 — run `npm install` and
  `pip install -r requirements.txt` in a networked environment and fix any
  dependency-version issues before a live demo.

## 12. AI / data limitations (for judges)

- Vocal-state estimation is a heuristic mapping from a general-purpose
  speech-emotion model onto four engineering labels — not a validated
  stress/fatigue biomarker.
- No physiological/biometric sensor is integrated; none is fabricated.
- State/performance "association" is descriptive statistics over a small
  sample, not a causal or statistically-validated model.
- OpenF1 coverage (radio, location, weather, stints) varies by session; the
  app degrades gracefully wherever data is missing rather than guessing.

## 13. Future improvements

- Per-clip state time series aligned across a full session with confidence
  bands.
- Swap the SVG avatar for a rigged 3D/WebGL driver model.
- True circuit basemap overlay where official track geometry is licensed.
- Live-session polling for `Live Monitoring` mode once real-time OpenF1
  access is available.

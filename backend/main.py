from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, stocks, trade
try:
    from routes import analytics as analytics_routes
except ImportError:
    analytics_routes = None
try:
    from routes import pipeline as pipeline_routes
except ImportError:
    pipeline_routes = None
try:
    from routes import admin as admin_routes
except ImportError:
    admin_routes = None
from database import ensure_time_series_collection, ensure_indexes

app = FastAPI(title="Stock BDA Platform", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(trade.router)
if analytics_routes is not None:
    app.include_router(analytics_routes.router)
if pipeline_routes is not None:
    app.include_router(pipeline_routes.router)
if admin_routes is not None:
    app.include_router(admin_routes.router)


@app.on_event("startup")
def _startup():
    try:
        ensure_time_series_collection()
        ensure_indexes()
    except Exception as e:
        print(f"[warn] mongo init skipped: {e}")


@app.get("/")
def health_check():
    return {"status": "API is running", "version": "2.0"}

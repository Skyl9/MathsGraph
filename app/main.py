from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import concept_routes, auth_routes

app = FastAPI(
    title="Math Concepts API",
    description="API pour gérer les concepts mathématiques",
    version="1.0.0",
    docs_url="/docs",  # URL pour Swagger UI
    redoc_url="/redoc"  # URL pour ReDoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(concept_routes.router)
app.include_router(auth_routes.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
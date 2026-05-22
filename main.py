from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.tutors import router as tutors_router
from routes.sessions import router as sessions_router
from routes.reviews import router as reviews_router
from routes.profile import router as profile_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ChargedCode API",
    swagger_ui_parameters={"persistAuthorization": True},
)

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tutors_router)
app.include_router(sessions_router)
app.include_router(reviews_router)
app.include_router(profile_router)

PUBLIC_ROUTES = ["/", "/auth/register", "/auth/login", "/tutors/"]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="ChargedCode API",
        version="1.0.0",
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path, methods in schema["paths"].items():
        for method in methods.values():
            if path in PUBLIC_ROUTES:
                method["security"] = []
            else:
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

@app.get("/")
def root():
    return {"status": "API rodando ✅"}

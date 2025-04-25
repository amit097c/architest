from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from storage_routes import router as storage_router
from test_runner import router as test_runner_router

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(storage_router)
app.include_router(test_runner_router)

@app.get("/")
async def root():
    return {"message": "ArchiTest API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
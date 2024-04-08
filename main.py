from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.games import router as games_router
from api.user import router as user_router
from firebase_config import db

app = FastAPI()

origins = [
    "https://terminal-arcade.vercel.app/",
    "http://localhost:3000"  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games_router)
app.include_router(user_router)

@app.get("/")
def read_root():
    return {"Hello" : "world"}
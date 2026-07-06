from fastapi import FastAPI

from app.api.router import api_router

from app.database.base import Base 
from app.database.database import engine

app = FastAPI()

app.include_router(api_router)

@app.get('/')
def sanity_check():
    return {'status': 'ok'}

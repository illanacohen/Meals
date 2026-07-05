from fastapi import FastAPI
from app.api.router import api_router
from fastapi.routing import APIRoute

app = FastAPI()

app.include_router(api_router)

@app.get('/')
def sanity_check():
    return {'status': 'ok'}

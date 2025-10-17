from fastapi import FastAPI

from api.main import *

app = FastAPI()

app.include_router()
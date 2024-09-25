import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PIPEFY_API_URL = "https://api.pipefy.com/graphql"
    PIPEFY_API_TOKEN = os.getenv('PIPEFY_API_TOKEN')
    PIPEFY_PIPE_ID = os.getenv('PIPEFY_PIPE_ID')

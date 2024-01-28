from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from settings.parameters import ParkingSpotCFG
from router import parking_spot
from utils.generators import initialize_csv
import uvicorn
import logging


# Declare a Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

api_config = ParkingSpotCFG()


app = FastAPI(
    title=api_config.title,
    version=api_config.version,
    description=api_config.description,
    root_path=api_config.root_path,
)

filename = api_config.csv_filename
file_exists = initialize_csv(filename)
if file_exists:
    logger.info(f"Appending to existing file {filename}")
else:
    logger.info(f"Created new file {filename}")


# Middleware
# Allow these origins to access the API
ORIGINS = [
    # "http://localhost",
    # "http://localhost:5500",
    # "http://127.0.0.1:5500",
    # "http://localhost:3000",
    # "http://localhost:5173",
    # "https://www.noloreader.org",
    # "https://www.nololector.org",
    # "http://elk.latampod.com:3006",
    # "http://10.60.25.20:3006",
    # "http://10.60.25.69:3000",
    "*"
]

# Allow these methods to be used
METHODS = ["*"] #["GET", "POST", "PUT", "PATCH", "DELETE"]

# Only these headers are allowed
# headers = ["Content-Type", "Authorization"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=METHODS,
    allow_headers=["*"],
)


# Entry Point
@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def docs():
    return RedirectResponse(url="/docs")


# Router
app.include_router(parking_spot.router)


# Run the API Server
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

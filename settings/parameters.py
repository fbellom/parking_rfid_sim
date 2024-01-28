import os
from dotenv import load_dotenv
import logging

load_dotenv()

DESCRIPTION_DATA = """
Parking Lot Availability API helps you manage Parking Slot
"""


# Set Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


class ParkingSpotCFG:
    """
    Initials Parameters
    """

    def __init__(self):
        self.title = "Parking Spot Availability API Backend"
        self.description = DESCRIPTION_DATA
        self.version = "1.1.0" or os.getenv("API_VERSION")
        self.secret_key = "" or os.getenv("SECRET_KEY")
        self.root_path = "" or os.getenv("API_ROOT_URI")
        self.run_mode = "" or os.getenv("API_RUN_MODE")
        self.logs_cfg = logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s"
        )
        self.csv_filename = "parking_simulation_log.csv"

        # inform
        logger.info("Config in Use", extra={"data": self})

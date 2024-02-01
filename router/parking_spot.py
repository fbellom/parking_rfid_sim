import asyncio
from fastapi import APIRouter, HTTPException, status, Body, WebSocket
from fastapi_utils.tasks import repeat_every
from models.parking_model import (
    ParkingEntry,
    ParkingLotLocation,
    ParkingOcuppancy,
    ParkingGateInfo,
    ParkingSimulation,
)
from utils.generators import *
import datetime
import logging
from typing import List

# Create Logger
logger = logging.getLogger(__name__)

# Module specific Libraries


# Global Vars
MODULE_NAME = "parking"
MODULE_PREFIX = "/parking"
MODULE_TAGS = [MODULE_NAME]
MODULE_DESCRIPTION = ""

# Simulation DATA Mockup
PARKING_DATA = None
PARKING_LOT_SIZE = None
PARKING_LOT_LOCATION = None
GATE_HEX_UUID = None
GATE_DESC = None


# Simulator Conditions to Create a More realistic behavior
RUSH_HOURS = [(7.5, 9), (13, 14.5)]  # Rush Hour Periods in Hours
PEAK_MEAN = 8.25  # Rush Hour in the Morning
PEAK_STD_DEV = 0.25  # Standard Deviation
MIN_PARKING_DURATION_IN_SECS = 900  # 15 minutes
MIN_SEARCHING_DURATION_IN_SECS = 120  # 2 minutes
HOURS_PROBABILITY = generate_entry_exit_hourly_probs()
NON_RUSH_HOURS_PROB_DICT = {"entry_prob": 0.5, "exit_prob": 0.5, "is_rush": False}
SIMULATION_START = None
SIMULATION_STOP = None

# Data Collector
PARKING_ACTIVITY_FILENAME = "parking_simulation_log.csv"


# FastAPI Instance
router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)

# Handlers


# Models


# Environment
random.seed(42)


# Simulation
def simulate_vehicle_entry():
    location = generate_random_location(PARKING_LOT_LOCATION)
    entry = ParkingEntry(
        rfid=generate_random_string(),
        size=random.choice(["small", "medium", "large"]),
        driver_name=generate_random_string(5),
        entry_time=datetime.datetime.now(),
        latitude=location["latitude"],
        longitude=location["longitude"],
        status="searching",
        gateid=GATE_HEX_UUID,
    )
    entry.status_start_time = datetime.datetime.now()
    PARKING_DATA.append(entry.dict())
    append_to_csv(PARKING_ACTIVITY_FILENAME, entry.dict())
    logger.info(f"Vehicle Entered and Seraching for spot: {entry}")


def safely_remove_vehicle(vehicle=None):
    try:
        PARKING_DATA.remove(vehicle)
        logger.info(f"Vehicle Exiting; {vehicle}")
    except ValueError:
        logger.error(f"Attempted to remove a vehicle not in parking data: {vehicle}")


def simulate_vehicle_exit(vehicle=None):
    if not vehicle and PARKING_DATA:
        vehicle = random.choice(PARKING_DATA)

    if vehicle:
        vehicle["exit_time"] = datetime.datetime.now()
        if vehicle["status"] == "searching":
            vehicle["reason"] = "lot_full"
        elif vehicle["status"] == "parked":
            vehicle["reason"] = "normal_leaving"
        vehicle["status"] = "leaving"
        append_to_csv(PARKING_ACTIVITY_FILENAME, vehicle)
        safely_remove_vehicle(vehicle)


def simulate_vehicle_parking():
    current_time = datetime.datetime.now()
    # Calculate ocuppancy rate
    occupancy_rate = (
        len([vehicle for vehicle in PARKING_DATA if vehicle["status"] == "parked"])
        / PARKING_LOT_SIZE
    )

    # look for searching vehicles
    for vehicle in PARKING_DATA:
        if vehicle["status"] == "searching":
            search_duration = (
                current_time - vehicle["status_start_time"]
            ).total_seconds() / 60  # in minutes
            additional_search_time = calculate_additional_search_time(
                occupancy_rate, (MIN_SEARCHING_DURATION_IN_SECS / 60)
            )
            if search_duration >= additional_search_time:
                vehicle["status"] = "parked"
                vehicle["status_start_time"] = datetime.datetime.now()
                append_to_csv(PARKING_ACTIVITY_FILENAME, vehicle)
                logger.info(f"Vehicle Parked: {vehicle}")


def prepare_parking_data():
    # Convert datetime objects to strings
    serialized_data = []
    for entry in PARKING_DATA:
        serialized_entry = {
            key: value.isoformat() if isinstance(value, datetime.datetime) else value
            for key, value in entry.items()
        }
        serialized_data.append(serialized_entry)
    return serialized_data


def prepare_parking_util_data():
    utilization = ParkingOcuppancy(
        spots_in_use=len(
            [vehicle for vehicle in PARKING_DATA if vehicle["status"] == "parked"]
        ),
        spots_avail=PARKING_LOT_SIZE
        - len([vehicle for vehicle in PARKING_DATA if vehicle["status"] == "parked"]),
        usage_rate=(
            len([vehicle for vehicle in PARKING_DATA if vehicle["status"] == "parked"])
            / PARKING_LOT_SIZE
        )
        * 100,
    )

    return utilization


def prepare_gate_info():
    gate_info = ParkingGateInfo(
        gate_id=GATE_HEX_UUID,
        gate_desc=GATE_DESC,
        latitude=PARKING_LOT_LOCATION["latitude"],
        longitude=PARKING_LOT_LOCATION["longitude"],
    )

    return gate_info


# Start a Simulation
@router.on_event("startup")
@repeat_every(seconds=10)  # every 10 seconds
async def simulate_parking_activity():
    """
    Simulation Code
    """

    # TODO: Validate Globals Has been set by the /start_simulation call
    if PARKING_DATA is None:
        logger.warning("Initial Parking Info needed. Please use /start_sim")
        return {"msg": "use start_simulation to set the gate"}

    logger.info(
        f"Starting Parking Activity Sensor Simulation for a Lot of {PARKING_LOT_SIZE} spots located at {PARKING_LOT_LOCATION}"
    )
    current_time = datetime.datetime.now()
    current_day_of_week = datetime.datetime.today().weekday()
    current_hour = current_time.hour + current_time.minute / 60
    nearest_quarter_hour = round(current_hour * 4) / 4
    entry_prob = HOURS_PROBABILITY.get(nearest_quarter_hour, NON_RUSH_HOURS_PROB_DICT)[
        "entry_prob"
    ]

    # Modify entry_prob based on day of week
    entry_prob = adjust_probability_for_day_of_week(entry_prob, current_day_of_week)

    exit_prob = HOURS_PROBABILITY.get(nearest_quarter_hour, NON_RUSH_HOURS_PROB_DICT)[
        "exit_prob"
    ]

    logger.info(
        f" Initializers : Current Hour {current_hour} , Nearest Quarter Hour : {nearest_quarter_hour} ,Entry/Exit Prob: {entry_prob}/{exit_prob}"
    )

    parked_cars = len(
        [vehicle for vehicle in PARKING_DATA if vehicle["status"] == "parked"]
    )
    logger.info(f"Occupancy {parked_cars}/{PARKING_LOT_SIZE}")
    logger.info(f"Occupancy % {(parked_cars/PARKING_LOT_SIZE) * 100}")

    if random.random() < entry_prob and len(PARKING_DATA) < PARKING_LOT_SIZE:
        logger.info(f"Vehicle Entering to Parking Lot")
        simulate_vehicle_entry()

    # Delay before checking for exits
    await asyncio.sleep(5)  # Introduce a small delay

    if PARKING_DATA:
        # Randomly select a vehicle for potential exit
        vehicle = random.choice(PARKING_DATA)
        time_in_current_status = (
            current_time - vehicle["status_start_time"]
        ).total_seconds()
        adjusted_exit_prob = exit_prob

        if len(PARKING_DATA) == PARKING_LOT_SIZE:
            # Increase exit probability if the lot is full
            logger.info("Parking Lot Full")
            adjusted_exit_prob *= 1.2
        elif (
            len(PARKING_DATA) < PARKING_LOT_SIZE
            and HOURS_PROBABILITY.get(nearest_quarter_hour, NON_RUSH_HOURS_PROB_DICT)[
                "is_rush"
            ]
        ):
            # Adjust exit probability during rush hour
            adjusted_exit_prob *= 0.9

        should_exit = random.random() < adjusted_exit_prob

        if (
            vehicle["status"] == "parked"
            and time_in_current_status >= MIN_PARKING_DURATION_IN_SECS
        ) or (
            vehicle["status"] == "searching"
            and time_in_current_status >= MIN_SEARCHING_DURATION_IN_SECS
        ):
            if should_exit:
                logger.info(f"Vehicle Exiting Parking Lot: {vehicle}")
                simulate_vehicle_exit(vehicle)

    # Additionally, simulate parking and exiting
    if len(PARKING_DATA) < PARKING_LOT_SIZE:
        simulate_vehicle_parking()


# Routes
@router.get("")
def index():
    return {
        "mesagge": f"Hello to module: {MODULE_NAME}",
        "module": MODULE_NAME,
    }


@router.post("/start_sim", status_code=status.HTTP_201_CREATED)
async def start_simulation(parking: ParkingSimulation):
    global PARKING_LOT_LOCATION
    global PARKING_LOT_SIZE
    global PARKING_DATA
    global PARKING_LOT_SIZE
    global PARKING_LOT_LOCATION
    global PARKING_ACTIVITY_FILENAME
    global GATE_HEX_UUID
    global GATE_DESC
    global SIMULATION_START

    # Set the values
    PARKING_LOT_LOCATION = {}
    PARKING_LOT_LOCATION["latitude"] = parking.latitude
    PARKING_LOT_LOCATION["longitude"] = parking.longitude
    PARKING_LOT_SIZE = parking.lot_size
    PARKING_DATA = []
    GATE_HEX_UUID = generate_gate_id()
    GATE_DESC = parking.gate_desc
    SIMULATION_START = datetime.datetime.now()

    logger.info(f"Simulation started for parking lot at gate : {GATE_DESC}")
    return {"message": f"Simulation started for parking lot at gate : {GATE_DESC}  "}


@router.put("/stop_sim", status_code=status.HTTP_202_ACCEPTED)
async def stop_simulation():
    """
    STOP All Simulations
    """
    global PARKING_LOT_LOCATION
    global PARKING_LOT_SIZE
    global PARKING_DATA
    global PARKING_LOT_SIZE
    global PARKING_LOT_LOCATION
    global PARKING_ACTIVITY_FILENAME
    global GATE_HEX_UUID
    global GATE_DESC
    global SIMULATION_START
    global SIMULATION_STOP

    # Set the values to None
    PARKING_LOT_LOCATION = None
    PARKING_LOT_SIZE = None
    PARKING_DATA = None
    PARKING_ACTIVITY_FILENAME = None
    GATE_HEX_UUID = None
    GATE_DESC = None
    SIMULATION_STOP = datetime.datetime.now()

    duration = SIMULATION_STOP - SIMULATION_START

    duration.total_seconds()
    logger.info(f"Simulation Stopped. Duration: {str(duration.total_seconds())} secs")

    return {
        "message": f"Simulation Stopped. Duration: {str(duration.total_seconds())} secs"
    }


@router.get("/available", response_model=ParkingOcuppancy)
async def get_parking_spot_availability():
    utilization = prepare_parking_util_data()

    return utilization


@router.get("/detail", response_model=List[ParkingEntry])
async def get_all_used_spot_detail():
    return PARKING_DATA


@router.get("/gate", response_model=ParkingGateInfo)
async def get_gate_info():
    gate = prepare_gate_info()
    return gate


# WebSocket
@router.websocket("/ws/parking_activity")
async def websocket_parking_activity(websocket: WebSocket):
    await websocket.accept()
    data_type = websocket.query_params.get("type", "activity")
    while True:
        # Prepare Data
        if data_type == "activity":
            data = prepare_parking_data()
        elif data_type == "util":
            data = prepare_parking_util_data()
            data = data.dict()
        else:
            data = {}

        # send data to client
        await websocket.send_json(data)

        # add some time before next update
        await asyncio.sleep(10)

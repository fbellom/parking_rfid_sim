from pydantic import BaseModel
import datetime


class ParkingEntry(BaseModel):
    rfid: str
    size: str
    driver_name: str
    entry_time: datetime.datetime = None
    exit_time: datetime.datetime = None
    latitude: float
    longitude: float
    status: str = "searching"  # 'searching', 'parked', 'leaving'
    status_start_time: datetime.datetime = None
    reason: str = ""  # normal, no spot,
    gateid: str = ""


class ParkingLotLocation(BaseModel):
    latitude: float
    longitude: float


class ParkingOcuppancy(BaseModel):
    spots_in_use: int = 0
    spots_avail: int = 0
    usage_rate: float = 0.0


class ParkingGateInfo(BaseModel):
    gate_id: str = ""
    gate_desc: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


class ParkingSimulation(BaseModel):
    lot_size: int = 0
    gate_desc: str = ""
    latitude: float = 0.0
    longitude: float = 0.0

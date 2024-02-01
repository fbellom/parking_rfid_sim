import random
import string
import numpy as np
from scipy.stats import norm
import csv
import os
import uuid


def generate_random_string(length=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_gate_id():
    return uuid.uuid4().hex

def generate_random_location(base_location, radius=0.01):
    return {
        "latitude": base_location["latitude"] + random.uniform(-radius, radius),
        "longitude": base_location["longitude"] + random.uniform(-radius, radius),
    }


def is_rush_hour(current_time, rush_hours):
    hour = current_time.hour + current_time.minute / 60
    return any(start <= hour <= end for start, end in rush_hours)


def calculate_event_probability(current_time, peak_mean, peak_std_dev):
    hour = current_time.hour + current_time.minute / 60
    return np.exp(-0.5 * ((hour - peak_mean) / peak_std_dev) ** 2)


# def get_entry_exit_probabilities(is_rush_hour):
#     if is_rush_hour:
#         return (0.7, 0.3)  # 70% chance of entry, 30% chance of exit
#     else:
#         return (0.3, 0.7)  # 30% chance of entry, 70% chance of exit

def initialize_csv(filename:str):
    headers = ["RFID", "Size", "Driver Name", "Entry Time", "Exit Time", "Lat","Long","Status", "Last Status Change", "Gate"]

    file_exists = os.path.exists(filename)

    if not file_exists:
        with open(filename, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()        

    return file_exists

def append_to_csv(filename:str, parking_record):

    with open(filename, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=parking_record.keys())
        writer.writerow(parking_record)

def generate_entry_exit_hourly_probs(
    start: float = 7.0,
    mid_day: float = 14.25,
    end_day: float = 20.0,
    entry_peak_mean: float = 10.25,
    entry_peak_std_dev: float = 1.0,
    exit_peak_mean: float = 16.5,
    exit_peak_std_dev: float = 1.75,
):
    hourly_probs = {}
    # Create normal distributions for entry and exit
    entry_distribution = norm(entry_peak_mean, entry_peak_std_dev)
    exit_distribution = norm(exit_peak_mean, exit_peak_std_dev)
    rush_flag = False
    min_prob = 0.1  # Minimum probability threshold

    for hour in np.arange(0, 24, 0.25):
        entry_prob = entry_distribution.pdf(hour)
        exit_prob = exit_distribution.pdf(hour)

        # Adjust probs based on time of Day
        if start <= hour < mid_day:
            # More Entries
            exit_prob *= 1.2
        elif mid_day <= hour < end_day:
            # More Exits
            entry_prob *= 1.2

        # Normalize Probabilities
        total = entry_prob + exit_prob
        if total > 0:
            entry_prob = max(entry_prob / total, min_prob)
            exit_prob = max(exit_prob / total, min_prob)

        hourly_probs[hour] = {
            "entry_prob": entry_prob,
            "exit_prob": exit_prob,
            "is_rush": start <= hour < mid_day or mid_day <= hour < end_day,
        }

    return hourly_probs


def adjust_probability_for_day_of_week(probability, day_of_week):
    if day_of_week in [0, 1, 2]:  # Monday, Tuesday, Wednesday
        return probability * 1.2  # Increase probability
    elif day_of_week in [3, 4]:  # Thursday, Friday
        return probability
    else:  # Weekend
        return probability * 0.5  # Decrease probability
    

def calculate_additional_search_time(occupancy_rate,searching_time_in_min):
    # Example: Add up to 5 additional minutes based on occupancy
    return min(searching_time_in_min * occupancy_rate, searching_time_in_min)
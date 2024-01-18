import csv
from datetime import datetime

from fastapi import UploadFile, HTTPException
from pydantic import ValidationError

from database.flights import insert_flight
from schemas.flight import flight_add_helper, FlightCreateSchema, fs_keys, fs_types

mfb_types = {
    "Tail Number": "aircraft",
    "Hold": "holds_instrument",
    "Landings": "landings_day",
    "FS Night Landings": "landings_night",
    "X-Country": "time_xc",
    "Night": "time_night",
    "Simulated Instrument": "time_sim_instrument",
    "Ground Simulator": "time_sim",
    "Dual Received": "dual_recvd",
    "SIC": "time_sic",
    "PIC": "time_pic",
    "Flying Time": "time_total",
    "Hobbs Start": "hobbs_start",
    "Hobbs End": "hobbs_end",
    "Engine Start": "time_start",
    "Engine End": "time_stop",
    "Flight Start": "time_off",
    "Flight End": "time_down",
    "Comments": "comments",
}


async def import_from_csv_mfb(file: UploadFile, user: str):
    content = await file.read()
    decoded_content = content.decode("utf-8").splitlines()
    decoded_content[0] = decoded_content[0].replace('\ufeff', '', 1)
    reader = csv.DictReader(decoded_content)
    flights = []
    for row in reader:
        entry = {}
        for label, value in dict(row).items():
            if len(value) and label in mfb_types:
                entry[mfb_types[label]] = value
            else:
                if label == "Date":
                    entry["date"] = datetime.strptime(value, "%Y-%m-%d")
                elif label == "Route":
                    r = str(value).split(" ")
                    l = len(r)
                    route = ""
                    start = ""
                    end = ""
                    if l == 1:
                        start = r[0]
                    elif l >= 2:
                        start = r[0]
                        end = r[-1]
                        route = " ".join(r[1:-1])
                    entry["route"] = route
                    entry["waypoint_from"] = start
                    entry["waypoint_to"] = end
        flights.append(entry)
    # print(flights)
    for entry in flights:
        # try:
        await insert_flight(FlightCreateSchema(**entry), user)
        # except ValidationError as e:
        #     raise HTTPException(400, e.json())

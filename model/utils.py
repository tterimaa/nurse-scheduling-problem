from typing import Dict


def get_hours(day: Dict):
    hours = day.get("hours")
    if not isinstance(hours, int):
        raise Exception("An hour has a None value " + str(day))
    return hours

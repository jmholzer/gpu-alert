from datetime import datetime


def generate_time_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

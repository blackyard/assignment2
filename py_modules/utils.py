from datetime import datetime


def get_current_datetime():
    """Return current datetime string in ISO format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

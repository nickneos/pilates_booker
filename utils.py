from datetime import datetime, timedelta, date, time
from tempfile import NamedTemporaryFile
import shutil
import csv
import logging

# initialise logging
logger = logging.getLogger(__name__)


def convert_booking_date_str(str_date):
    """Convert date strings from website to datetime"""

    dt = datetime.strptime(str_date, "%a. %b %d, %Y %I:%M %p")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_bookings_data(csv_file="bookings.csv"):
    """Read bookings csv and return data as list of dicts"""
    rows = []
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def get_wishlist(days_in_advance=2):
    """Return a list of timeslots wanted that fall within the `days_in_advance` window"""

    bookings = get_bookings_data()
    date_filter = datetime.combine(
        date.today() + timedelta(days=days_in_advance + 1), time()
    )

    date_gt = datetime.now() + timedelta(hours=6)

    return [
        b.get("datetime")
        for b in bookings
        if b.get("status").lower().strip() not in ("booked", "waitlisted")
        and datetime.strptime(b.get("datetime"), "%Y-%m-%d %H:%M:%S") < date_filter
        and datetime.strptime(b.get("datetime"), "%Y-%m-%d %H:%M:%S") >= date_gt
    ]


def update_record(dt_str, status, csv_file="bookings.csv"):
    """Update an existing record in the bookings csv"""

    fields = ["datetime", "status"]
    tempfile = NamedTemporaryFile(mode="w", delete=False)

    with open(csv_file, "r") as csvfile, tempfile:
        reader = csv.DictReader(csvfile, fieldnames=fields)
        writer = csv.DictWriter(tempfile, fieldnames=fields)

        for row in reader:
            if row["datetime"] == dt_str:
                row["status"] = status

            row = {"datetime": row["datetime"], "status": row["status"]}
            writer.writerow(row)

    shutil.move(tempfile.name, csv_file)
    logger.info(f"updated record in {csv_file}: {dt_str} -> '{status}'")


def insert_records(timeslots, status="", csv_file="bookings.csv"):
    """Insert timeslots into the bookings csv"""

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if row[0] in timeslots:
                timeslots.remove(row[0])

    counter = 0
    with open(csv_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for timeslot in timeslots:
            writer.writerow([timeslot, status])
            counter += 1
    logger.info(f"inserted {counter} records to {csv_file}")


def list_of_dates(n=180):
    """Return a list of sequential dates for `n` days from today"""

    today = date.today()
    return [today + timedelta(days=x) for x in range(n)]


def generate_timeslots(timeslot, days=180, *args):
    """Add timeslots to bookings csv based on the provided
    `timeslot` for days of week provided by `*args`

    Args:
        timeslot (str):  timeslot as a string in `HH:MM` format. eg "06:30"
        *args (str): Variable length argument list of days of week eg. ("Mon", "Sat", "Sun").
    """

    dates = list_of_dates(days)
    t = datetime.time(datetime.strptime(timeslot, "%H:%M"))
    timeslots = []

    for d in dates:
        for dow in args:
            if dow.lower().strip() == d.strftime("%a").lower():
                timeslots.append(datetime.combine(d, t).strftime("%Y-%m-%d %H:%M:%S"))

    return timeslots


if __name__ == "__main__":
    # print(get_wishlist())
    d = ("Thu",)
    insert_records(generate_timeslots("6:30", 365, *d))
    # x = get_wishlist()
    # print(x)

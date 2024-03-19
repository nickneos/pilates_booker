from datetime import datetime,  timedelta, date, time
from tempfile import NamedTemporaryFile
import shutil
import csv
import logging

# initialise logging
logger = logging.getLogger(__name__)


def convert_booking_date_str(str_date):
    dt = datetime.strptime(str_date, "%a. %b %d, %Y %I:%M %p")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def read_csv(csv_file="bookings.csv"):
    rows = []
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def get_wishlist(days_in_advance=2):
    bookings = read_csv()
    date_filter = datetime.combine(date.today() + timedelta(days=days_in_advance+1), time())

    logger.info(f"Getting wishlist items within 2 days: ie. < {date_filter}")
    
    return [
        b.get("datetime")
        for b in bookings
        if b.get("status").lower().strip() != "booked" and 
            datetime.strptime(b.get("datetime"), "%Y-%m-%d %H:%M:%S") < date_filter
    ]


def update_record(dt_str, status, csv_file="bookings.csv"):
    fields = ['datetime', 'status']
    tempfile = NamedTemporaryFile(mode='w', delete=False)

    with open(csv_file, 'r') as csvfile, tempfile:
        reader = csv.DictReader(csvfile, fieldnames=fields)
        writer = csv.DictWriter(tempfile, fieldnames=fields)

        for row in reader:
            if row['datetime'] == dt_str:
                row['status'] = status
            
            row = {'datetime': row['datetime'], 'status': row['status']}
            writer.writerow(row)

    shutil.move(tempfile.name, csv_file)
    logger.info(f"updated record in {csv_file}: {dt_str} -> '{status}'")


# if __name__ == "__main__":
#     print(get_wishlist())

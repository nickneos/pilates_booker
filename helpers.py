from datetime import datetime
import csv


def extract_datetime(str_date):
    return datetime.strptime(str_date, "%a. %b %d, %Y %I:%M %p")


def read_csv(csv_file="bookings.csv"):
    rows = []
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def get_wishlist():
    bookings = read_csv()
    return [
        b.get("datetime")
        for b in bookings
        if b.get("status").lower().strip() != "booked"
    ]


if __name__ == "__main__":
    print(get_wishlist())

# Pilates Booker

## Overview

To keep the wife happy, I created this script to automatically book in pilates classes at her gym. Apparently it gets super competitive booking in classes which get released at 5am 2 days in advance (the popular classes usually book out within minutes).

I trigger this script at the required time via crontab.

## Setup

1. Create `settings.py` and add required details (use `settings.py.example` as a guide)
2. Create venv eg. `python3 -m venv .venv`
3. Activate venv and install requirements:
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

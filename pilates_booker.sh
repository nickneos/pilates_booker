#!/bin/bash

# Wrapper shell script to execute via cron

cd $HOME/projects/pilates_booker/
source .venv/bin/activate
python main.py

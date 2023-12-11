import serial
import time
from collections import deque
from datetime import datetime, timedelta

# Function to parse GPGSV and GLGSV sentences and update the satellite SNR dictionary
def parse_and_update_snr(sentence, satellite_snr):
    parts = sentence.split(',')
    sats_info = parts[4:-1]  # Satellite info in this message

    for i in range(0, len(sats_info), 4):
        if len(sats_info[i:i + 4]) == 4:
            prn, elevation, azimuth, snr = sats_info[i:i + 4]
            if snr.isdigit():  # Ensure SNR is a valid number
                satellite_snr[prn] = int(snr)

# Function to calculate the total reception score
def calculate_reception_score(satellite_snr):
    return sum(satellite_snr.values())

# Function to calculate min, max, and average for a list of scores
def calculate_stats(scores):
    if scores:
        return min(scores), max(scores), sum(scores) / len(scores)
    return 0, 0, 0

# Open serial port
try:
    ser = serial.Serial('COM8', 9600, timeout=1)
    print("Serial port COM8 opened at 9600 bps")
except serial.SerialException:
    print("Failed to open serial port COM8")
    exit(1)

# Dictionary to hold satellite SNR values and deque for historical scores
satellite_snr = {}
historical_scores = deque()

# Read from the serial port and parse data
try:
    while True:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if line.startswith(('$GPGSV', '$GLGSV')):
            parse_and_update_snr(line, satellite_snr)
            score = calculate_reception_score(satellite_snr)
            historical_scores.append((datetime.now(), score))

            # Removing old scores
            while historical_scores and historical_scores[0][0] < datetime.now() - timedelta(days=1):
                historical_scores.popleft()

            # Calculating statistics
            scores_last_minute = [score for time, score in historical_scores if time > datetime.now() - timedelta(minutes=1)]
            scores_last_hour = [score for time, score in historical_scores if time > datetime.now() - timedelta(hours=1)]
            scores_last_24_hours = [score for _, score in historical_scores]

            min_last_minute, max_last_minute, avg_last_minute = calculate_stats(scores_last_minute)
            min_last_hour, max_last_hour, avg_last_hour = calculate_stats(scores_last_hour)
            min_last_24_hours, max_last_24_hours, avg_last_24_hours = calculate_stats(scores_last_24_hours)

            print(f"Current Score: {score} | "
                  f"Last Minute (Min: {min_last_minute}, Max: {max_last_minute}, Avg: {avg_last_minute:.2f}) | "
                  f"Last Hour (Min: {min_last_hour}, Max: {max_last_hour}, Avg: {avg_last_hour:.2f}) | Last 24 Hours (Min: {min_last_24_hours}, Max: {max_last_24_hours}, Avg: {avg_last_24_hours:.2f})")
except KeyboardInterrupt:
    print("Program terminated by user")
finally:
    ser.close()
    print("Serial port closed")

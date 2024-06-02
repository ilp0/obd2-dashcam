import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import argparse

# Set up command line argument parsing
parser = argparse.ArgumentParser(description='Embed information as text in an MP4 video.')
parser.add_argument('csv_file', type=str, help='Path to the CSV file containing the data.')
parser.add_argument('fps', type=int, help='Frames per second of the video.')
args = parser.parse_args()

# Read the CSV file
csv_file = args.csv_file
fps = args.fps
frame_duration_ms = 1000 / fps
data = pd.read_csv(csv_file)

# Function to convert CSV time format to total milliseconds
def time_to_ms(time_str):
    h, m, s, ms = map(int, time_str.split('.'))
    return (h * 3600 + m * 60 + s) * 1000 + ms

# Function to convert total milliseconds to ASS time format with two decimal places for milliseconds
def ms_to_ass_time(total_ms):
    total_seconds = total_ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int(total_seconds * 100 % 100)
    return f"{hours:01}:{minutes:02}:{seconds:02}.{milliseconds:02}"

# Calculate the start and end times
data['time_ms'] = data['time'].apply(time_to_ms)
data['start_time'] = data['time_ms'] - data['time_ms'].iloc[0]

# Fill NaN values to avoid issues with interpolation
data['Vehicle speed (km/h)'].fillna(method='ffill', inplace=True)
data['Engine RPM (rpm)'].fillna(method='ffill', inplace=True)
data['Calculated boost (bar)'].fillna(method='ffill', inplace=True)

# Ensure no NaNs in the first row after fill
data['Vehicle speed (km/h)'].fillna(0, inplace=True)
data['Engine RPM (rpm)'].fillna(0, inplace=True)
data['Calculated boost (bar)'].fillna(0, inplace=True)

# Generate the interpolated data
interpolated_times = np.arange(data['start_time'].iloc[0], data['start_time'].iloc[-1], frame_duration_ms)

# Interpolate using interp1d for better control
interp_speed = interp1d(data['start_time'], data['Vehicle speed (km/h)'], kind='linear', fill_value="extrapolate")
interp_rpm = interp1d(data['start_time'], data['Engine RPM (rpm)'], kind='linear', fill_value="extrapolate")
interp_boost = interp1d(data['start_time'], data['Calculated boost (bar)'], kind='linear', fill_value="extrapolate")

interpolated_data = pd.DataFrame({
    'time_ms': interpolated_times,
    'Vehicle speed (km/h)': interp_speed(interpolated_times),
    'Engine RPM (rpm)': interp_rpm(interpolated_times),
    'Calculated boost (bar)': interp_boost(interpolated_times)
})

# Create ASS file content
ass_content = """
[Script Info]
Title: Video with embedded information
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0.00,1,1,0,1,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Iterate through the interpolated data and create ASS dialogues
for i in range(len(interpolated_data) - 1):
    start_time = ms_to_ass_time(interpolated_data.iloc[i]['time_ms'])
    end_time = ms_to_ass_time(interpolated_data.iloc[i + 1]['time_ms'])
    
    speed = f"{int(interpolated_data.iloc[i]['Vehicle speed (km/h)']):03d}"
    rpm = f"{int(interpolated_data.iloc[i]['Engine RPM (rpm)']):04d}"
    boost = f"{float(interpolated_data.iloc[i]['Calculated boost (bar)']):.2f}"
    
    text = (f"Vehicle Speed: {speed} km/h\\N"
            f"Engine RPM: {rpm} rpm\\N"
            f"Calculated boost: {boost} bar")
    
    # Append the dialogue entry to the ASS content
    ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"

# Write the ASS content to a file
with open('output.ass', 'w') as f:
    f.write(ass_content)


import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import moviepy.editor as mpy
from datetime import datetime
import os
from matplotlib.font_manager import FontProperties
from scipy.interpolate import interp1d
import concurrent.futures

# Set the backend to 'Agg' to avoid issues with threading and Tkinter
plt.switch_backend('Agg')

# Check if file path is provided as an argument
if len(sys.argv) < 2:
    print("Please provide the CSV file path as an argument.")
    sys.exit(1)

# Load the provided CSV file path
file_path = sys.argv[1]

# Load the custom font
font_path = "gauge_font.ttf"
prop = FontProperties(fname=font_path)

# Function to convert time to seconds since start
def convert_time_to_seconds(time_str, start_time):
    time_format = "%H.%M.%S.%f"
    time_obj = datetime.strptime(time_str, time_format)
    start_time_obj = datetime.strptime(start_time, time_format)
    time_delta = time_obj - start_time_obj
    return time_delta.total_seconds()

# Load the data
data = pd.read_csv(file_path)

# Parse the time column to seconds
start_time = data['time'].iloc[0]
data['time_seconds'] = data['time'].apply(lambda x: convert_time_to_seconds(x, start_time))

# Interpolation for Altitude (GPS)
time_values = data['time_seconds'].values
altitude_values = data['Altitude (GPS) (m)'].values
interp_altitude = interp1d(time_values, altitude_values, kind='linear', fill_value="extrapolate")

# Function to create a simple gauge image with altitude
def create_simple_gauge(altitude):
    fig, ax = plt.subplots(figsize=(2, 1), facecolor='green')
    ax.axis('off')
    
    # Add altitude text
    ax.text(0.5, 0.5, f'ELEV {altitude:04.0f}m', ha='center', va='center', fontsize=28, fontweight='bold', fontproperties=prop, color='black')

    fig.set_size_inches(4, 1)
    fig.canvas.draw()
    image = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
    image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    plt.close(fig)
    return image

# Function to save a frame with altitude
def save_frame_altitude(i, fps, interp_altitude):
    current_time = i / fps
    altitude = interp_altitude(current_time)
    frame = create_simple_gauge(altitude)
    frame_filename = os.path.join("frames_altitude", f"frame_{i}.png")
    plt.imsave(frame_filename, frame)
    return frame_filename

def main():
    # Create 'frames_altitude' directory if it doesn't exist
    if not os.path.exists("frames_altitude"):
        os.makedirs("frames_altitude")

    # Initialize variables
    frames = []
    fps = 20
    duration = data['time_seconds'].iloc[-1]
    total_frames = int(fps * duration)

    # Generate frames sequentially
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        for i, frame_filename in enumerate(executor.map(save_frame_altitude, range(total_frames), [fps]*total_frames, [interp_altitude]*total_frames)):
            frames.append(frame_filename)

    # Create video from frames at 30 fps
    clip = mpy.ImageSequenceClip(frames, fps=fps)
    output_file = "altitude_counter_30fps.mp4"
    clip.write_videofile(output_file, codec='libx264')

    # Clean up frame files
    for frame_filename in frames:
        os.remove(frame_filename)

    print(f"Video saved as {output_file}")

if __name__ == '__main__':
    main()

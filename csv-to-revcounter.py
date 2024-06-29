import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import moviepy.editor as mpy
from datetime import datetime
import os
from matplotlib.font_manager import FontProperties
from scipy.interpolate import interp1d

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

# Interpolation
time_values = data['time_seconds'].values
rpm_values = data['Engine RPM (rpm)'].values
speed_values = data['Speed (GPS) (km/h)'].values
interp_rpm = interp1d(time_values, rpm_values, kind='linear', fill_value="extrapolate")
interp_speed = interp1d(time_values, speed_values, kind='linear', fill_value="extrapolate")

# Function to create a modern gauge image
def create_modern_gauge(rpm, speed, max_rpm=7000, redline_rpm=6000):
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={'aspect': 'equal'}, facecolor='green')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('off')

    # Draw the gauge background
    circle = plt.Circle((0, 0), 1, color='white', ec='black', lw=5)

    ax.add_patch(circle)

    # Draw the gauge ticks
    num_subticks = 3
    num_ticks = 8

    tick_angles = np.linspace(5 * np.pi / 4, -np.pi / 4, num_ticks)
    subtick_angles = []

    # Generate subtick angles based on main tick angles
    for i in range(len(tick_angles) - 1):
        subtick_angles.extend(np.linspace(tick_angles[i], tick_angles[i+1], num_subticks+2)[1:-1])

    # Draw the subticks
    for angle in subtick_angles:
        x0, y0 = np.cos(angle), np.sin(angle)
        x1, y1 = 0.95 * x0, 0.95 * y0
        ax.plot([x0, x1], [y0, y1], color='black', lw=1)

    # Draw the main ticks
    tick_labels = range(0, max_rpm + 1000, 1000)
    for i, angle in enumerate(tick_angles):
        x0, y0 = np.cos(angle), np.sin(angle)
        x1, y1 = 0.9 * x0, 0.9 * y0
        ax.plot([x0, x1], [y0, y1], color='black', lw=3)
        ax.text(0.7 * x0, 0.7 * y0, f'{int(tick_labels[i]/1000)}' + 'K', ha='center', va='center', fontweight='bold', fontsize=12, fontproperties=prop, color='black')
    
    # Draw the redline area
    redline_start_angle = (5 * np.pi / 4) - (redline_rpm / max_rpm) * (3 * np.pi / 2)
    redline_end_angle = -np.pi / 4
    # Draw the redline ticks
    redline_subtick_angles = np.linspace(redline_start_angle, redline_end_angle, 20)
    for angle in redline_subtick_angles:
        x0, y0 = np.cos(angle), np.sin(angle)
        x1, y1 = 0.8 * x0, 0.8 * y0
        ax.plot([x0, x1], [y0, y1], color='red', lw=1)

    # Draw the needle
    needle_angle = (5 * np.pi / 4) - (rpm / max_rpm) * (3 * np.pi / 2)
    needle_length = 0.9
    base_angle = 0.1  # small angle for the base of the needle

    # Define the four points of the polygon
    x_points = [0.2 * np.cos(needle_angle - base_angle), needle_length * np.cos(needle_angle), 0.2 * np.cos(needle_angle + base_angle), 0]
    y_points = [0.2 * np.sin(needle_angle - base_angle), needle_length * np.sin(needle_angle), 0.2 * np.sin(needle_angle + base_angle), 0]

    # Draw the polygon
    ax.fill(x_points, y_points, color='orange')

    # Add RPM text in the middle, a bit down
    ax.text(0, -0.8, f'{rpm:.0f} RPM', ha='center', va='center', fontsize=17, fontweight='bold', fontproperties=prop, color='black')

    # Add speed text on the right side
    speed_text = f'{speed:03.0f} km/h'
    ax.text(1.7, -0.8, speed_text, ha='center', va='center', fontsize=28, fontweight='bold', fontproperties=prop, color='black')

    fig.set_size_inches(8, 5.5)
    # Convert plot to image
    fig.canvas.draw()
    image = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
    image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    plt.close(fig)
    return image

import concurrent.futures

# Function to save a frame
def save_frame(i, fps, interp_rpm, interp_speed):
    current_time = i / fps
    rpm = interp_rpm(current_time)
    speed = interp_speed(current_time)
    frame = create_modern_gauge(rpm, speed)
    frame_filename = os.path.join("frames", f"frame_{i}.png")
    plt.imsave(frame_filename, frame)
    return frame_filename

def main():
    # Create 'frames' directory if it doesn't exist
    if not os.path.exists("frames"):
        os.makedirs("frames")

    # Initialize variables
    frames = []
    fps = 20
    duration = data['time_seconds'].iloc[-1]
    total_frames = int(fps * duration)

    # Generate frames sequentially
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        for i, frame_filename in enumerate(executor.map(save_frame, range(total_frames), [fps]*total_frames, [interp_rpm]*total_frames, [interp_speed]*total_frames)):
            frames.append(frame_filename)

    # Create video from frames at 30 fps
    clip = mpy.ImageSequenceClip(frames, fps=fps)
    output_file = "rpm_counter_modern_30fps.mp4"
    clip.write_videofile(output_file, codec='libx264')

    # Clean up frame files
    for frame_filename in frames:
        os.remove(frame_filename)

    print(f"Video saved as {output_file}")

if __name__ == '__main__':
    main()



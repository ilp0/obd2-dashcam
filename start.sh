#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <csv-file> <mp4-file> <fps>"
  exit 1
fi

# Assign command line arguments to variables
CSV_FILE=$1
MP4_FILE=$2
FPS=$3

# Step 1: Interpolate missing values in the CSV file
echo "Interpolating missing values in the CSV file..."
python3 ./interpolate_csv_values.py "$CSV_FILE"
if [ $? -ne 0 ]; then
  echo "Error: Failed to interpolate CSV values."
  exit 1
fi

# Step 2: Convert interpolated CSV to ASS subtitle format
echo "Converting CSV to ASS subtitle format..."
python3 ./csv-to-ass.py interpolated_file.csv "$FPS"
if [ $? -ne 0 ]; then
  echo "Error: Failed to convert CSV to ASS."
  exit 1
fi

# Step 3: Overlay ASS subtitles onto the MP4 video using FFmpeg
echo "Overlaying ASS subtitles onto the MP4 video..."
ffmpeg -i "$MP4_FILE" -vf "ass=output.ass" -c:a copy output.mp4
if [ $? -ne 0 ]; then
  echo "Error: Failed to overlay ASS subtitles onto the video."
  exit 1
fi

rm interpolated_file.csv
rm output.ass

echo "Process completed successfully. The output video is saved as output.mp4"

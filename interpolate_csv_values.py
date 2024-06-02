import pandas as pd
import argparse

def interpolate_csv(file_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Display the DataFrame before interpolation
    print("DataFrame before interpolation:")
    print(df)

    # Interpolate missing values
    df_interpolated = df.interpolate(method='linear', axis=0, limit_direction='both')

    # Display the DataFrame after interpolation
    print("\nDataFrame after interpolation:")
    print(df_interpolated)

    # Save the interpolated DataFrame to a new CSV file
    output_path = 'interpolated_file.csv'
    df_interpolated.to_csv(output_path, index=False)
    print(f"\nInterpolated data saved to {output_path}")

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Interpolate missing values in a CSV file.')
    parser.add_argument('file_path', type=str, help='Path to the input CSV file')
    
    args = parser.parse_args()
    
    # Call the interpolate function with the provided file path
    interpolate_csv(args.file_path)


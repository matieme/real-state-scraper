import pandas as pd
import os

folder_path = 'results/'


def merge_files():
    all_files = [f for f in os.listdir(folder_path) if
                 os.path.isfile(os.path.join(folder_path, f)) and f.startswith('scraped_')]
    dfs = []  # List to store DataFrames
    for filename in all_files:
        filepath = os.path.join(folder_path, filename)
        df = pd.read_csv(filepath)
        dfs.append(df)

    # Concatenate all data into one DataFrame
    merged_df = pd.concat(dfs, ignore_index=True)

    # Save to a single file
    merged_df.to_csv(os.path.join(folder_path, "all_scraped_data.csv"), index=False)

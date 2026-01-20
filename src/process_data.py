import glob
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Set global style
plt.style.use("seaborn-v0_8-whitegrid")
sns.set_palette("viridis")

DATA_DIR = "datasets"
OUTPUT_DIR = "analysis_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_and_merge(folder_name, date_col="date"):
    """Loads all CSVs from a folder and merges them."""
    path = os.path.join(DATA_DIR, folder_name)
    all_files = glob.glob(os.path.join(path, "*.csv"))

    if not all_files:
        print(f"Warning: No files found in {path}")
        return pd.DataFrame()

    df_list = []
    for filename in all_files:
        try:
            df = pd.read_csv(filename)
            df_list.append(df)
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    if not df_list:
        return pd.DataFrame()

    full_df = pd.concat(df_list, ignore_index=True)

    # Standardize Column Names
    full_df.columns = [c.lower().strip() for c in full_df.columns]

    # Date Conversion
    if date_col in full_df.columns:
        full_df[date_col] = pd.to_datetime(
            full_df[date_col], format="%d-%m-%Y", errors="coerce"
        )

    return full_df


def process_data():
    print("Loading datasets...")

    # 1. Load Data
    enrol_df = load_and_merge("api_data_aadhar_enrolment")
    demo_df = load_and_merge("api_data_aadhar_demographic")
    bio_df = load_and_merge("api_data_aadhar_biometric")

    print(f"Enrolment Shape: {enrol_df.shape}")
    print(f"Demographic Shape: {demo_df.shape}")
    print(f"Biometric Shape: {bio_df.shape}")

    # 2. Aggregation by State/District (summing up all time periods)
    # We want to find 'Hotspots', so we look at total volume first.

    # Enrolment Total
    e_cols = ["age_0_5", "age_5_17", "age_18_greater"]
    # Check if columns exist (handle potential naming variations)
    e_cols = [c for c in e_cols if c in enrol_df.columns]
    if not e_cols:
        print("Error: Enrolment columns not found")
        return

    enrol_df["total_enrolment"] = enrol_df[e_cols].sum(axis=1)
    e_grouped = (
        enrol_df.groupby(["state", "district"])["total_enrolment"].sum().reset_index()
    )

    # Demographic Total
    d_cols = ["demo_age_5_17", "demo_age_17_"]  # Based on file read earlier
    d_cols = [c for c in d_cols if c in demo_df.columns]
    # If standard columns fail, try to find any numeric columns excluding key ones
    if not d_cols:
        # Fallback logic if needed, but assuming standard format based on earlier read
        pass

    demo_df["total_demo_updates"] = demo_df[d_cols].sum(axis=1)
    d_grouped = (
        demo_df.groupby(["state", "district"])["total_demo_updates"].sum().reset_index()
    )

    # Biometric Total
    b_cols = ["bio_age_5_17", "bio_age_17_"]
    b_cols = [c for c in b_cols if c in bio_df.columns]

    bio_df["total_bio_updates"] = bio_df[b_cols].sum(axis=1)
    b_grouped = (
        bio_df.groupby(["state", "district"])["total_bio_updates"].sum().reset_index()
    )

    # 3. Merge into Master DataFrame
    master_df = pd.merge(e_grouped, d_grouped, on=["state", "district"], how="outer")
    master_df = pd.merge(master_df, b_grouped, on=["state", "district"], how="outer")

    master_df.fillna(0, inplace=True)

    # 4. Calculate UER (Update-to-Enrolment Ratio)
    # Adding a small epsilon to avoid division by zero
    master_df["UER"] = (
        master_df["total_demo_updates"] + master_df["total_bio_updates"]
    ) / (master_df["total_enrolment"] + 1)

    # 5. Classify Clusters
    def classify(row):
        # Increased threshold to 15.0 to identify only TRUE hubs (not just active centers)
        if row["UER"] > 15.0 and row["total_demo_updates"] > 3000:
            return "Migrant Hub"
        elif row["total_bio_updates"] > row["total_demo_updates"] * 1.5:
            return "Biometric Stress Zone"
        elif row["UER"] < 1.0 and row["total_enrolment"] > 1000:
            return "Growth Zone"
        else:
            return "Standard"

    master_df["Cluster"] = master_df.apply(classify, axis=1)

    # Save processed data
    master_df.to_csv(os.path.join(OUTPUT_DIR, "district_clusters.csv"), index=False)
    print("Data processed and saved to district_clusters.csv")

    return master_df


if __name__ == "__main__":
    process_data()

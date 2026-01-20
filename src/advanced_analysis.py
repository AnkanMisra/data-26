import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# --- GLOBAL AESTHETICS CONFIGURATION ---
# Set the context to 'talk' for larger, readable fonts (good for papers/slides)
sns.set_context("talk")
# Use a clean, white style
sns.set_style("whitegrid")
# Custom Color Palette (Professional/Academic)
CUSTOM_PALETTE = ["#E74C3C", "#F39C12", "#2ECC71", "#3498DB", "#9B59B6"]

DATA_DIR = "datasets"
OUTPUT_DIR = "analysis_results"
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)


def save_plot(filename):
    """Saves the current plot in both PNG (High DPI) and SVG (Vector) formats."""
    # Save as Ultra-High DPI PNG
    plt.savefig(
        os.path.join(PLOTS_DIR, f"{filename}.png"), dpi=600, bbox_inches="tight"
    )
    # Save as Vector SVG (Infinite Crispness)
    plt.savefig(os.path.join(PLOTS_DIR, f"{filename}.svg"), bbox_inches="tight")
    print(f"Saved {filename} (.png and .svg)")


def load_and_merge(folder_name, date_col="date"):
    """Loads all CSVs from a folder and merges them."""
    path = os.path.join(DATA_DIR, folder_name)
    all_files = glob.glob(os.path.join(path, "*.csv"))

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
    full_df.columns = [c.lower().strip() for c in full_df.columns]

    if date_col in full_df.columns:
        full_df[date_col] = pd.to_datetime(
            full_df[date_col], format="%d-%m-%Y", errors="coerce"
        )

    return full_df


def run_advanced_analysis():
    print("Loading datasets for Advanced Analysis...")
    enrol_df = load_and_merge("api_data_aadhar_enrolment")
    demo_df = load_and_merge("api_data_aadhar_demographic")
    bio_df = load_and_merge("api_data_aadhar_biometric")

    # --- 1. PINCODE LEVEL ANALYSIS ---
    print("Performing Pincode-level Aggregation...")

    def get_sum(df, cols, name):
        valid_cols = [c for c in cols if c in df.columns]
        if not valid_cols:
            return None
        df[name] = df[valid_cols].sum(axis=1)
        return df.groupby(["state", "district", "pincode"])[name].sum().reset_index()

    e_pin = get_sum(
        enrol_df, ["age_0_5", "age_5_17", "age_18_greater"], "enrolment_vol"
    )
    d_pin = get_sum(demo_df, ["demo_age_5_17", "demo_age_17_"], "demo_vol")
    b_pin = get_sum(bio_df, ["bio_age_5_17", "bio_age_17_"], "bio_vol")

    # Merge
    pin_df = pd.merge(e_pin, d_pin, on=["state", "district", "pincode"], how="outer")
    pin_df = pd.merge(pin_df, b_pin, on=["state", "district", "pincode"], how="outer")
    pin_df.fillna(0, inplace=True)

    # Metric Calculation
    # Add epsilon to avoid division by zero
    pin_df["UER"] = (pin_df["demo_vol"] + pin_df["bio_vol"]) / (
        pin_df["enrolment_vol"] + 1
    )

    # --- 2. UNSUPERVISED ML: K-MEANS TUNING ---
    print("Running K-Means Clustering with Validation...")

    features = ["enrolment_vol", "demo_vol", "bio_vol", "UER"]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(pin_df[features])

    # Validate Cluster Count (Silhouette Score)
    best_score = -1
    best_k = 4  # Default
    best_model = None

    print(f"{'K':<5} | {'Silhouette Score':<20}")
    print("-" * 30)

    for k in range(3, 7):  # Test k=3, 4, 5, 6
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)

        # Calculate score (using a sample for speed if dataset is huge, but here it's fine)
        # Limiting sample size for performance if needed
        sample_size = min(10000, len(X_scaled))
        score = silhouette_score(X_scaled, labels, sample_size=sample_size)

        print(f"{k:<5} | {score:.4f}")

        if score > best_score:
            best_score = score
            best_k = k
            best_model = model

    print("-" * 30)
    print(f"Optimal Number of Clusters found: k={best_k} (Score: {best_score:.4f})")

    # Apply Best Model
    pin_df["ML_Cluster"] = best_model.fit_predict(X_scaled)

    # --- 3. CLUSTER PROFILING (Integrity Check) ---
    print("\n--- Cluster Integrity Profile ---")
    profile = pin_df.groupby("ML_Cluster")[["enrolment_vol", "demo_vol", "UER"]].mean()
    print(profile)

    # Save Pincode Data
    pin_df.to_csv(os.path.join(OUTPUT_DIR, "pincode_ml_clusters.csv"), index=False)

    # Visualize Clusters
    plt.figure(figsize=(12, 10))
    sns.scatterplot(
        data=pin_df,
        x="enrolment_vol",
        y="demo_vol",
        hue="ML_Cluster",
        palette="rocket",  # High contrast
        alpha=0.7,
        s=100,
        edgecolor="w",
        linewidth=0.5,
    )
    plt.title(
        f"K-Means Segmentation (k={best_k})", fontweight="bold", pad=20, fontsize=20
    )
    plt.xlabel("Enrolment Volume (Log Scale)", fontweight="bold")
    plt.ylabel("Demographic Update Volume (Log Scale)", fontweight="bold")
    plt.xscale("log")
    plt.yscale("log")
    sns.despine()

    # Move legend to bottom
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)

    plt.tight_layout()
    save_plot("ml_cluster_scatter")
    plt.close()

    # --- 4. ANOMALY DETECTION (ISOLATION FOREST) ---
    print("\nRunning Anomaly Detection...")

    iso = IsolationForest(contamination=0.01, random_state=42)
    pin_df["anomaly_score"] = iso.fit_predict(pin_df[["UER", "demo_vol"]])

    anomalies = pin_df[pin_df["anomaly_score"] == -1]
    anomalies.to_csv(os.path.join(OUTPUT_DIR, "detected_anomalies.csv"), index=False)

    print(f"Detected {len(anomalies)} anomalous pincodes.")

    # Plot Anomalies
    plt.figure(figsize=(12, 8))
    # Plot Normal Points
    sns.scatterplot(
        data=pin_df[pin_df["anomaly_score"] == 1],
        x="enrolment_vol",
        y="demo_vol",
        alpha=0.3,
        color="#bdc3c7",  # Gray
        label="Normal Operations",
        s=50,
        edgecolor="none",
    )
    # Plot Anomalies
    sns.scatterplot(
        data=anomalies,
        x="enrolment_vol",
        y="demo_vol",
        color="#c0392b",  # Dark Red
        label="Detected Anomaly",
        s=100,
        edgecolor="w",
        linewidth=1.0,
        marker="X",  # Distinct Marker
    )
    plt.title("Anomaly Detection: Suspicious Activity", fontweight="bold", pad=20)
    plt.xlabel("Enrolment Volume")
    plt.ylabel("Update Volume")
    plt.xscale("log")
    plt.yscale("log")
    sns.despine()

    # Move legend to bottom
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)

    plt.tight_layout()
    save_plot("anomalies_scatter")
    plt.close()

    # --- 5. FORECASTING (Simple Seasonality) ---
    print("\nRunning Biometric Demand Forecasting...")

    if "date" in bio_df.columns:
        bio_daily = (
            bio_df.groupby("date")[["bio_age_5_17", "bio_age_17_"]].sum().sum(axis=1)
        )

        if not bio_daily.empty:
            # Save Forecast Data for external plotting
            bio_daily.to_csv(os.path.join(OUTPUT_DIR, "biometric_daily_trend.csv"))

            plt.figure(figsize=(14, 7))

            # Plot Actuals
            bio_daily.plot(label="Actual Daily Updates", color="#3498db", alpha=0.3)

            # Rolling Mean
            rolling_mean = bio_daily.rolling(window=7).mean()
            rolling_mean.plot(label="7-Day Trend", color="#e74c3c", linewidth=3.0)

            # Simple Threshold for Capacity
            capacity_threshold = rolling_mean.mean() * 1.5
            plt.axhline(
                y=capacity_threshold,
                color="#2ecc71",
                linestyle="--",
                linewidth=2,
                label="System Capacity Threshold",
            )

            plt.title(
                "Predictive Analytics: Biometric Update Surges",
                fontweight="bold",
                pad=20,
            )
            plt.ylabel("Daily Transaction Volume", fontweight="bold")
            plt.xlabel("Timeline", fontweight="bold")

            # Move legend to bottom
            plt.legend(
                loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False
            )

            sns.despine(left=True)
            plt.grid(axis="y", alpha=0.3)
            plt.tight_layout()
            save_plot("biometric_forecast_trend")
            plt.close()

    print("Advanced Analysis Complete.")


if __name__ == "__main__":
    run_advanced_analysis()

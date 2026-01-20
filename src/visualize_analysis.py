import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# --- GLOBAL AESTHETICS CONFIGURATION ---
# Set the context to 'talk' for larger, readable fonts (good for papers/slides)
sns.set_context("talk")
# Use a clean, white style
sns.set_style("whitegrid")
# Custom Color Palette (Professional/Academic)
CUSTOM_PALETTE = {
    "Migrant Hub": "#E74C3C",  # Urgent Red
    "Biometric Stress Zone": "#F39C12",  # Warning Orange
    "Growth Zone": "#2ECC71",  # Growth Green
    "Standard": "#3498DB",  # Neutral Blue
    "Dormant": "#95A5A6",  # Gray
}

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


def load_processed_data():
    file_path = os.path.join(OUTPUT_DIR, "district_clusters.csv")
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found. Please run process_data.py first.")
        return pd.DataFrame()
    return pd.read_csv(file_path)


def generate_visuals(df):
    print("Generating High-Quality Visualizations (600 DPI + SVG)...")

    if df.empty:
        return

    # 1. State-wise Average UER (The "Heatmap" proxy)
    state_uer = df.groupby("state")["UER"].mean().sort_values(ascending=False).head(15)

    plt.figure(figsize=(14, 9))
    ax = sns.barplot(
        x=state_uer.values,
        y=state_uer.index,
        palette="rocket",  # High contrast palette
        edgecolor="black",
        linewidth=0.5,
    )

    plt.title(
        "Top 15 States by Migration Pressure (Avg UER)", fontweight="bold", pad=20
    )
    plt.xlabel("Average Update-to-Enrolment Ratio")
    plt.ylabel("")
    sns.despine(left=True, bottom=True)  # Remove borders for clean look
    plt.grid(axis="x", alpha=0.3)  # Subtle grid
    plt.tight_layout()
    save_plot("state_uer_heatmap")
    plt.close()

    # 2. The "Scatter of Truth" (Updates vs Enrolment)
    plt.figure(figsize=(14, 10))

    # Main Scatter Plot
    sns.scatterplot(
        data=df,
        x="total_enrolment",
        y="total_demo_updates",
        hue="Cluster",
        style="Cluster",
        palette=CUSTOM_PALETTE,  # Use our custom colors
        s=150,  # Larger dots
        alpha=0.7,  # Transparency
        edgecolor="white",
        linewidth=0.8,
    )

    # Annotate Top 3 Migrant Hubs (Reduced to prevent clutter)
    top_hubs = (
        df[df["Cluster"] == "Migrant Hub"]
        .sort_values("total_demo_updates", ascending=False)
        .head(3)
    )

    # Smart Offsets to prevent text overlapping dots
    offsets = [(1000, 2000), (500, -3000), (200, 4000)]

    for i in range(top_hubs.shape[0]):
        x = top_hubs.total_enrolment.iloc[i]
        y = top_hubs.total_demo_updates.iloc[i]
        label = top_hubs.district.iloc[i]

        x_off, y_off = offsets[i] if i < len(offsets) else (0, 1000)

        plt.text(
            x + x_off,
            y + y_off,
            label,
            horizontalalignment="left",
            size="small",
            color="#333333",
            weight="bold",
            bbox=dict(
                facecolor="white",
                alpha=0.8,
                edgecolor="#cccccc",
                boxstyle="round,pad=0.3",
            ),
        )

    plt.title(
        "The Scatter of Truth: Identifying Migrant Hubs", fontweight="bold", pad=20
    )
    plt.xlabel("Total New Enrolments (Log Scale)", fontweight="bold")
    plt.ylabel("Total Demographic Updates (Log Scale)", fontweight="bold")
    plt.xscale("log")
    plt.yscale("log")

    # Legend at BOTTOM to prevent cutoff
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4, frameon=False)

    plt.grid(True, which="major", ls="-", alpha=0.2)
    sns.despine()

    # Ensure tight layout accommodates the bottom legend
    plt.tight_layout()
    save_plot("scatter_of_truth")
    plt.close()

    # 3. Top 10 Migrant Hubs (Bar Chart)
    migrant_hubs = (
        df[df["Cluster"] == "Migrant Hub"].sort_values("UER", ascending=False).head(10)
    )

    if not migrant_hubs.empty:
        plt.figure(figsize=(14, 8))
        sns.barplot(
            x="UER",
            y="district",
            data=migrant_hubs,
            hue="state",  # Color by State
            dodge=False,
            palette="viridis",
        )
        plt.title('Top 10 "Migrant Hub" Districts (Highest UER)', fontweight="bold")
        plt.xlabel("Update-to-Enrolment Ratio")
        sns.despine(left=True, bottom=True)

        # Move legend to bottom right
        plt.legend(bbox_to_anchor=(1.05, 0), loc="lower right", borderaxespad=0)

        plt.tight_layout()
        save_plot("top_migrant_hubs")
        plt.close()

    # 4. Cluster Distribution (Donut Chart for modern look)
    plt.figure(figsize=(12, 10))  # Square-ish aspect ratio
    cluster_counts = df["Cluster"].value_counts()

    # Match colors to index
    colors = [CUSTOM_PALETTE.get(c, "#cccccc") for c in cluster_counts.index]

    plt.pie(
        cluster_counts,
        labels=None,  # Remove labels from the pie itself to avoid clutter
        autopct="%1.1f%%",
        colors=colors,
        startangle=140,
        pctdistance=0.85,  # Move % text out
        wedgeprops=dict(width=0.4, edgecolor="white"),  # Donut style
        textprops={"fontsize": 14, "weight": "bold"},
    )

    # Add center text
    plt.text(
        0,
        0,
        f"Total\n{len(df)}",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
    )

    plt.title("Distribution of District Clusters", fontweight="bold")

    # Legend at BOTTOM with clear descriptions and MATCHING COLORS
    legend_handles = [
        mpatches.Patch(
            color=CUSTOM_PALETTE["Standard"], label="Standard: Low Activity"
        ),
        mpatches.Patch(
            color=CUSTOM_PALETTE["Migrant Hub"],
            label="Migrant Hub: High Updates (Migration)",
        ),
        mpatches.Patch(
            color=CUSTOM_PALETTE["Biometric Stress Zone"],
            label="Bio Stress: High Child Updates",
        ),
        mpatches.Patch(
            color=CUSTOM_PALETTE["Growth Zone"], label="Growth: High New Births"
        ),
    ]

    plt.legend(
        handles=legend_handles,
        title="Cluster Definitions",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=1,
        fontsize=12,
        frameon=True,
    )

    plt.tight_layout()
    save_plot("cluster_distribution")
    plt.close()

    print("Visualizations generated in 'analysis_results/plots'.")


def generate_report_stats(df):
    if df.empty:
        return

    print("\n=== KEY INSIGHTS FOR REPORT ===")

    migrant_count = df[df["Cluster"] == "Migrant Hub"].shape[0]
    stress_count = df[df["Cluster"] == "Biometric Stress Zone"].shape[0]
    total_districts = df.shape[0]

    print(f"Total Districts Analyzed: {total_districts}")
    print(
        f"Identified Migrant Hubs: {migrant_count} ({migrant_count / total_districts * 100:.1f}%)"
    )
    print(
        f"Identified Stress Zones: {stress_count} ({stress_count / total_districts * 100:.1f}%)"
    )

    print("\n--- Top 5 Migrant Hubs ---")
    print(
        df[df["Cluster"] == "Migrant Hub"][
            ["state", "district", "UER", "total_demo_updates"]
        ]
        .sort_values("UER", ascending=False)
        .head(5)
    )


if __name__ == "__main__":
    df = load_processed_data()
    generate_visuals(df)
    generate_report_stats(df)

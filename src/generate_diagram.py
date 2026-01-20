import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

OUTPUT_DIR = "analysis_results/plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def draw_architecture_diagram():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")

    # Define box styles
    box_style = dict(boxstyle="round,pad=0.5", ec="#2c3e50", fc="#ecf0f1", lw=2)
    highlight_style = dict(boxstyle="round,pad=0.5", ec="#27ae60", fc="#d5f5e3", lw=2)

    # 1. Data Ingestion
    ax.text(
        1.5,
        5,
        "Raw Datasets\n(Enrolment, Demo, Bio)",
        ha="center",
        va="center",
        bbox=box_style,
        fontsize=10,
    )

    # Arrow
    ax.annotate("", xy=(3, 5), xytext=(4, 5), arrowprops=dict(arrowstyle="<-", lw=2))

    # 2. ETL Layer
    ax.text(
        5.5,
        5,
        "ETL Layer\n(Data Fusion & Cleaning)",
        ha="center",
        va="center",
        bbox=box_style,
        fontsize=10,
    )

    # Arrow down
    ax.annotate(
        "", xy=(5.5, 3.8), xytext=(5.5, 4.5), arrowprops=dict(arrowstyle="<-", lw=2)
    )

    # 3. Analytics Engine (The Core)
    ax.text(
        5.5,
        3,
        "Analytics Engine\n(UER Calculation)",
        ha="center",
        va="center",
        bbox=highlight_style,
        fontsize=11,
        fontweight="bold",
    )

    # Split Arrows
    ax.annotate(
        "", xy=(3, 1.5), xytext=(4.5, 2.5), arrowprops=dict(arrowstyle="<-", lw=2)
    )  # To ML
    ax.annotate(
        "", xy=(8, 1.5), xytext=(6.5, 2.5), arrowprops=dict(arrowstyle="<-", lw=2)
    )  # To Dashboard

    # 4. AI Layer
    ax.text(
        1.5,
        1,
        "AI Model\n(K-Means & Isolation Forest)",
        ha="center",
        va="center",
        bbox=highlight_style,
        fontsize=10,
    )

    # 5. Output Layer
    ax.text(
        9.5,
        1,
        "Actionable Insights\n(Clusters & Anomaly Alerts)",
        ha="center",
        va="center",
        bbox=box_style,
        fontsize=10,
    )

    # Connection from AI to Output
    ax.annotate(
        "", xy=(8, 1), xytext=(3, 1), arrowprops=dict(arrowstyle="<-", lw=2, ls="--")
    )

    plt.title(
        "System Architecture: The 'Bridge the Gap' Framework", fontsize=14, pad=20
    )
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "system_architecture.png"))
    plt.close()


if __name__ == "__main__":
    draw_architecture_diagram()

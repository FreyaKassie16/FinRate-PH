import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Dict, Optional
import matplotlib.axes


def create_plot(
    ax: matplotlib.axes.Axes,
    reviews_df: pd.DataFrame,
    plot_type: str = "cumulative",
    app_id: Optional[str] = None,
) -> None:
    """
    Creates a plot for a single app's reviews.

    Args:
        ax (matplotlib.axes.Axes): The axes to plot on.
        reviews_df (pd.DataFrame): The DataFrame containing reviews.
        plot_type (str): The type of plot ("cumulative", "rolling", "monthly").
        app_id (str): The app ID (optional for title).
    """
    if reviews_df.empty:
        ax.clear()
        ax.text(
            0.5,
            0.5,
            "No Data Available",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
            color="gray",
        )
        return

    df = reviews_df.sort_values("review_date")
    ax.clear()

    if plot_type == "cumulative":
        df["cumulative_average_rating"] = (
            df["review_rating"].expanding().mean()
        )
        ax.plot(df["review_date"], df["cumulative_average_rating"])
        title = "Cumulative Average Rating Over Time"
        ylabel = "Cumulative Average Rating"

    elif plot_type == "rolling":
        df["rolling_average_rating"] = (
            df["review_rating"].rolling(window=30, min_periods=1).mean()
        )
        ax.plot(df["review_date"], df["rolling_average_rating"])
        title = "30-Day Rolling Average Rating Over Time"
        ylabel = "Rolling Average Rating"

    elif plot_type == "monthly":
        df_monthly = (
            df.resample("M", on="review_date")["review_rating"]
            .mean()
            .reset_index()
        )
        ax.plot(df_monthly["review_date"], df_monthly["review_rating"])
        title = "Average Monthly Rating"
        ylabel = "Average Rating"
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())

    else:
        df["cumulative_average_rating"] = (
            df["review_rating"].expanding().mean()
        )
        ax.plot(df["review_date"], df["cumulative_average_rating"])
        title = "Cumulative Average Rating Over Time (Invalid plot_type)"
        ylabel = "Cumulative Average Rating"

    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    title_str = title if not app_id else f"{title} for {app_id}"
    ax.set_title(title_str)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.figure.tight_layout()


def create_combined_plot(
    ax: matplotlib.axes.Axes,
    all_reviews_data: Dict[str, pd.DataFrame],
    plot_type: str = "cumulative",
) -> None:
    """
    Creates a combined plot for multiple apps' reviews.

    Args:
        ax (matplotlib.axes.Axes): The axes to plot on.
        all_reviews_data (dict): A dictionary of DataFrames containing reviews for each app.
        plot_type (str): The type of plot ("cumulative", "rolling", "monthly").
    """
    ax.clear()
    if not all_reviews_data:
        ax.text(
            0.5,
            0.5,
            "No Data Available",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
            color="gray",
        )
        return

    for app_id, reviews_df in all_reviews_data.items():
        if reviews_df.empty:
            print(f"Skipping {app_id} (no data).")
            continue

        df = reviews_df.sort_values("review_date")
        app_name = reviews_df.get("app_name", [app_id])[0]

        if plot_type == "cumulative":
            df["cumulative_average_rating"] = (
                df["review_rating"].expanding().mean()
            )
            ax.plot(
                df["review_date"],
                df["cumulative_average_rating"],
                label=app_name,
            )
            ylabel = "Cumulative Average Rating"
        elif plot_type == "rolling":
            df["rolling_average_rating"] = (
                df["review_rating"].rolling(window=30, min_periods=1).mean()
            )
            ax.plot(
                df["review_date"], df["rolling_average_rating"], label=app_name
            )
            ylabel = "Rolling Average Rating"
        elif plot_type == "monthly":
            df_monthly = (
                df.resample("M", on="review_date")["review_rating"]
                .mean()
                .reset_index()
            )
            ax.plot(
                df_monthly["review_date"],
                df_monthly["review_rating"],
                label=app_name,
            )
            ylabel = "Average Rating"
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
        else:
            df["cumulative_average_rating"] = (
                df["review_rating"].expanding().mean()
            )
            ax.plot(
                df["review_date"],
                df["cumulative_average_rating"],
                label=app_name,
            )
            ylabel = "Cumulative Average Rating"

    ax.set_title(f"Comparison of App Ratings ({plot_type.capitalize()})")
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.legend()
    ax.figure.tight_layout()

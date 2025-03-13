import pandas as pd


def save_reviews_to_csv(reviews_df: pd.DataFrame, filename: str) -> None:
    """
    Saves a DataFrame of reviews to a CSV file.

    Args:
        reviews_df (pd.DataFrame): The DataFrame containing reviews.
        filename (str): The path to the CSV file.
    """
    if reviews_df.empty:
        print("No reviews to save.")
        return

    try:
        reviews_df.to_csv(filename, index=False, encoding="utf-8")
        print(f"Reviews saved to {filename}")
    except Exception as e:
        print(f"Error saving reviews to CSV: {e}")

from google_play_scraper import reviews, Sort, search
import time
from typing import List, Optional, Dict, Any, Union


def search_app(
    app_name: str, country: str = "ph", lang: str = "en"
) -> Optional[List[Dict[str, Any]]]:
    """
    Searches for apps on Google Play Store.

    Args:
        app_name (str): The name of the app to search for.
        country (str): The country code (default: "ph").
        lang (str): The language code (default: "en").

    Returns:
        list: A list of search results or None if no results or an error occurs.
    """
    try:
        results = search(app_name, lang=lang, country=country, n_hits=5)
        return results if results else None
    except Exception as e:
        print(f"Error searching for app: {e}")
        return None


def get_app_reviews(
    app_id: str,
    country: str = "ph",
    lang: str = "en",
    max_reviews: Optional[int] = None,
) -> List[Dict[str, Union[str, int, Any]]]:
    """
    Fetches reviews for a given app ID.

    Args:
        app_id (str): The ID of the app.
        country (str): The country code (default: "ph").
        lang (str): The language code (default: "en").
        max_reviews (int): Maximum number of reviews to fetch (default: None, fetches all).

    Returns:
        list: A list of reviews or an empty list if an error occurs.
    """
    all_reviews = []
    continuation_token = None
    review_count = 0
    retries = 3

    for attempt in range(retries):
        try:
            while True:
                result, continuation_token = reviews(
                    app_id,
                    lang=lang,
                    country=country,
                    sort=Sort.MOST_RELEVANT,
                    count=200,
                    continuation_token=continuation_token,
                )

                for review_data in result:
                    review = {
                        "app_id": app_id,
                        "review_text": review_data["content"],
                        "review_date": review_data["at"],
                        "review_rating": review_data["score"],
                    }
                    all_reviews.append(review)
                    review_count += 1

                    if max_reviews is not None and review_count >= max_reviews:
                        return all_reviews

                if continuation_token.token is None:
                    break

                time.sleep(1)

            return all_reviews

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                print(f"Error fetching reviews for {app_id}: {e}")
                return []
            time.sleep(5)

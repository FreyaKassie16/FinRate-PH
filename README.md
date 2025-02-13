# FinRate PH: Google Play Store Review Scraper and Visualizer

## Overview

**FinRate PH** is a desktop application built with Python and Tkinter that allows users to scrape, analyze, and visualize user reviews of financial applications from the Google Play Store, with a particular focus on apps available in the Philippines.  It leverages the `google-play-scraper` library for data retrieval and `pandas`, `matplotlib` for data processing and visualization. This tool provides insights into user sentiment towards financial apps over time. This project showcases my skills in data acquisition, data manipulation, visualization, and GUI development.

## Features

*   **App Search and Selection:**  Search for financial apps by name (with results localized to the Philippines) and select the correct app from a list of potential matches.  Handles search errors gracefully.
*   **Review Scraping:** Fetches user reviews from the Google Play Store for selected applications.  Includes robust error handling with retries and rate limiting to avoid being blocked by Google Play's servers. Supports fetching all reviews (use with caution!) or a specified maximum number of reviews.
*   **Data Storage:** Saves the scraped reviews to CSV files in a user-specified output directory. The CSV files are named using the App ID and include the review text, date, and rating.
*   **Data Visualization:** Generates interactive plots of review data using Matplotlib, embedded within the Tkinter GUI:
    *   **Cumulative Average Rating:**  Displays the cumulative average rating of an app over time.
    *   **Rolling Average Rating:** Shows the 30-day rolling average rating, smoothing out short-term fluctuations.
    *   **Monthly Average Rating:** Presents the average rating per month, providing a clear view of monthly trends.
    *   **Combined Plots:**  Allows comparison of multiple apps on the same plot, using any of the above plot types.
*   **User-Friendly GUI:**  Provides a graphical user interface (Tkinter) for easy interaction.  Includes features such as:
    *   Adding and removing apps.
    *   Selecting the maximum number of reviews to fetch.
    *   Choosing the output directory.
    *   Selecting plot types.
    *   Visualizing individual or combined app data.
    *   Status updates during review fetching.
* **Threading:** The fetching process is run on a separate thread to ensure a responsive user experience.
* **App ID Selection:** Handles the selection of the app ID through a dedicated window to address cases where the app name search returns more than one result.

## Skills Demonstrated

*   **Python Programming:** Core language for the entire application.
*   **Data Scraping:**  Using the `google-play-scraper` library to extract data from the Google Play Store.
*   **Data Manipulation and Analysis:**  Employing `pandas` for data cleaning, transformation (date handling, calculating rolling averages, resampling), and aggregation.
*   **Data Visualization:**  Creating informative plots with `matplotlib`, including line plots and date-based formatting.
*   **GUI Development:** Building a user-friendly interface with `tkinter`.
*   **Error Handling:** Implementing robust error handling (e.g., network issues, API limits, invalid input) and retries.
*   **File I/O:** Saving data to CSV files.
*   **Threading:** Implementing multi-threading to improve the responsiveness of the GUI, particularly during the review fetching process.
*   **Asynchronous Operations:** Managing asynchronous tasks (fetching reviews) and updating the GUI accordingly.

## Requirements

*   Python 3.7+
*   `google-play-scraper`
*   `pandas`
*   `matplotlib`
*   `tkinter` (usually comes pre-installed with Python)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>  # Replace <repository_url>
    cd <repository_directory>    # Replace <repository_directory>
    ```

2.  **Install dependencies:**

    ```bash
    pip install google-play-scraper pandas matplotlib
    ```

## Usage

1.  **Run the script:**

    ```bash
    python main.py
    ```

2.  **Add App Names:**
    *   In the "App Names" section, enter the names of the financial apps you want to analyze, separated by commas (e.g., "GCash, PayMaya, Coins.ph").  The app focuses on the Philippines market.
    *   Click "Add".  The application will search for the apps and prompt you to select the correct one if multiple matches are found.

3.  **Fetch Reviews:**
    *   (Optional) Enter the maximum number of reviews to fetch per app in the "Max Reviews per App" field.  Leave it blank to fetch all reviews (this can be *very* slow).
    *   Click "Fetch Reviews".  The application will display status updates as it fetches the data.  The fetched data will be saved in CSV files in the "app_reviews" folder (or the folder you specify, see step 5).

4.  **Visualize Data:**
    *   **Single App Visualization:**
        *   Select an app from the "Visualize Single App" dropdown.
        *   Choose a "Plot Type" (cumulative, rolling, or monthly).
        *   Click "Visualize".
    *   **Combined App Visualization:**
        *   Select a "Plot Type" from the "Visualize Combined Apps" dropdown.
        *   Click "Visualize".

5.  **Change Output Directory:**
    *   Click the "Change..." button next to "Output Directory" to select a different folder for saving the CSV files.

## Important Notes

*   **Rate Limiting:**  The `google-play-scraper` library and this application include delays to avoid being rate-limited by Google.  Fetching a large number of reviews may still take a significant amount of time.
*   **API Changes:**  The Google Play Store's API may change without notice, which could break the functionality of this scraper.
*   **Data Accuracy:**  The accuracy of the data depends on the `google-play-scraper` library and the availability of reviews on the Google Play Store.
*   **Error Handling:**  While the application includes error handling, unexpected issues may still occur.  Check the console output for error messages.

## Future Enhancements

*   **Sentiment Analysis:** Integrate sentiment analysis (e.g., using NLTK or spaCy) to automatically classify reviews as positive, negative, or neutral.
*   **Keyword Extraction:** Identify frequently mentioned keywords in reviews to understand common user concerns or praises.
*   **More Visualization Options:**  Add more plot types (e.g., histograms of ratings, box plots).
*   **User Authentication (Optional):**  For potential deployment as a web app, add user authentication to manage data and access.
*   **Database Integration:** Store scraped data in a database (e.g., SQLite, PostgreSQL) for more efficient data management and querying.
* **Automated Updates:** Ability to regularly update the scraped data.
* **More robust scraping**: Handle CAPTCHAs or other anti-scraping measures that Google might employ.

## Disclaimer

This project is for educational and informational purposes only.  The developer is not responsible for any misuse of this tool or any consequences resulting from its use.  Always respect the terms of service of the Google Play Store.

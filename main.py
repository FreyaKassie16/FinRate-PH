from google_play_scraper import reviews, Sort, search
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading


def search_app(app_name, country="ph", lang="en"):
    """Searches for an app, handles errors, and returns app ID."""
    try:
        results = search(app_name, lang=lang, country=country, n_hits=5)
        if results:
            app_ids = [result["appId"] for result in results]
            app_titles = [result["title"] for result in results]
            return choose_app_id(app_titles, app_ids)
        else:
            messagebox.showinfo(
                "App Not Found", f"No apps found for '{app_name}'."
            )
            return None
    except Exception as e:
        messagebox.showerror("Error", f"Error searching for app: {e}")
        return None


def choose_app_id(app_titles, app_ids):
    """Creates a dialog for the user to choose the correct app ID."""
    if not app_titles:
        return None

    dialog = tk.Toplevel()
    dialog.title("Choose App")
    listbox = tk.Listbox(dialog, width=50, height=min(len(app_titles), 10))
    for title in app_titles:
        listbox.insert(tk.END, title)
    listbox.pack(padx=10, pady=10)
    selected_app_id = tk.StringVar()

    def on_select():
        try:
            index = listbox.curselection()[0]
            selected_app_id.set(app_ids[index])
            dialog.destroy()
        except IndexError:
            messagebox.showwarning("Warning", "Please select an app.")

    ok_button = ttk.Button(dialog, text="OK", command=on_select)
    ok_button.pack(pady=5)
    dialog.grab_set()
    dialog.wait_window()
    return selected_app_id.get() if selected_app_id.get() else None


def get_app_reviews(app_id, country="ph", lang="en", max_reviews=None):
    """Fetches reviews with error handling and retries."""
    all_reviews = []
    continuation_token = None
    review_count = 0
    retries = 3  # Number of retry attempts

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

                time.sleep(2)  # Rate limiting

            return all_reviews

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                print(f"Error fetching reviews for {app_id}: {e}")
                return []
            time.sleep(5)  # Wait before retrying


def save_reviews_to_csv(reviews_df, filename):
    """Saves a DataFrame of reviews to a CSV file."""
    if reviews_df.empty:  # Check if DataFrame is empty
        print("No reviews to save.")
        return

    try:
        reviews_df.to_csv(filename, index=False, encoding="utf-8")
        print(f"Reviews saved to {filename}")
    except Exception as e:
        print(f"Error saving reviews to CSV: {e}")


def create_plot(ax, reviews_df, plot_type="cumulative", app_id=None):
    """Creates a plot (now takes a DataFrame)."""
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

    else:  # Default to cumulative
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


def create_combined_plot(ax, all_reviews_data, plot_type="cumulative"):
    """Creates a combined plot (now uses DataFrames)."""
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
                df["review_date"],
                df["rolling_average_rating"],
                label=app_name,
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
        else:  # Default to Cumulative
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
    ax.figure.tight_layout()  # Only call this once
    plt.savefig("images/example.png")


class AppReviewGUI:
    """GUI for the App Review Scraper and Visualizer."""

    def __init__(self, master):
        self.master = master
        master.title("FinRate PH")
        master.geometry("800x700")

        self.app_ids = []
        self.all_app_data = {}  # Store DataFrames here
        self.output_dir = "app_reviews"
        self.app_names = {}  # Dictionary to map app_id to app_name

        # --- GUI Elements (same as before, but with threading calls) ---
        self.app_name_frame = ttk.LabelFrame(master, text="App Names")
        self.app_name_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        master.columnconfigure(0, weight=1)

        self.app_name_label = ttk.Label(
            self.app_name_frame, text="App Names (comma-separated):"
        )
        self.app_name_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.app_name_entry = ttk.Entry(self.app_name_frame, width=50)
        self.app_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.app_name_frame.columnconfigure(1, weight=1)
        self.add_app_name_button = ttk.Button(
            self.app_name_frame, text="Add", command=self.add_app_name
        )
        self.add_app_name_button.grid(row=0, column=2, padx=5, pady=2)

        self.app_id_tree = ttk.Treeview(
            self.app_name_frame,
            columns=("App ID", "App Name"),
            show="headings",
            height=5,
        )
        self.app_id_tree.heading("#1", text="App ID")
        self.app_id_tree.heading("#2", text="App Name")
        self.app_id_tree.column("#1", anchor="w")
        self.app_id_tree.column("#2", anchor="w")
        self.app_id_tree.grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=2
        )
        self.remove_app_id_button = ttk.Button(
            self.app_name_frame,
            text="Remove Selected",
            command=self.remove_app_id,
        )
        self.remove_app_id_button.grid(
            row=2, column=0, columnspan=3, padx=5, pady=2
        )

        self.fetch_frame = ttk.Frame(master)
        self.fetch_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.max_reviews_label = ttk.Label(
            self.fetch_frame,
            text="Max Reviews per App (if None, fetches all [SLOW!!]):",
        )
        self.max_reviews_label.grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.max_reviews_entry = ttk.Entry(self.fetch_frame, width=10)
        self.max_reviews_entry.grid(
            row=0, column=1, sticky="w", padx=5, pady=2
        )

        self.fetch_button = ttk.Button(
            self.fetch_frame,
            text="Fetch Reviews",
            command=self.fetch_reviews,
            # style="Accent.TButton",
        )
        self.fetch_button.grid(row=0, column=2, padx=10, pady=5)

        self.status_label = ttk.Label(master, text="", anchor="w")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=10, pady=2)

        self.visualization_frame = ttk.LabelFrame(master, text="Visualization")
        self.visualization_frame.grid(
            row=3, column=0, padx=10, pady=5, sticky="ew"
        )

        self.single_app_label = ttk.Label(
            self.visualization_frame, text="Visualize Single App:"
        )
        self.single_app_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.single_app_combo = ttk.Combobox(
            self.visualization_frame, values=[], state="readonly"
        )
        self.single_app_combo.grid(
            row=0, column=1, sticky="ew", padx=5, pady=2
        )

        self.plot_type_label = ttk.Label(
            self.visualization_frame, text="Plot Type:"
        )
        self.plot_type_label.grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.plot_type_combo = ttk.Combobox(
            self.visualization_frame,
            values=["cumulative", "rolling", "monthly"],
            state="readonly",
        )
        self.plot_type_combo.grid(row=0, column=3, sticky="ew", padx=5, pady=2)
        self.plot_type_combo.set("cumulative")

        self.visualize_single_button = ttk.Button(
            self.visualization_frame,
            text="Visualize",
            command=self.visualize_single,
        )
        self.visualize_single_button.grid(row=0, column=4, padx=5, pady=2)

        self.visualize_combined_label = ttk.Label(
            self.visualization_frame, text="Visualize Combined Apps:"
        )
        self.visualize_combined_label.grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.visualize_combined_plot_type_combo = ttk.Combobox(
            self.visualization_frame,
            values=["cumulative", "rolling", "monthly"],
            state="readonly",
        )
        self.visualize_combined_plot_type_combo.grid(
            row=1, column=1, sticky="ew", padx=5, pady=2
        )
        self.visualize_combined_plot_type_combo.set("cumulative")

        self.visualize_combined_button = ttk.Button(
            self.visualization_frame,
            text="Visualize",
            command=self.visualize_combined,
        )
        self.visualize_combined_button.grid(row=1, column=2, padx=5, pady=2)

        self.output_dir_frame = ttk.Frame(master)
        self.output_dir_frame.grid(
            row=4, column=0, sticky="ew", padx=10, pady=5
        )

        self.output_dir_label = ttk.Label(
            self.output_dir_frame, text="Output Directory:"
        )
        self.output_dir_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.output_dir_display = ttk.Entry(
            self.output_dir_frame, width=50, state="readonly"
        )
        self.output_dir_display.grid(
            row=0, column=1, sticky="ew", padx=5, pady=2
        )
        self.output_dir_frame.columnconfigure(1, weight=1)
        self.output_dir_button = ttk.Button(
            self.output_dir_frame,
            text="Change...",
            command=self.set_output_directory,
        )
        self.output_dir_button.grid(row=0, column=2, padx=5, pady=2)
        self.output_dir_display.insert(0, self.output_dir)

        self.plot_frame = ttk.Frame(master)
        self.plot_frame.grid(row=5, column=0, padx=10, pady=5, sticky="nsew")
        master.rowconfigure(5, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(
            side=tk.TOP, fill=tk.BOTH, expand=True
        )

        style = ttk.Style()
        style.configure(
            "Accent.TButton", foreground="white", background="#007bff"
        )

    def add_app_name(self):
        """Adds App IDs, searching by name (no threading needed here)."""
        app_names_input = self.app_name_entry.get()
        new_app_names = [
            name.strip() for name in app_names_input.split(",") if name.strip()
        ]

        for app_name in new_app_names:
            app_id = search_app(app_name)
            if app_id:
                if app_id not in self.app_ids:
                    self.app_ids.append(app_id)
                    self.app_names[app_id] = app_name
                    self.app_id_tree.insert(
                        "", tk.END, values=(app_id, app_name)
                    )
        self.app_name_entry.delete(0, tk.END)
        self.update_single_app_combobox()

    def remove_app_id(self):
        """Removes App ID (no threading needed)."""
        try:
            selected_item = self.app_id_tree.selection()[0]
            app_id_to_remove = self.app_id_tree.item(selected_item)["values"][
                0
            ]
            self.app_id_tree.delete(selected_item)
            self.app_ids.remove(app_id_to_remove)
            del self.app_names[app_id_to_remove]
            self.update_single_app_combobox()
        except IndexError:
            messagebox.showwarning("Warning", "No App ID selected.")

    def update_single_app_combobox(self):
        """Updates combobox (no threading)."""
        self.single_app_combo["values"] = [
            self.app_names[app_id] for app_id in self.app_ids
        ]

    def _fetch_reviews_thread(self):
        """Fetches reviews in a separate thread."""
        self.all_app_data = {}  # Clear previous data
        if not self.app_ids:
            messagebox.showwarning(
                "Warning", "Please add at least one App ID."
            )
            return

        try:
            max_reviews_input = self.max_reviews_entry.get()
            max_reviews_per_app = (
                int(max_reviews_input) if max_reviews_input else None
            )
        except ValueError:
            messagebox.showerror("Error", "Invalid Max Reviews value.")
            return

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        for app_id in self.app_ids:
            app_name = self.app_names[app_id]
            self.status_label.config(
                text=f"Fetching reviews for {app_name}..."
            )
            self.master.update_idletasks()

            reviews_list = get_app_reviews(
                app_id, max_reviews=max_reviews_per_app
            )
            if reviews_list:
                reviews_df = pd.DataFrame(reviews_list)
                reviews_df["review_date"] = pd.to_datetime(
                    reviews_df["review_date"]
                )

                reviews_df["app_name"] = app_name
                self.all_app_data[app_id] = reviews_df

                filename = os.path.join(
                    self.output_dir, f"{app_id}_reviews.csv"
                )
                save_reviews_to_csv(reviews_df, filename)
            else:
                messagebox.showinfo(
                    "Info", f"No reviews retrieved for {app_id}."
                )

        self.status_label.config(text="Reviews fetched and saved.")

    def fetch_reviews(self):
        """Starts the fetch reviews thread."""
        self.fetch_button.config(state="disabled")
        try:
            thread = threading.Thread(target=self._fetch_reviews_thread)
            thread.start()
        finally:
            self.master.after(0, lambda: self.wait_for_thread(thread))

    def wait_for_thread(self, thread):
        """Check if thread is still alive, re-enable button when done"""
        if thread.is_alive():
            # Check again in 100ms
            self.master.after(100, lambda: self.wait_for_thread(thread))
        else:
            self.fetch_button.config(state="normal")

    def visualize_single(self):
        """Visualizes reviews for a single app (uses DataFrame)."""
        selected_app_name = self.single_app_combo.get()
        if not selected_app_name:
            messagebox.showwarning("Warning", "Select an app.")
            return

        selected_app_id = None
        for app_id, app_name in self.app_names.items():
            if app_name == selected_app_name:
                selected_app_id = app_id
                break

        if not selected_app_id:
            messagebox.showerror("Error", f"No data for {selected_app_name}.")
            return

        if selected_app_id not in self.all_app_data:
            messagebox.showerror("Error", f"No data for {selected_app_id}.")
            return

        plot_type = self.plot_type_combo.get()
        create_plot(
            self.ax,
            self.all_app_data[selected_app_id],
            plot_type,
            selected_app_name,
        )
        self.canvas.draw()

    def visualize_combined(self):
        """Visualizes combined reviews (uses DataFrames)."""
        if len(self.all_app_data) < 2:
            messagebox.showwarning(
                "Warning", "Fetch reviews for at least two apps."
            )
            return

        plot_type = self.visualize_combined_plot_type_combo.get()
        create_combined_plot(self.ax, self.all_app_data, plot_type)
        self.canvas.draw()

    def set_output_directory(self):
        """Sets the output directory."""
        directory = filedialog.askdirectory(initialdir=self.output_dir)
        if directory:
            self.output_dir = directory
            self.output_dir_display.config(state="normal")
            self.output_dir_display.delete(0, tk.END)
            self.output_dir_display.insert(0, self.output_dir)
            self.output_dir_display.config(state="readonly")


def main():
    root = tk.Tk()
    gui = AppReviewGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

import os
from typing import List, Optional, Dict

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plotting import create_combined_plot, create_plot
from scraper import get_app_reviews, search_app
from utils import save_reviews_to_csv


class FetchThread(QThread):
    status_update = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(
        self,
        app_ids: List[str],
        app_names: Dict[str, str],
        max_reviews: Optional[int],
        output_dir: str,
        all_app_data: Dict[str, pd.DataFrame],
    ) -> None:
        super().__init__()
        self.app_ids = app_ids
        self.app_names = app_names
        self.max_reviews = max_reviews
        self.output_dir = output_dir
        self.all_app_data = all_app_data

    def run(self) -> None:
        if not self.app_ids:
            QMessageBox.warning(
                None, "Warning", "Please add at least one App ID."
            )
            self.finished.emit()
            return

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        for app_id in self.app_ids:
            app_name = self.app_names[app_id]
            self.status_update.emit(f"Fetching reviews for {app_name}...")
            reviews_list = get_app_reviews(
                app_id, max_reviews=self.max_reviews
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
                QMessageBox.information(
                    None, "Info", f"No reviews retrieved for {app_id}."
                )
        self.status_update.emit("Reviews fetched and saved.")
        self.finished.emit()


class AppSelectionDialog(QDialog):
    def __init__(
        self, app_titles: List[str], app_ids: List[str], parent=None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Choose App")
        self.app_ids = app_ids
        self.selected_app_id = None

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.addItems(app_titles)
        layout.addWidget(self.list_widget)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.on_select)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def on_select(self) -> None:
        try:
            index = self.list_widget.currentRow()
            if index >= 0:
                self.selected_app_id = self.app_ids[index]
                self.accept()
            else:
                QMessageBox.warning(self, "Warning", "Please select an app.")
        except IndexError:
            QMessageBox.warning(self, "Warning", "Please select an app.")


class AppReviewGUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FinRate PH")
        self.setGeometry(100, 100, 800, 850)

        self.app_ids = []
        self.all_app_data = {}  # Store DataFrames here
        self.output_dir = "app_reviews"
        self.app_names = {}  # Dictionary to map app_id to app_name

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.app_name_group = QGroupBox("App Names")
        app_name_layout = QGridLayout()
        self.app_name_label = QLabel("App Names (comma-separated):")
        self.app_name_entry = QLineEdit()
        self.app_name_entry.setMinimumWidth(300)
        self.add_app_name_button = QPushButton("Add")
        self.add_app_name_button.clicked.connect(self.add_app_name)
        app_name_layout.addWidget(self.app_name_label, 0, 0)
        app_name_layout.addWidget(self.app_name_entry, 0, 1)
        app_name_layout.addWidget(self.add_app_name_button, 0, 2)
        self.app_id_tree = QTreeWidget()
        self.app_id_tree.setHeaderLabels(["App Id", "App Name"])
        self.app_id_tree.setColumnWidth(0, 200)
        app_name_layout.addWidget(self.app_id_tree, 1, 0, 1, 3)
        self.remove_app_id_button = QPushButton("Remove Selected")
        self.remove_app_id_button.clicked.connect(self.remove_app_id)
        app_name_layout.addWidget(self.remove_app_id_button, 2, 0, 1, 3)
        self.app_name_group.setLayout(app_name_layout)
        main_layout.addWidget(self.app_name_group)

        fetch_widget = QWidget()
        fetch_layout = QGridLayout()
        self.max_reviews_label = QLabel(
            "Max Reviews per App (if None, fetches all [SLOW!!]):"
        )
        self.max_reviews_entry = QLineEdit()
        self.max_reviews_entry.setMaximumWidth(100)
        self.fetch_button = QPushButton("Fetch Reviews")
        self.fetch_button.clicked.connect(self.fetch_reviews)
        fetch_layout.addWidget(self.max_reviews_label, 0, 0)
        fetch_layout.addWidget(self.max_reviews_entry, 0, 1)
        fetch_layout.addWidget(self.fetch_button, 0, 2)
        fetch_widget.setLayout(fetch_layout)
        main_layout.addWidget(fetch_widget)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        self.visualization_group = QGroupBox("Visualization")
        vis_layout = QGridLayout()
        self.single_app_label = QLabel("Visualize Single App:")
        self.single_app_combo = QComboBox()
        self.plot_type_label = QLabel("Plot Type:")
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["cumulative", "rolling", "monthly"])
        self.plot_type_combo.setCurrentText("cumulative")
        self.visualize_single_button = QPushButton("Visualize")
        self.visualize_single_button.clicked.connect(self.visualize_single)
        vis_layout.addWidget(self.single_app_label, 0, 0)
        vis_layout.addWidget(self.single_app_combo, 0, 1)
        vis_layout.addWidget(self.plot_type_label, 0, 2)
        vis_layout.addWidget(self.plot_type_combo, 0, 3)
        vis_layout.addWidget(self.visualize_single_button, 0, 4)
        self.visualize_combined_label = QLabel("Visualize Combined Apps:")
        self.visualize_combined_plot_type_combo = QComboBox()
        self.visualize_combined_plot_type_combo.addItems(
            ["cumulative", "rolling", "monthly"]
        )
        self.visualize_combined_plot_type_combo.setCurrentText("cumulative")
        self.visualize_combined_button = QPushButton("Visualize")
        self.visualize_combined_button.clicked.connect(self.visualize_combined)
        vis_layout.addWidget(self.visualize_combined_label, 1, 0)
        vis_layout.addWidget(self.visualize_combined_plot_type_combo, 1, 1)
        vis_layout.addWidget(self.visualize_combined_button, 1, 2)
        self.visualization_group.setLayout(vis_layout)
        main_layout.addWidget(self.visualization_group)

        # Output Directory Frame
        output_widget = QWidget()
        output_layout = QGridLayout()
        self.output_dir_label = QLabel("Output Directory:")
        self.output_dir_display = QLineEdit(self.output_dir)
        self.output_dir_display.setReadOnly(True)
        self.output_dir_button = QPushButton("Change...")
        self.output_dir_button.clicked.connect(self.set_output_directory)
        output_layout.addWidget(self.output_dir_label, 0, 0)
        output_layout.addWidget(self.output_dir_display, 0, 1)
        output_layout.addWidget(self.output_dir_button, 0, 2)
        output_widget.setLayout(output_layout)
        main_layout.addWidget(output_widget)

        # Plot Frame
        self.fig, self.ax = plt.subplots(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        main_layout.addWidget(self.canvas)
        main_layout.setStretch(5, 1)  # Allow plot to expand

    def choose_app_id(
        self, app_titles: List[str], app_ids: List[str]
    ) -> Optional[str]:
        """
        Creates a dialog for the user to choose the correct app ID.

        Args:
            app_titles (list): List of app titles.
            app_ids (list): List of corresponding app IDs.

        Returns:
            str: The selected app ID or None if no selection is made.
        """
        dialog = AppSelectionDialog(app_titles, app_ids, self)
        if dialog.exec_():
            return dialog.selected_app_id
        return None

    def add_app_name(self) -> None:
        app_names_input = self.app_name_entry.text()
        new_app_names = [
            name.strip() for name in app_names_input.split(",") if name.strip()
        ]

        for app_name in new_app_names:
            results = search_app(app_name)
            if results:
                app_titles = [result["title"] for result in results]
                app_ids = [result["appId"] for result in results]
                selected_app_id = self.choose_app_id(app_titles, app_ids)
                if selected_app_id and selected_app_id not in self.app_ids:
                    self.app_ids.append(selected_app_id)
                    self.app_names[selected_app_id] = app_name
                    item = QTreeWidgetItem(
                        self.app_id_tree, [selected_app_id, app_name]
                    )
            else:
                QMessageBox.information(
                    self, "App Not Found", f"No apps found for '{app_name}'."
                )
        self.app_name_entry.clear()
        self.update_single_app_combobox()

    def remove_app_id(self) -> None:
        selected_items = self.app_id_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No App ID selected.")
            return
        item = selected_items[0]
        app_id_to_remove = item.text(0)
        self.app_ids.remove(app_id_to_remove)
        del self.app_names[app_id_to_remove]
        self.app_id_tree.takeTopLevelItem(
            self.app_id_tree.indexOfTopLevelItem(item)
        )
        self.update_single_app_combobox()

    def update_single_app_combobox(self) -> None:
        self.single_app_combo.clear()
        self.single_app_combo.addItems(
            [self.app_names[app_id] for app_id in self.app_ids]
        )

    def fetch_reviews(self) -> None:
        self.fetch_button.setEnabled(False)
        try:
            max_reviews_input = self.max_reviews_entry.text()
            max_reviews = int(max_reviews_input) if max_reviews_input else None
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid Max Reviews value.")
            self.fetch_button.setEnabled(True)
            return

        self.thread = FetchThread(
            self.app_ids,
            self.app_names,
            max_reviews,
            self.output_dir,
            self.all_app_data,
        )
        self.thread.status_update.connect(self.status_label.setText)
        self.thread.finished.connect(
            lambda: self.fetch_button.setEnabled(True)
        )
        self.thread.start()

    def visualize_single(self) -> None:
        selected_app_name = self.single_app_combo.currentText()
        if not selected_app_name:
            QMessageBox.warning(self, "Warning", "Select an app.")
            return

        selected_app_id = next(
            (
                app_id
                for app_id, name in self.app_names.items()
                if name == selected_app_name
            ),
            None,
        )
        if not selected_app_id or selected_app_id not in self.all_app_data:
            QMessageBox.critical(
                self, "Error", f"No data for {selected_app_name}."
            )
            return
        plot_type = self.plot_type_combo.currentText()
        create_plot(
            self.ax,
            self.all_app_data[selected_app_id],
            plot_type,
            selected_app_name,
        )
        self.canvas.draw()

    def visualize_combined(self) -> None:
        if len(self.all_app_data) < 2:
            QMessageBox.warning(
                self, "Warning", "Fetch reviews for at least two apps."
            )
            return
        plot_type = self.visualize_combined_plot_type_combo.currentText()
        create_combined_plot(self.ax, self.all_app_data, plot_type)
        self.canvas.draw()

    def set_output_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir
        )
        if directory:
            self.output_dir = directory
            self.output_dir_display.setText(self.output_dir)

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QDialog
import numpy as np
from FSPM.utilities import data_preparation, parameters_creation, conn_data_preparation
from FSPM.statparmap import preprocessing, static_correlation
from FSPM.visuals import show_map, conn_visualization
from FSPM.funcon import network_metrics, conn_correlation, conn_preprocessing
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import QTimer
import pandas as pd
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QDialog, QTableWidget, QTableWidgetItem, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvas
from PyQt5.QtCore import Qt
import ipywidgets as widgets
from IPython.display import display, clear_output
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mplsoccer import Pitch





class PlayerSelectionPlotPopup(QDialog):
    def __init__(self, df_passes, avg_connectivity_matrix, significant_connections, all_players, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Player Selection and Significant Connections Plot")
        self.df_passes = df_passes
        self.avg_connectivity_matrix = avg_connectivity_matrix
        self.significant_connections = significant_connections
        self.all_players = all_players

        self.selected_players = [None] * 11

        layout = QVBoxLayout(self)

        # Create dropdowns for player selection
        self.dropdowns = []

        most_frequent_starting_eleven = conn_data_preparation.get_most_frequent_starting_eleven(df_passes)

        dropdown_layout_1 = QHBoxLayout()
        dropdown_layout_2 = QHBoxLayout()

        for i in range(11):
            dropdown = QComboBox(self)
            dropdown.addItems(all_players)
            dropdown.setCurrentText(most_frequent_starting_eleven[i])
            dropdown.currentIndexChanged.connect(self.update_plot)
            self.dropdowns.append(dropdown)
            if i < 6:
                dropdown_layout_1.addWidget(dropdown)
            else:
                dropdown_layout_2.addWidget(dropdown)

        layout.addLayout(dropdown_layout_1)
        layout.addLayout(dropdown_layout_2)

        # Create the canvas for plotting
        self.canvas = FigureCanvas(Figure(figsize=(15, 20)))
        layout.addWidget(self.canvas)

        self.update_plot()

    def update_plot(self):
        selected_players = [dropdown.currentText() for dropdown in self.dropdowns]
        self.plot_players_and_significant_connections(selected_players)

    def plot_players_and_significant_connections(self, selected_players):
        self.canvas.figure.clf()
        pitch = Pitch(pitch_type='opta', line_zorder=4,
                      pitch_color='#22312b', line_color='#efefef')
        ax = self.canvas.figure.add_subplot(111)
        pitch.draw(ax=ax)
        self.canvas.figure.set_facecolor('#22312b')

        mean_coordinates = self.df_passes.groupby('playerName')[['x', 'y']].mean()
        mean_coordinates.columns = ['mean_x', 'mean_y']

        for player in selected_players:
            if player in mean_coordinates.index:
                mean_x = mean_coordinates.loc[player, 'mean_x']
                mean_y = mean_coordinates.loc[player, 'mean_y']
                pitch.scatter(mean_x, mean_y, ax=ax, label=player, s=100, edgecolor='k', color='red', zorder=2)
                ax.text(mean_x, mean_y, player, fontsize=10, ha='center', color='white', zorder = 3)

        for i, player_i in enumerate(selected_players):
            for j, player_j in enumerate(selected_players):
                if player_i in mean_coordinates.index and player_j in mean_coordinates.index:
                    x_start = mean_coordinates.loc[player_i, 'mean_x']
                    y_start = mean_coordinates.loc[player_j, 'mean_y']
                    if self.significant_connections[self.all_players.index(player_i), self.all_players.index(player_j)]:
                        pitch.lines(x_start, mean_coordinates.loc[player_i, 'mean_y'],
                                    mean_coordinates.loc[player_j, 'mean_x'], y_start, ax=ax,
                                    color='green', lw=self.avg_connectivity_matrix[self.all_players.index(player_i), self.all_players.index(player_j)] * 35,
                                    alpha=0.9, zorder=1)

        self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Football Functional Connectivity Analysis (FFCA)")
        tab_widget = QTabWidget()

        data_preparation_tab = DataTab('Connectivity Data Preparation', 'Prepare Data', data_preparation=True, main_window=self)
        data_analysis_tab = DataTab('Functional Connectivity Analysis', 'Analyze Data', data_analysis=True, main_window=self)

        tab_widget.addTab(data_preparation_tab, "Data Preparation")
        tab_widget.addTab(data_analysis_tab, "Data Analysis")

        self.setCentralWidget(tab_widget)
        self.shared_data = {}

    def set_shared_data (self, key, value):
        self.shared_data[key] = value
    def get_shared_data (self, key):
        return self.shared_data.get(key)

class DataTab(QWidget):
    def __init__(self, text, button_text, data_preparation=False, data_analysis=False, main_window=None):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()

        # Load the logo image and add to the layout
        image_label = QLabel(self)
        pixmap = QPixmap("/Users/michele/code/micheledeantoni/FSPM/FSPM/GUI/FFCA_logo.png")  # Load the logo directly by name
        image_label.setPixmap(pixmap.scaledToWidth(600))  # Scale image to a reasonable size
        layout.addWidget(image_label)

        if data_preparation:
            self.load_csv_button = QPushButton("Load CSV")
            self.load_csv_button.clicked.connect(self.load_csv)
            layout.addWidget(self.load_csv_button)

            self.data_preparation = QPushButton("Prepare Data")
            self.data_preparation.setEnabled(False)  # Disable until CSV is loaded
            self.data_preparation.clicked.connect(self.data_prep)
            layout.addWidget(self.data_preparation)

            self.main_button = QPushButton("Show Network Metrics")
            self.main_button.setEnabled(False)  # Disable until CSV is loaded
            self.main_button.clicked.connect(self.network_metrics)
            layout.addWidget(self.main_button)

        if data_analysis:
            self.analysis_button = QPushButton("Compute Basic Parameters")
            self.analysis_button.clicked.connect(self.compute_basic_parameters)
            self.analysis_button.setEnabled(True)
            layout.addWidget(self.analysis_button)

            self.parameter_menu = QComboBox()
            self.parameter_menu.setEnabled(False)
            self.parameter_menu.currentIndexChanged.connect(self.parameter_changed)
            layout.addWidget(self.parameter_menu)

            self.correlation_button = QPushButton("Run Correlation Analysis")
            self.correlation_button.setEnabled(False)
            self.correlation_button.clicked.connect(self.correlation_analysis_stub)
            layout.addWidget(self.correlation_button)

            self.interactive_plot_button = QPushButton("Visualize Player Network")
            self.interactive_plot_button.setEnabled(False)  # Disable until data is ready
            self.interactive_plot_button.clicked.connect(self.show_interactive_plot)
            layout.addWidget(self.interactive_plot_button)

        self.setLayout(layout)
        self.data_frame = None

    def load_csv(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)", options=options)
        if fileName:
            self.df_passes, self.df_all_events  = conn_data_preparation.prepare_data(fileName)
            #export the shared data
            self.main_window.set_shared_data('df_passes', self.df_passes)
            self.main_window.set_shared_data('df_all_events', self.df_all_events)
            print("CSV loaded successfully:")
            # self.update_selection_menu()
            self.data_preparation.setEnabled(True)
            # self.filter_button.setEnabled(True)

    def data_prep(self):
        if self.df_passes is not None and self.df_all_events is not None:
            self.filtered_pass_data = data_preparation.filter_pass_data_by_top_players(self.df_passes, self.df_all_events)
            self.all_connectivity_matrices, self.all_player_times = conn_preprocessing.process_matches(self.df_all_events)

            # Create a master list of all players who appeared in any match
            all_players = set()
            for player_times in self.all_player_times:
                all_players.update(player_times.keys())
            all_players = sorted(list(all_players))
            self.all_players = all_players
            #export all_players
            self.main_window.set_shared_data('all_players', self.all_players)

            # Align each match's connectivity matrix to this master list
            self.aligned_connectivity_matrices, self.avg_connectivity_matrix = conn_preprocessing.align_connectivity_matrices(self.all_connectivity_matrices,
                                                                                                                    self.all_player_times,
                                                                                                                    self.all_players)
            #export the shared data
            self.main_window.set_shared_data('aligned_connectivity_matrices', self.aligned_connectivity_matrices)
            self.main_window.set_shared_data('avg_connectivity_matrix', self.avg_connectivity_matrix)

            print("Data prepared successfully")
            self.main_button.setEnabled(True)


    def network_metrics(self):
        if self.filtered_pass_data is not None:
            self.aggregated_metrics = network_metrics.compute_pass_network_metrics(self.filtered_pass_data)
            print("Network metrics computed successfully")
            self.top_players = network_metrics.get_players_with_max_metrics(self.aggregated_metrics)
            self.show_metrics_popup(self.top_players)

    def show_metrics_popup(self, metrics):
        dialog = QDialog(self)
        dialog.setWindowTitle("Network Metrics")

        layout = QVBoxLayout(dialog)

        explanations = QLabel(
            "Degree Centrality: Reflects the number of direct connections a player has.\n"
            "Betweenness Centrality: Reflects the extent to which a player lies on the paths between other players.\n"
            "Closeness Centrality: Reflects how close a player is to all other players in the network.\n"
            "Eigenvector Centrality: Reflects a player's influence in the network based on connections.\n"
            "Clustering Coefficient: Reflects how often a player's teammates are also passing to each other, indicating local passing triangles and teamwork."
        )
        layout.addWidget(explanations)

        table = QTableWidget()
        table.setRowCount(len(metrics))
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['Measure', 'Player', 'Value'])

        for row, (measure, (player, value)) in enumerate(metrics.items()):
            measure_name = measure.replace('_', ' ').capitalize()
            measure_item = QTableWidgetItem(measure_name)
            measure_item.setFlags(measure_item.flags() & ~Qt.ItemIsEditable)  # Make item uneditable
            player_item = QTableWidgetItem(player)
            player_item.setFlags(player_item.flags() & ~Qt.ItemIsEditable)  # Make item uneditable
            value_item = QTableWidgetItem(f"{value:.4f}")
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)  # Make item uneditable

            table.setItem(row, 0, measure_item)
            table.setItem(row, 1, player_item)
            table.setItem(row, 2, value_item)

        table.resizeColumnsToContents()  # Adjust column width to fit the text

        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.exec_()

    def show_figure_popup(self, figure):
        dialog = QDialog(self)
        dialog.setWindowTitle("P-Values Visualization")

        layout = QVBoxLayout(dialog)

        # Create a canvas to display the figure
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)

        # Resize the canvas to fit the figure
        canvas.draw()
        dialog.resize(canvas.sizeHint())

        dialog.setLayout(layout)
        dialog.exec_()

    def update_parameter_menu (self):
        self.parameter_menu.clear()
        self.parameter_menu.addItems(['Goals Scored','Goals Conceded', 'Custom Matrix'])
        self.parameter_menu.setEnabled(True)


    def parameter_changed (self, index):
        self.selected_parameter =  self.parameter_menu.currentText()
        print (f"Selcted parameter {self.selected_parameter}")


    def correlation_analysis_stub(self):
        if self.selected_parameter != 'Custom Matrix':
            X = pd.DataFrame({
                'goals_scored': self.goals_scored,
                'goals_conceded': self.goals_conceded})
            X['intercept'] = 1
            X = X[['intercept', 'goals_scored','goals_conceded']]
            self.X = X
            if self.selected_parameter == 'Goals Scored':
                self.contrast = np.array([0, 1, 0])
            else:
                self.contrast = np.array ([0, 0, 1])
        else:
            print("Custom matrix selected")
        self.correlation_analysis()
        self.interactive_plot_button.setEnabled(True)
        print ('Correlation Analsysi Completed')

    def correlation_analysis(self):
        #get the data
        self.aligned_connectivity_matrices = self.main_window.get_shared_data('aligned_connectivity_matrices')
        self.Y = np.array([matrix.flatten() for matrix in self.aligned_connectivity_matrices])
        if np.array_equal(self.contrast, np.array([0, 1, 0])):
            self.contrast_index = 1
        else:
            self.contrast_index = 2

        self.coefs, self.pvals = conn_correlation.perform_regression_with_contrast(self.Y,
                                                                                   self.X,
                                                                                   contrast_index=self.contrast_index,
                                                                                   positive=True)
        # Reshape coefficients and p-values to the original connectivity matrix shape
        self.all_players = self.main_window.get_shared_data('all_players')
        self.coef_matrix = self.coefs.reshape((len(self.all_players), len(self.all_players)))
        self.pval_matrix = self.pvals.reshape((len(self.all_players), len(self.all_players)))

        # Identify significant connections
        self.significant_connections = self.pval_matrix < 0.05

        # Visualize p-values and show in a popup
        figure = conn_visualization.visualize_pvalues(self.pval_matrix, self.all_players)
        self.show_figure_popup(figure)

    def compute_basic_parameters(self):
        # Placeholder function
        print("Computing basic parameters...")
        self.goals_scored, self.goals_conceded = parameters_creation.match_goals(self.main_window.get_shared_data('df_all_events'))
        if len (self.goals_conceded) == len(self.main_window.get_shared_data('df_all_events').matchId.unique()):
            self.update_parameter_menu()
            self.correlation_button.setEnabled(True)
        else:
            print('Issues with Design Matrix')

    def show_interactive_plot(self):
        self.df_passes = self.main_window.get_shared_data('df_passes')

        self.dialog = PlayerSelectionPlotPopup(
            self.df_passes,
            self.main_window.get_shared_data('avg_connectivity_matrix'),
            self.significant_connections,
            self.all_players,
            self
        )
        self.dialog.exec_()

def main():
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

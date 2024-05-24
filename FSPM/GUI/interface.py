from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QDialog
import numpy as np
from FSPM.utilities import data_preparation, parameters_creation
from FSPM.statparmap import preprocessing, static_correlation
from FSPM.visuals import show_map
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import QTimer
import pandas as pd
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvas

class GraphPopup(QDialog):
    def __init__(self, data,  res = None, plot_type='general', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Heatmap Visualization")
        self.data = data  # Store the data
        self.res = res
        self.plot_type = plot_type  # 'general' for general heatmap, 'result' for specific map with results
        self.initUI()

    def initUI(self):
        plot_button = QPushButton("Show Heatmap", self)
        # Connect button to the appropriate plotting function based on plot_type
        if self.plot_type == 'general':
            plot_button.clicked.connect(self.plot_graph)
        elif self.plot_type == 'result':
            plot_button.clicked.connect(self.plot_graph_result)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(plot_button)

    def plot_graph(self):
        # Example plotting function; you might need to replace `show_map.plot_heatmap_general` with your actual function
        fig = show_map.plot_heatmap_general(self.data)
        self.canvas = FigureCanvas(fig)
        self.layout.addWidget(self.canvas)
        self.canvas.draw()
        self.resize(int(fig.get_size_inches()[0] * fig.dpi), int(fig.get_size_inches()[1] * fig.dpi))

    def plot_graph_result(self):
        # Example result plotting function; update with your actual function
        #map_stats = self.main_window.get_shared_data('maps_stats')
        fig = show_map.plot_map(self.data, self.res, significant=False)
        self.canvas = FigureCanvas(fig)
        self.layout.addWidget(self.canvas)
        self.canvas.draw()
        self.resize(int(fig.get_size_inches()[0] * fig.dpi), int(fig.get_size_inches()[1] * fig.dpi))

# Usage example:
# dialog = GraphPopup(data, plot_type='general')  # To show general heatmap
# dialog.show()

# dialog = GraphPopup(data, plot_type='result')  # To show result-specific heatmap
# dialog.show()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Football Statistical Parameter Mapping (FSPM)")
        tab_widget = QTabWidget()

        data_preparation_tab = DataTab('Data Preparation', 'Prepare Data', data_preparation=True, main_window=self)
        data_analysis_tab = DataTab('Data Analysis', 'Analyze Data', data_analysis=True, main_window=self)

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
        pixmap = QPixmap("/Users/michele/code/micheledeantoni/FSPM/FSPM/GUI/FSPM_logo2.png")  # Load the logo directly by name
        image_label.setPixmap(pixmap.scaledToWidth(600))  # Scale image to a reasonable size
        layout.addWidget(image_label)

        # Add a text label beneath the image
        #label = QLabel(text)
        #layout.addWidget(label)


        if data_preparation:
            self.load_csv_button = QPushButton("Load CSV")
            self.load_csv_button.clicked.connect(self.load_csv)
            layout.addWidget(self.load_csv_button)

            self.selection_menu = QComboBox()
            self.selection_menu.setEnabled(False)  # Disable until CSV is loaded
            self.selection_menu.currentIndexChanged.connect(self.selection_changed)  # Connect signal
            layout.addWidget(self.selection_menu)

            self.main_button = QPushButton(button_text)
            self.main_button.setEnabled(False)  # Disable until CSV is loaded
            self.main_button.clicked.connect(self.preprocess_data_stub)
            layout.addWidget(self.main_button)

            self.filter_button = QPushButton("Filter Outliers")
            self.filter_button.clicked.connect(self.outlier_filtering)
            self.filter_button.setEnabled(False)  # Disable until CSV is loaded
            layout.addWidget(self.filter_button)

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

            # self.plot_button = QPushButton("Show Additional Plot")
            # self.plot_button.clicked.connect(self.show_additional_plot)
            # layout.addWidget(self.plot_button)

        self.setLayout(layout)
        self.data_frame = None

    def load_csv(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)", options=options)
        if fileName:
            data = data_preparation.data_loader(fileName, toi=True)
            print("CSV loaded successfully:", data)
            self.data_frame = data['all'][0]
            self.update_selection_menu()
            self.main_button.setEnabled(True)
            self.filter_button.setEnabled(True)

    def update_selection_menu(self):
        self.selection_menu.clear()
        self.selection_menu.addItems(['Entire Team'])
        self.selection_menu.addItems(self.data_frame.playerName.unique())  # Example options
        self.selection_menu.setEnabled(True)

    def update_parameter_menu (self):
        self.parameter_menu.clear()
        self.parameter_menu.addItems(['Goals Scored','Goals Conceded', 'Custom Matrix'])
        self.parameter_menu.setEnabled(True)

    def selection_changed(self, index):
        # This method is called whenever the selection changes
        self.selected_option = self.selection_menu.currentText()
        print(f"Selected option: {self.selected_option}")

    def parameter_changed (self, index):
        self.selected_parameter =  self.parameter_menu.currentText()
        print (f"Selcted parameter {self.selected_parameter}")

    def preprocess_data_stub(self):
        print(f"MainWindow Reference: {self.main_window}")  # Check if this prints the correct reference

        # First, ensure there is data loaded
        if self.data_frame is not None:
            selected_option = self.selection_menu.currentText()  # Get the currently selected option text

            # Check if the selected option is 'Entire Team'
            if selected_option == 'Entire Team':
                print("Preprocessing entire team data...")
                self.data = self.data_frame  # Use the entire data frame if the entire team is selected
                self.main_window.set_shared_data('data', self.data)

            else:
                print(f"Preprocessing data for {selected_option}...")
                # Assuming 'playerName' is a column in your DataFrame where player names are stored
                self.data = self.data_frame[self.data_frame['playerName'] == selected_option]
                self.main_window.set_shared_data('data', self.data)

            # Now proceed with preprocessing the data
            self.preprocess_data(self.data)
            print("Preprocessing complete")
        else:
            print("No data loaded. Please load a CSV file first.")

    def preprocess_data(self, df):
        binsize = (20, 20)
        maps_stats = {}
        for m in df.matchId.unique():
            maps_stats[m] = preprocessing.preprocess_df(df[df['matchId'] == m], binsize=binsize)
        self.map_stats = maps_stats
        self.main_window.set_shared_data('maps_stats', maps_stats)
        print("Data preprocessed successfully")
        self.heatmap_general()
        self.s_map = np.array([x['statistic'] for x in maps_stats.values()])

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
        print ('Correlation Analsysi Completed')

    def correlation_analysis(self):
        binsize = (20, 20)
        self.processed_s_map = self.main_window.get_shared_data('processed_s_map')
        self.res = static_correlation.perform_correlation_analysis2(self.processed_s_map,
                                                                    self.X,
                                                                    binsize= binsize,
                                                                    contrast = self.contrast,
                                                                    mtc = False,
                                                                    cluster_correction=True)
        self.result_heatmap()


    def outlier_filtering(self, s_map):
        binsize = (20, 20)
        print ("Filtering outliers...")
        self.processed_s_map = preprocessing.outlier_filtering(self.s_map, binsize = binsize)
        self.main_window.set_shared_data('processed_s_map', self.processed_s_map)
        #self.analysis_button.setEnabled(True)

    def heatmap_general(self):
        popup = GraphPopup(self.map_stats, plot_type='general')
        popup.exec_()  # Make the popup modal

    def result_heatmap(self):
        self.map_stats = self.main_window.get_shared_data('maps_stats')
        popup = GraphPopup(self.map_stats, plot_type='result', res=self.res)
        popup.exec_()

    def compute_basic_parameters(self):
        # Placeholder function
        print("Computing basic parameters...")
        self.goals_scored, self.goals_conceded = parameters_creation.match_goals(self.main_window.get_shared_data('data'))
        if len (self.goals_conceded) == len(self.main_window.get_shared_data('maps_stats')):
            self.update_parameter_menu()
            self.correlation_button.setEnabled(True)
        else:
            print('Issues with Design Matrix')

def main():
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

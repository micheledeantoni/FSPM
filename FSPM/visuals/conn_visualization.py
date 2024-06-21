import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
from mplsoccer import Pitch
from FSPM.utilities import conn_data_preparation

def visualize_pvalues(pval_matrix, players, significance_level=0.05):
    # Replace p-values above the significance level with NaN for better visualization
    pval_matrix_filtered = np.where(pval_matrix < significance_level, pval_matrix, np.nan)

    # Avoid taking log of NaN or zero
    with np.errstate(divide='ignore', invalid='ignore'):
        neg_log_pvals = -np.log10(pval_matrix_filtered)
        neg_log_pvals[np.isinf(neg_log_pvals)] = np.nan  # Replace inf with NaN

    # Create a DataFrame for better visualization with labels
    df_pvals = pd.DataFrame(neg_log_pvals, index=players, columns=players)

    # Create the figure and axis for the heatmap
    fig, ax = plt.subplots(figsize=(12, 12))

    # Plot the heatmap with visible grid lines
    sns.heatmap(df_pvals, annot=True, cmap="YlOrRd", cbar=True, linewidths=0.5, linecolor='black', ax=ax)
    ax.set_title('Significant Connections Related to Goals Scored')
    ax.set_xlabel('Pass Recipient')
    ax.set_ylabel('Pass Origin')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)

    # Modify the grid so it is tangent to the squares
    for spine in ax.spines.values():
        spine.set_visible(True)

    fig.tight_layout()
    # Return the figure
    return fig


import ipywidgets as widgets
from IPython.display import display, clear_output
import matplotlib.pyplot as plt
from mplsoccer import Pitch

def create_player_selection_ui(df_passes, handle_player_selection, avg_connectivity_matrix, significant_connections, all_players):
    # Create dropdowns for selecting players
    most_frequent_starting_eleven = conn_data_preparation.get_most_frequent_starting_eleven(df_passes)
    dropdowns = []
    for i in range(11):
        dropdown = widgets.Dropdown(
            options=all_players,
            value=most_frequent_starting_eleven[i],
            description=f'Player {i+1}:'
        )
        dropdowns.append(dropdown)

    # Arrange dropdowns in a grid layout
    UI = widgets.VBox([
        widgets.HBox(dropdowns[:3]),
        widgets.HBox(dropdowns[3:6]),
        widgets.HBox(dropdowns[6:9]),
        widgets.HBox(dropdowns[9:])
    ])

    display(UI)

    # Attach the observer to each dropdown
    for dropdown in dropdowns:
        dropdown.observe(
            lambda change, dp=dropdowns: handle_player_selection(
                change, df_passes, dp, UI, avg_connectivity_matrix, significant_connections, all_players
            ),
            names='value'
        )

    return dropdowns, UI

def handle_player_selection(change, df_passes, dropdowns, UI, avg_connectivity_matrix, significant_connections, all_players):
    selected_players = [dropdown.value for dropdown in dropdowns]
    if len(set(selected_players)) == 11:
        clear_output(wait=True)
        display(UI)
        plot_players_and_significant_connections_mplsoccer(df_passes, selected_players, avg_connectivity_matrix, significant_connections, all_players)

def plot_players_and_significant_connections_mplsoccer(df_passes, selected_players, avg_connectivity_matrix, significant_connections, all_players):
    pitch = Pitch(pitch_type='opta', line_zorder=4,
                  pitch_color='#22312b', line_color='#efefef')
    fig, ax = pitch.draw(figsize=(15, 20))
    fig.set_facecolor('#22312b')

    mean_coordinates = df_passes.groupby('playerName')[['x', 'y']].mean()
    mean_coordinates.columns = ['mean_x', 'mean_y']

    for player in selected_players:
        if player in mean_coordinates.index:
            mean_x = mean_coordinates.loc[player, 'mean_x']
            mean_y = mean_coordinates.loc[player, 'mean_y']
            pitch.scatter(mean_x, mean_y, ax=ax, label=player, s=100, edgecolor='k', color='red', zorder=2)
            ax.text(mean_x, mean_y, player, fontsize=14, ha='center', color='white')

    for i, player_i in enumerate(selected_players):
        for j, player_j in enumerate(selected_players):
            if player_i in mean_coordinates.index and player_j in mean_coordinates.index:
                x_start = mean_coordinates.loc[player_i, 'mean_x']
                y_start = mean_coordinates.loc[player_i, 'mean_y']
                x_end = mean_coordinates.loc[player_j, 'mean_x']
                y_end = mean_coordinates.loc[player_j, 'mean_y']
                if significant_connections[all_players.index(player_i), all_players.index(player_j)]:
                    pitch.lines(x_start, y_start, x_end, y_end, ax=ax, color='green', lw=avg_connectivity_matrix[all_players.index(player_i), all_players.index(player_j)] * 35, alpha=0.9, zorder=1)

    plt.show()

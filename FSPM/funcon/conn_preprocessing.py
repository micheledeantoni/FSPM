from utilities import conn_data_preparation
import numpy as np
import pandas as pd

def normalize_matrix(matrix):
    row_sums = matrix.sum(axis=1, keepdims=True)
    normalized_matrix = np.divide(matrix, row_sums, where=row_sums!=0)
    return normalized_matrix


def calculate_player_time_and_connectivity(df_all_events):
    players_on_field = conn_data_preparation.initialize_starting_players(df_all_events)
    players = list(set(df_all_events['playerName'].dropna().unique()) | set(df_all_events['recipient'].dropna().unique()))
    player_time_on_field = {player: 0 for player in players}
    n_players = len(players)
    connectivity_matrix = np.zeros((n_players, n_players))
    last_active_time = {player: 0 for player in players}
    sub_time = {}

    for index, row in df_all_events.iterrows():
        if row['type'] == 'Pass':
            if pd.notna(row['playerName']) and pd.notna(row['recipient']):
                start_idx = players.index(row['playerName'])
                end_idx = players.index(row['recipient'])
                connectivity_matrix[start_idx, end_idx] += 1
                last_active_time[row['playerName']] = row['expandedMinute']
                last_active_time[row['recipient']] = row['expandedMinute']
        elif row['type'] == 'SubstitutionOff':
            player_off = row['playerName']
            if player_off in players_on_field:
                last_active_time[player_off] = row['expandedMinute']
        elif row['type'] == 'SubstitutionOn':
            player_on = row['playerName']
            sub_time[player_on] = row['expandedMinute']
            last_active_time[player_on] = row['expandedMinute']

    final_time = df_all_events['expandedMinute'].max()
    for player in players:
        player_time_on_field[player] = last_active_time[player] - sub_time.get(player, 0)

    normalized_connectivity_matrix = normalize_matrix(connectivity_matrix)

    return normalized_connectivity_matrix, player_time_on_field

def process_matches(df_all_events):
    match_ids = df_all_events['matchId'].unique()
    all_connectivity_matrices = []
    all_player_times = []
    for match_id in match_ids:
        match_events = df_all_events[df_all_events['matchId'] == match_id]
        conn_matrix, play_time = calculate_player_time_and_connectivity(match_events)
        all_connectivity_matrices.append(conn_matrix)
        all_player_times.append(play_time)
    return all_connectivity_matrices, all_player_times


def align_connectivity_matrices(all_connectivity_matrices, all_player_times, all_players):
    aligned_connectivity_matrices = []
    for conn_matrix, player_times in zip(all_connectivity_matrices, all_player_times):
        aligned_matrix = np.zeros((len(all_players), len(all_players)))
        for i, player_i in enumerate(all_players):
            if player_i in player_times:
                for j, player_j in enumerate(all_players):
                    if player_j in player_times:
                        original_i = list(player_times.keys()).index(player_i)
                        original_j = list(player_times.keys()).index(player_j)
                        aligned_matrix[i, j] = conn_matrix[original_i, original_j]
        aligned_connectivity_matrices.append(aligned_matrix)
    avg_connectivity_matrix =  np.mean(aligned_connectivity_matrices, axis=0)
    return aligned_connectivity_matrices, avg_connectivity_matrix

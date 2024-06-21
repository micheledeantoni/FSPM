import pandas as pd
import networkx as nx

import pandas as pd
import networkx as nx

def compute_pass_network_metrics(filtered_pass_data, min_matches_threshold=6):
    pass_df = filtered_pass_data
    matches = pass_df['matchId'].unique()

    # Create pass counts
    pass_counts = pass_df.groupby(['matchId', 'playerName', 'pass_recipient_name']).size().reset_index(name='pass_count')

    networks = {}

    for match in matches:
        match_data = pass_df[pass_df['matchId'] == match]
        G = nx.DiGraph()

        for _, row in match_data.iterrows():
            player_from = row['playerName']
            player_to = row['pass_recipient_name']
            pass_count = pass_counts[(pass_counts['matchId'] == match) &
                                     (pass_counts['playerName'] == player_from) &
                                     (pass_counts['pass_recipient_name'] == player_to)]['pass_count'].values[0]
            G.add_edge(player_from, player_to, weight=pass_count)

        networks[match] = G

    # Compute network metrics
    metrics = []

    for match, G in networks.items():
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        eigenvector_centrality = nx.eigenvector_centrality(G)
        clustering_coefficient = nx.clustering(G.to_undirected())

        for player in G.nodes():
            metrics.append({
                'matchId': match,
                'player': player,
                'degree_centrality': degree_centrality.get(player, 0),
                'betweenness_centrality': betweenness_centrality.get(player, 0),
                'closeness_centrality': closeness_centrality.get(player, 0),
                'eigenvector_centrality': eigenvector_centrality.get(player, 0),
            })

    # Create DataFrame and normalize numeric columns
    metrics_df = pd.DataFrame(metrics)

    # Filter players based on the number of matches they played
    player_match_counts = metrics_df.groupby('player')['matchId'].nunique()
    players_to_keep = player_match_counts[player_match_counts >= min_matches_threshold].index
    metrics_df = metrics_df[metrics_df['player'].isin(players_to_keep)]

    # Convert appropriate columns to numeric
    numeric_columns = ['degree_centrality', 'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality']
    metrics_df[numeric_columns] = metrics_df[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # Normalize numeric columns for each match
    normalized_df = metrics_df.copy()
    for match in matches:
        match_mask = normalized_df['matchId'] == match
        normalized_df.loc[match_mask, numeric_columns] = (normalized_df.loc[match_mask, numeric_columns] - normalized_df.loc[match_mask, numeric_columns].min()) / (normalized_df.loc[match_mask, numeric_columns].max() - normalized_df.loc[match_mask, numeric_columns].min())

    # Aggregate metrics
    aggregated_metrics = normalized_df.groupby('player').mean().reset_index()
    aggregated_metrics.drop('matchId', axis=1, inplace=True)

    return aggregated_metrics

# Example usage:
# filtered_pass_data = pd.read_csv('your_filtered_pass_data.csv')  # Load your data
# aggregated_metrics = compute_pass_network_metrics(filtered_pass_data, min_matches_threshold=3)
# print(aggregated_metrics)


# Example usage:
# filtered_pass_data = pd.read_csv('your_filtered_pass_data.csv')  # Load your data
# aggregated_metrics = compute_pass_network_metrics(filtered_pass_data)
# print(aggregated_metrics)

def get_players_with_max_metrics(aggregated_metrics):
    # Dictionary to store the results
    max_players = {}

    # Iterate over each column in the DataFrame except the 'player' column
    for column in aggregated_metrics.columns:
        if column != 'player':
            # Find the player with the maximum value in the current column
            max_player = aggregated_metrics.loc[aggregated_metrics[column].idxmax(), 'player']
            max_value = aggregated_metrics[column].max()

            # Store the result in the dictionary
            max_players[column] = (max_player, max_value)

    return max_players

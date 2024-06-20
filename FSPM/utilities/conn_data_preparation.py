from FSPM.utilities import data_preparation
import pandas as pd


# Load and prepare data
def prepare_data(filepath):
    data = data_preparation.data_loader(filepath, toi=True)
    df_passes = data['all'][0]
    df_passes['recipient'] = df_passes['playerName'].shift(-1)
    df_passes['next_teamId'] = df_passes['teamId'].shift(-1)
    df_passes['next_matchId'] = df_passes['matchId'].shift(-1)
    # Ensure no player is marked as passing to themselves
    df_passes['recipient'] = df_passes.apply(
        lambda row: row['recipient'] if (row['teamId'] == row['next_teamId']) and
        (row['matchId'] == row['next_matchId']) and (row['type'] == 'Pass') and
        (row['playerName'] != row['recipient']) else None,
        axis=1
    )

    df_passes = df_passes.drop(columns=['next_teamId', 'next_matchId'])
    df_passes.dropna(subset=['recipient'], inplace=True)

    df_sub_off = data['SubstitutionOff'][0].drop_duplicates()
    df_sub_on = data['SubstitutionOn'][0].drop_duplicates()
    df_all_events = pd.concat([df_passes, df_sub_off, df_sub_on], ignore_index=True)
    df_all_events = df_all_events.sort_values(by=['matchId', 'expandedMinute']).reset_index(drop=True)
    return df_passes, df_all_events

def initialize_starting_players(events_df):
    starting_players = set()
    for player in events_df['playerName']:
        if player not in starting_players and pd.notna(player):
            starting_players.add(player)
        if len(starting_players) == 11:
            break
    return starting_players

# Calculate the most frequent starting eleven
def get_most_frequent_starting_eleven(df):
    starting_elevens = []
    for match_id in df['matchId'].unique():
        match_events = df[df['matchId'] == match_id]
        starting_eleven = match_events['playerName'].dropna().unique()[:11]
        starting_elevens.append(starting_eleven)

    starting_elevens_flat = [player for sublist in starting_elevens for player in sublist]
    most_frequent_starting_eleven = pd.Series(starting_elevens_flat).value_counts().head(11).index.tolist()

    return most_frequent_starting_eleven

import pandas as pd

def show_team_names (match_urls):
    return sorted(list(set([m['home'] for m in match_urls])))

def show_player_names (dataframe):
    id = dataframe.teamId.value_counts().index[0]
    dft = dataframe[dataframe['teamId'] == id]
    return sorted(dft.playerName.dropna().unique())

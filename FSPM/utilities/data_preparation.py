import pandas as pd

def classify_result(row):
    """Classifies the result based on team location and score."""
    home_score, away_score = map(int, row['score'].split(':'))

    if row['h_a'] == 'h':
        if home_score > away_score:
            return 'Win'
        elif home_score < away_score:
            return 'Loss'
        else:
            return 'Draw'
    else:  # Away team
        if away_score > home_score:
            return 'Win'
        elif away_score < home_score:
            return 'Loss'
        else:
            return 'Draw'

def goals_fa(row):
    """Classifies the result based on team location and score."""
    home_score, away_score = map(int, row['score'].split(':'))

    if row['h_a'] == 'h':
        return home_score , away_score
    else:  # Away team
        return away_score , home_score

def add_result_column(df):
    """Adds a result classification column to the DataFrame."""
    df['result_class'] = df.apply(classify_result, axis=1)
    df['goals'] = df.apply(goals_fa, axis=1)
    df['goals_scored'] = df['goals'].apply(lambda x: x[0])
    df['goals_conceded'] = df['goals'].apply(lambda x: x[1])
    return df


def data_organizer(df):
    result_dict = {}
    for activity_type in df['type'].unique():
        filtered_type = df[df['type'] == activity_type]
        successful_df = filtered_type[filtered_type['outcomeType'] == 'Successful']
        unsuccessful_df = filtered_type[filtered_type['outcomeType'] == 'Unsuccessful']
        result_dict[activity_type] = [successful_df, unsuccessful_df, filtered_type]
    result_dict['all'] = [df]
    #remove empty dataframes
    result_dict = {k: v for k, v in result_dict.items() if not all([x.empty for x in v])}

    return result_dict

def data_loader (fpath, toi = False):
    #toi: team of interest
    df = pd.read_csv(fpath)
    if toi:
        id = df.teamId.value_counts().index[0]
        df = df[df['teamId'] == id]
    df = df.dropna(subset=['playerName'])
    df = add_result_column(df)
    return data_organizer(df)

def filter_pass_data_by_top_players(data):
    # Create a backup of the original data
    all_data = data['all'][0]
    pass_data = data['Pass'][0]
    backup_data = all_data.copy()

    # Prepare pass data with recipient names
    pass_data['pass_recipient_name'] = pass_data['playerName'].shift(-1)
    pass_data.dropna(subset=['pass_recipient_name'], inplace=True)

    # Calculate play times
    play_times = []

    for match in backup_data['matchId'].unique():
        match_data = backup_data[backup_data['matchId'] == match].copy()

        for index, row in match_data.iterrows():
            if row['type'] == 'SubstitutionOff':
                play_time = row['expandedMinute']
            elif row['type'] == 'SubstitutionOn':
                play_time = 90 - row['expandedMinute']
            else:
                play_time = 90

            play_times.append({
                'matchId': match,
                'playerName': row['playerName'],
                'play_time': play_time
            })

    # Create a DataFrame for play times
    play_times_df = pd.DataFrame(play_times)

    # Sum play times for each player in each match
    total_play_times = play_times_df.groupby(['matchId', 'playerName'])['play_time'].sum().reset_index()

    # Identify top 11 players for each match
    top_11_players = total_play_times.groupby('matchId').apply(
        lambda x: x.nlargest(11, 'play_time')).reset_index(drop=True)

    # Get list of top 11 players for each match
    top_11_player_names = top_11_players[['matchId', 'playerName']]

    # Filter pass data to include only top 11 players
    filtered_pass_data = pass_data.merge(
        top_11_player_names, how='inner', on=['matchId', 'playerName']
    )
    filtered_pass_data = filtered_pass_data.merge(
        top_11_player_names.rename(columns={'playerName': 'pass_recipient_name'}),
        how='inner', on=['matchId', 'pass_recipient_name']
    )

    return filtered_pass_data

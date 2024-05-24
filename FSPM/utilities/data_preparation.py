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

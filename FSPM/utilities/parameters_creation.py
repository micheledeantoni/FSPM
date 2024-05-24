def match_goals(df):
    goals_conceded = [x[0] for x in df.groupby('matchId').first()[['goals_conceded']].values.astype(int)]
    goals_scored = [x[0] for x in df.groupby('matchId').first()[['goals_scored']].values.astype(int)]
    return goals_scored, goals_conceded

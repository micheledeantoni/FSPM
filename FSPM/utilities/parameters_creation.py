def match_goals(df):
    goals_conceded = [x[0] for x in df.groupby('matchId').first()[['goals_conceded_p']].values.astype(int)]
    goals_scored = [x[0] for x in df.groupby('matchId').first()[['goals_scored_p']].values.astype(int)]
    return goals_scored, goals_conceded

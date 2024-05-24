import pandas as pd
from data import main

league_urls = {'Premier League': 'https://1xbet.whoscored.com/Regions/252/Tournaments/2/England-Premier-League',
 'Championship' : 'https://1xbet.whoscored.com/Regions/252/Tournaments/7/England-Championship',
 'Serie A': 'https://1xbet.whoscored.com/Regions/108/Tournaments/5/Italy-Serie-A',
 'LaLiga': 'https://1xbet.whoscored.com/Regions/206/Tournaments/4/Spain-LaLiga',
 'Bundesliga': 'https://1xbet.whoscored.com/Regions/81/Tournaments/3/Germany-Bundesliga',
 'Ligue 1': 'https://1xbet.whoscored.com/Regions/74/Tournaments/22/France-Ligue-1',
 'Liga Portugal': 'https://1xbet.whoscored.com/Regions/177/Tournaments/21/Portugal-Liga-Portugal',
 'Eredivisie': 'https://1xbet.whoscored.com/Regions/155/Tournaments/13/Netherlands-Eredivisie',
 'Russian Premier League': 'https://1xbet.whoscored.com/Regions/182/Tournaments/77/Russia-Premier-League',
 'Brasileirão': 'https://1xbet.whoscored.com/Regions/31/Tournaments/95/Brazil-Brasileir%C3%A3o',
 'Major League Soccer': 'https://1xbet.whoscored.com/Regions/233/Tournaments/85/USA-Major-League-Soccer',
 'Super Lig': 'https://1xbet.whoscored.com/Regions/225/Tournaments/17/Turkey-Super-Lig',
 'Championship': 'https://1xbet.whoscored.com/Regions/252/Tournaments/7/England-Championship',
 'Premiership': 'https://1xbet.whoscored.com/Regions/253/Tournaments/20/Scotland-Premiership',
 'League One': 'https://1xbet.whoscored.com/Regions/252/Tournaments/8/England-League-One',
 'League Two': 'https://1xbet.whoscored.com/Regions/252/Tournaments/9/England-League-Two',
 'Liga Profesional': 'https://1xbet.whoscored.com/Regions/11/Tournaments/68/Argentina-Liga-Profesional',
 'Jupiler Pro League': 'https://1xbet.whoscored.com/Regions/22/Tournaments/18/Belgium-Jupiler-Pro-League',
 '2. Bundesliga': 'https://1xbet.whoscored.com/Regions/81/Tournaments/6/Germany-2-Bundesliga',
 'Champions League': 'https://1xbet.whoscored.com/Regions/250/Tournaments/12/Europe-Champions-League',
 'Europa League': 'https://1xbet.whoscored.com/Regions/250/Tournaments/30/Europe-Europa-League',
 'FA Cup': 'https://1xbet.whoscored.com/Regions/252/Tournaments/26/England-FA-Cup',
 'League Cup': 'https://1xbet.whoscored.com/Regions/252/Tournaments/29/England-League-Cup',
 'European Championship': 'https://1xbet.whoscored.com/Regions/247/Tournaments/124/International-European-Championship',
 "Women's Super League": 'https://1xbet.whoscored.com/Regions/252/Tournaments/739/England-Women-s-Super-League',
 'Africa Cup of Nations': 'https://1xbet.whoscored.com/Regions/247/Tournaments/104/International-Africa-Cup-of-Nations'}

def get_matches_url (competition, season, comp_urls = league_urls):
    return main.getMatchUrls(competition, season, comp_urls)

def get_team_data (team_name, competition, season):
    print(f"Getting data for {team_name} in {competition} {season}...")
    team_urls = main.getTeamUrls(team=team_name, match_urls=get_matches_url(competition, season))
    ## inside function
    def get_batch_data(urls, batch_size=10):
        all_data = []
        for i in range(0, len(urls), batch_size):
            print(f"Fetching batch starting at index {i}...")
            batch_urls = urls[i:i+batch_size]
            success = False
            attempts = 0
            while not success and attempts < 3:
                try:
                    # Attempt to fetch the data for the current batch
                    batch_data = main.getMatchesData(match_urls=batch_urls)
                    all_data.extend(batch_data)
                    success = True  # Set success to True if the above line does not raise an error
                except Exception as e:
                    print(f"Error retrieving data for batch starting at index {i}: {e}")
                    attempts += 1
                    if attempts == 3:
                        print("Max retries reached for this batch, moving to the next batch.")
        return all_data
    matches_data = get_batch_data(team_urls)  # you can adjust batch size as needed
    print(f"Data for {team_name} in {competition} {season} successfully retrieved.")
    events_ls = [main.createEventsDF(match) for match in matches_data]
    events_list = [main.addEpvToDataFrame(match) for match in events_ls]
    events_dfs = pd.concat(events_list)
    return events_dfs

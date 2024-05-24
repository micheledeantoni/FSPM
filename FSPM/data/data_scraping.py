import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import numpy as np

def collect_match_links(url):
    # Set up Chrome options
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # Initialize the driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    # Initialize WebDriverWait
    wait = WebDriverWait(driver, 5)

    # Accept cookies if necessary
    try:
        cookie_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), \"J'ACCEPTE\")]"))
        )
        cookie_btn.click()
    except TimeoutException:
        print("No cookie acceptance button found, continuing...")

    # List to hold all links
    all_links = []
    previous_page_content = None

    # Loop through pages to collect links
    while True:
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[id^='scoresBtn-']")))
            score_buttons = driver.find_elements(By.CSS_SELECTOR, "a[id^='scoresBtn-']")
            new_links = [btn.get_attribute('href') for btn in score_buttons]
            all_links.extend(new_links)
            current_page_content = driver.find_element(By.TAG_NAME, 'html').get_attribute('innerHTML')
            if current_page_content == previous_page_content:
                print("No change in page content, stopping...")
                break
            previous_page_content = current_page_content
        except TimeoutException:
            print("Failed to find elements with the specified ID pattern.")

        # Navigate to the previous page
        try:
            prev_button = driver.find_element(By.XPATH, '//*[@id="dayChangeBtn-prev"]')
            prev_button.click()
            time.sleep(5)  # Wait for potential page content to load
        except (NoSuchElementException, TimeoutException):
            print("No previous page button found or it's disabled, stopping...")
            break

    # Cleanup
    driver.quit()

    # Return the collected links
    return all_links




def fetch_match_data(url, headers=None, cookies=None):
    """
    Fetch and parse match data from WhoScored.com based on the provided URL.

    Args:
        url (str): The complete URL to fetch the match data.
        headers (dict, optional): HTTP headers to use for the request.
        cookies (dict, optional): Cookies to use for the request.

    Returns:
        tuple: A tuple containing a dictionary of player ID to player names, and a DataFrame of match events.
    """
    id = url.split('/')[-3]
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data, status code: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')
    script_text = next((s.text for s in soup.find_all('script') if 'matchCentreData' in s.text), None)
    if not script_text:
        raise ValueError("Match data script not found in the page.")
    match = re.search(r"matchCentreData: (\{.*?\}),\s*matchCentreEventTypeJson", script_text, re.DOTALL)
    if not match:
        raise ValueError("Failed to extract match data from the script.")

    json_data = json.loads(match.group(1))
    score = json_data['score']
    event_df = json_data_to_df(json_data)
    event_df['matchId'] = id
    event_df['score'] = score
    return event_df

def json_data_to_df(json_data):
    """
    Convert JSON match data to a pandas DataFrame.

    Args:
        json_data (dict): The JSON data extracted from the match page.

    Returns:
        tuple: A tuple containing a dictionary of player IDs to names and the DataFrame of events.
    """
    player_id_name_dict = json_data.get('playerIdNameDictionary', {})
    team_dict = {
        json_data['home']['teamId']: json_data['home']['name'],
        json_data['away']['teamId']: json_data['away']['name']
    }
    h_a_dict = { json_data['home']['teamId']:'h', json_data['away']['teamId']: 'a'
                }


    df = pd.DataFrame(json_data['events'])
    df = clean_event_data(df, team_dict, player_id_name_dict, h_a_dict)
    return  df

def clean_event_data(df, team_dict, player_id_name_dict, h_a_dict):
    """
    Clean and prepare event data.

    Args:
        df (pd.DataFrame): DataFrame of events to clean.
        team_dict (dict): Dictionary of team IDs to team names.
        player_id_name_dict (dict): Dictionary of player IDs to player names.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    df['outcomeType'] = df['outcomeType'].map(lambda x: x['displayName'])
    df['type'] = df['type'].map(lambda x: x['displayName'])
    df['period'] = df['period'].map(lambda x: x['displayName'])
    df['teamName'] = df['teamId'].map(team_dict)
    df['h_a'] = df['teamId'].map(h_a_dict)
    df['playerId'] = df['playerId'].astype(str).str.split('.').str[0]
    df['playerName'] = df['playerId'].map(lambda x: player_id_name_dict.get(x, np.nan))
    df.sort_values(['minute', 'second'], inplace=True)
    return df

def team_parsing (team, urls):
    return [l for l in urls if team in l]

def season_processing (urls):
    df_list = []
    for url in urls:
        try:
            df = fetch_match_data(url)
            df_list.append(df)
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
    return pd.concat(df_list)

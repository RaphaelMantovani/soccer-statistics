import requests, os, json, time
from pprint import pprint
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

load_dotenv()

# Getting API token
url = "https://oauth2.elenasport.io/oauth2/token"
payload = 'grant_type=client_credentials'
headers = {
    'Authorization': os.getenv('API_Key'),
    'Content-Type': 'application/x-www-form-urlencoded'
}

api_response = requests.request("POST", url, headers=headers, data=payload)

api_token = json.loads(api_response.text)["access_token"]

# Establishing headers for further requests
request_authorization = 'Bearer ' + str(api_token)

request_headers = {
    'Authorization': request_authorization
}

# User imputed league parameter
league = input('Select a football (soccer) league: ')
element_id = ''
error_msg = 'Error: Invalid league provided. Check league names at elenasports.io'
league_list = list()


# Function to request leagues from all pages in order to get the selected league's id
def make_request(page_number):
    global element_id, error_msg, league_list
    leagues_request = requests.get('https://football.elenasport.io/v2/leagues', headers=request_headers,
                                   params={'page': str(page_number)})
    leagues_request = leagues_request.json()

    for element in leagues_request['data']:
        if element['nationalLeague'] and (element['name'].upper().replace(' ', '') == league.upper().replace(' ', '')):
            league_list.append(element)
        elif not element['nationalLeague'] and (element['name'] is not None) and (
                element['name'].upper().replace(' ', '') == league.upper().replace(' ', '')):
            element_id = str(element['id'])

    try:
        if not leagues_request['pagination']['hasNextPage']:
            if len(element_id) == 0:
                element_id = error_msg

    except:
        if len(element_id) == 0:
            element_id = error_msg


# Calling the defined function
page_count = 1
while len(element_id) == 0:
    make_request(page_count)
    page_count += 1
    time.sleep(1.5)

# Getting the league id of national leagues
if len(league_list) == 1:
    for comp in league_list:
        element_id = str(comp['id'])
elif len(league_list) > 1:
    country = input("Specify the league's country: ")
    for comp in league_list:
        if comp['countryName'].upper().replace(' ', '') == country.upper().replace(' ', ''):
            element_id = str(comp['id'])

if element_id == error_msg:
    print(element_id)
    os._exit(1)

# Getting a specified season's id
year = input("Select the starting year of the season you would like: ")
season_request = requests.get('https://football.elenasport.io/v2/leagues/' + str(element_id) + '/seasons',
                              headers=request_headers)
season_request = season_request.json()

item_id = ''
for item in season_request['data']:
    if item['start'] == int(year):
        item_id = str(item['id'])

unavailable_data = "Error: Unavailable data for the chosen season. Try a more recent one."
if len(item_id) == 0:
    item_id = unavailable_data
    print(item_id)

if item_id == unavailable_data:
    os._exit(1)

fixtures_df = None
while_condition = False

# Defining a function to request the fixtures' data and store it in a dataframe
def request_fixtures(page):
    global item_id, while_condition, fixtures_df
    fixtures_request = requests.get('https://football.elenasport.io/v2/seasons/' + str(item_id) + '/fixtures',
                                    headers=request_headers, params={'page': str(page)})
    fixtures_request = fixtures_request.json()
    for fixture in fixtures_request['data']:
        del fixture['referees']
        if fixtures_df is None:
            fixtures_df = pd.DataFrame(columns=[k for k, v in fixture.items() if type(v) != dict])
            fixtures_df = fixtures_df.append(fixture, ignore_index=True, sort=False)
        else:
            fixtures_df = fixtures_df.append(fixture, ignore_index=True, sort=False)

    if not fixtures_request['pagination']['hasNextPage']:
        while_condition = True


# Calling the function
number = 1
while not while_condition:
    request_fixtures(number)
    number += 1
    time.sleep(1.5)

pd.set_option('display.max_columns', None)

# Adding a goal difference column to the data frame
fixtures_df['goal_difference'] = (fixtures_df['team_home_90min_goals'] + fixtures_df['team_home_ET_goals']) - \
                                 (fixtures_df['team_away_90min_goals'] + fixtures_df['team_away_ET_goals'])

fixtures_df['home_points'] = [3 if p > 0 else 1 if p == 0 else 0 for p in fixtures_df['goal_difference']]

# Generating a linear regression model to evaluate correlation between home points earned and mean attendance
grouped_df = fixtures_df.groupby('homeName').aggregate({'attendance': 'mean',
                                                        'home_points': 'sum'})
grouped_df = grouped_df.dropna()

LR = LinearRegression()
LR.fit(grouped_df['attendance'].array.reshape(-1, 1), grouped_df['home_points'])
prediction = LR.predict(grouped_df['attendance'].array.reshape(-1, 1))
plt.plot(grouped_df['attendance'], prediction, color='b')
plt.scatter(grouped_df['attendance'], grouped_df['home_points'], color='g', alpha=0.7)
plt.xlabel('mean attendance')
plt.ylabel('total home points')
plt.title('Home points x Attendance')
plt.show()

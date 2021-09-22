import requests, os, json, time
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

url = "https://oauth2.elenasport.io/oauth2/token"
payload = 'grant_type=client_credentials'
headers = {
    'Authorization': os.getenv('API_Key'),
    'Content-Type': 'application/x-www-form-urlencoded'
}

api_response = requests.request("POST", url, headers=headers, data=payload)

api_token = json.loads(api_response.text)["access_token"]
# print(api_token)

request_authorization = 'Bearer ' + str(api_token)

request_headers = {
    'Authorization': request_authorization
}

league = input('Select a football (soccer) league: ')
element_id = ''
error_msg = 'Error: Invalid league provided. Check league names at elenasports.io'
league_list = list()

def make_request(page_number):
    global element_id, error_msg, league_list
    leagues_request = requests.get('https://football.elenasport.io/v2/leagues', headers=request_headers,
                                   params={'page': str(page_number)})
    leagues_request = leagues_request.json()
    #pprint(leagues_request)

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


page_count = 1
while len(element_id) == 0:
    make_request(page_count)
    page_count += 1
    time.sleep(1.5)

if len(league_list) == 1:
    for comp in league_list:
        element_id = str(comp['id'])
elif len(league_list) > 1:
    country = input("Specify the league's country: ")
    for comp in league_list:
            if comp['countryName'].upper().replace(' ', '') == country.upper().replace(' ', ''):
                element_id = str(comp['id'])

print(league_list)

if element_id == error_msg:
    print(element_id)
    os._exit(1)

year = input("Select the starting year of the season you would like: ")
season_request = requests.get('https://football.elenasport.io/v2/leagues/' + str(element_id) + '/seasons',
                              headers=request_headers)
season_request = season_request.json()
# pprint(season_request)

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

stage_request = requests.get('https://football.elenasport.io/v2/seasons/' + item_id + '/stages',
                             headers=request_headers)
stage_request = stage_request.json()

time.sleep(1)

index_id = ''
no_standings = 'Error: Unavailable standings for this competition. Try another one.'
for index in stage_request['data']:
    if index['hasStanding']:
        if len(stage_request['data']) == 1:
            index_id = str(index['id'])
            standings_request = requests.get('https://football.elenasport.io/v2/stages/' + index_id + '/standing',
                                             headers=request_headers)
            standings_request = standings_request.json()
            pprint(standings_request)
        elif len(stage_request['data']) > 1:
            index_id = str(index['id'])
            standings_request = requests.get('https://football.elenasport.io/v2/stages/' + index_id + '/standing',
                                             headers=request_headers)
            standings_request = standings_request.json()
            pprint(standings_request)
            time.sleep(1)

standing_list = list()
if len(index_id) == 0:
    for key in stage_request['data']:
        if not index['hasStanding']:
            standing_list.append(key)

if len(standing_list) >= 1:
    index_id = no_standings
    print(index_id)

if index_id == no_standings:
    os._exit(1)

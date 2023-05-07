import requests
import pandas as pd
from datetime import datetime, timedelta
import pickle
import os
import boto3
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import sklearn


default_start_date = datetime.now() - timedelta(days=1)
default_end_date = datetime.now() + timedelta(days=7)
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['DYNAMODB_TABLE_NAME']
start_date = os.getenv('START_DATE', default_start_date.strftime('%Y-%m-%d'))
end_date = os.getenv('END_DATE', default_end_date.strftime('%Y-%m-%d'))
table = dynamodb.Table(table_name)

def time_string_to_minutes(time_string):
    try:
        time_string=str(time_string)
        minutes, seconds = map(int, time_string.split(':'))
    except:
        minutes=0
        seconds=0

    return minutes * 60 + seconds






def lambda_handler(event, context):
    events_map_df = pd.DataFrame(
        columns=('season', 'penaltyMinutes', 'eventIdx', 'period', 'x', 'y', 'goals_away', 'goals_home',
                 'time_left_in_period', 'epoch_time', 'Home_Shots', 'Away_Shots', 'Home_Faceoffs',
                 'Away_Faceoffs', 'Home_blocked_shots', 'Away_blocked_shots', 'Home_hits', 'Away_hits',
                 'Home_takeaway', 'Away_takeaway', 'Home_giveaway', 'Away_giveaway', 'Home_penalty_minutes',
                 'Away_penalty_minutes', 'penaltySeverity_0', 'penaltySeverity_Bench Minor',
                 'penaltySeverity_Game Misconduct', 'penaltySeverity_Major', 'penaltySeverity_Match',
                 'penaltySeverity_Minor', 'penaltySeverity_Misconduct', 'penaltySeverity_Penalty Shot',
                 'home_1', 'home_2', 'home_3', 'home_4', 'home_5', 'home_6', 'home_7', 'home_8', 'home_9',
                 'home_10', 'home_12', 'home_13', 'home_14', 'home_15', 'home_16', 'home_17', 'home_18',
                 'home_19', 'home_20', 'home_21', 'home_22', 'home_23', 'home_24', 'home_25', 'home_26',
                 'home_28', 'home_29', 'home_30', 'home_52', 'home_53', 'home_54', 'home_55', 'home_7461',
                 'away_1', 'away_2', 'away_3', 'away_4', 'away_5', 'away_6', 'away_7', 'away_8', 'away_9',
                 'away_10', 'away_12', 'away_13', 'away_14', 'away_15', 'away_16', 'away_17', 'away_18',
                 'away_19', 'away_20', 'away_21', 'away_22', 'away_23', 'away_24', 'away_25', 'away_26',
                 'away_28', 'away_29', 'away_30', 'away_52', 'away_53', 'away_54', 'away_55', 'away_7460',
                 'game_type_P', 'game_type_R', 'game_type_WA'))

    single_df = pd.DataFrame(
        columns=('season', 'penaltyMinutes', 'eventIdx', 'period', 'x', 'y', 'goals_away', 'goals_home',
                 'time_left_in_period', 'epoch_time', 'Home_Shots', 'Away_Shots', 'Home_Faceoffs', 'Away_Faceoffs',
                 'Home_blocked_shots', 'Away_blocked_shots', 'Home_hits', 'Away_hits', 'Home_takeaway', 'Away_takeaway',
                 'Home_giveaway', 'Away_giveaway', 'Home_penalty_minutes', 'Away_penalty_minutes', 'penaltySeverity_0',
                 'penaltySeverity_Bench Minor', 'penaltySeverity_Game Misconduct', 'penaltySeverity_Major',
                 'penaltySeverity_Match',
                 'penaltySeverity_Minor', 'penaltySeverity_Misconduct', 'penaltySeverity_Penalty Shot', 'home_1',
                 'home_2', 'home_3',
                 'home_4', 'home_5', 'home_6', 'home_7', 'home_8', 'home_9', 'home_10', 'home_12', 'home_13', 'home_14',
                 'home_15',
                 'home_16', 'home_17', 'home_18', 'home_19', 'home_20', 'home_21', 'home_22', 'home_23', 'home_24',
                 'home_25', 'home_26',
                 'home_28', 'home_29', 'home_30', 'home_52', 'home_53', 'home_54', 'home_55', 'home_7461', 'away_1',
                 'away_2', 'away_3',
                 'away_4', 'away_5', 'away_6', 'away_7', 'away_8', 'away_9', 'away_10', 'away_12', 'away_13', 'away_14',
                 'away_15',
                 'away_16', 'away_17', 'away_18', 'away_19', 'away_20', 'away_21', 'away_22', 'away_23', 'away_24',
                 'away_25', 'away_26',
                 'away_28', 'away_29', 'away_30', 'away_52', 'away_53', 'away_54', 'away_55', 'away_7460',
                 'game_type_P', 'game_type_R',
                 'game_type_WA'))

    special = pd.DataFrame(columns=['eventTypeId', 'description', 'eventIdx', 'period', 'periodTime',
                                    'periodTimeRemaining', 'dateTime', 'goals_away', 'goals_home', 'x', 'y',
                                    'id', 'triCode', 'secondaryType', 'penaltySeverity', 'penaltyMinutes',
                                    'strength_code', 'strength_name', 'gameWinningGoal', 'emptyNet',
                                    'Game_ID', 'game_type', 'season', 'away', 'home', 'date', 'epoch_time',
                                    'Home_Shots', 'Away_Shots', 'Home_Faceoffs', 'Away_Faceoffs',
                                    'Home_blocked_shots', 'Away_blocked_shots', 'Home_hits', 'Away_hits',
                                    'Home_takeaway', 'Away_takeaway', 'Home_giveaway', 'Away_giveaway',
                                    'Home_penalty_minutes', 'Away_penalty_minutes', 'time_left_in_period'])

    games_url = "https://statsapi.web.nhl.com/api/v1/schedule?startDate={}&endDate={}".format(start_date, end_date)

    schedule_response = requests.get(games_url)
    schedule_data = schedule_response.json()
    for date in schedule_data["dates"]:

        for game in date["games"]:

            items = {'Game_ID': int(game["gamePk"]), 'game_type': (game["gameType"]),
                     'season': (game["season"]),
                     'away': (game["teams"]['away']['team']['id']), 'home': (game["teams"]['home']['team']['id']),
                     'date': (date['date'])}


            game_id = (items['Game_ID'])

            events_url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"
            events_response = requests.get(events_url)
            data = events_response.json()
            df = pd.json_normalize(data["liveData"]["plays"]["allPlays"])

            is_empty = df.empty
            items2 = pd.DataFrame(items, index=[0])
            items2['date'] = pd.to_datetime(items2['date'])
            items2['epoch_time'] = items2['date'].apply(lambda dt: int(dt.timestamp()))

            if is_empty == False:
                games_df = pd.concat([df, items2], ignore_index=True)
                new_columns = {col: col.split('.', 1)[-1] for col in games_df.columns}
                games_df = games_df.rename(columns=new_columns)
                new_columns = {col: col.replace('.', '_') for col in games_df.columns}
                games_df = games_df.rename(columns=new_columns)
                games_df = games_df.drop(
                    columns=['players', 'link', 'eventCode', 'event', 'eventId', 'periodType', 'ordinalNum', 'name'])

                games_df['Home_Shots'] = 0
                games_df['Away_Shots'] = 0
                games_df['Home_Faceoffs'] = 0
                games_df['Away_Faceoffs'] = 0
                games_df['Home_blocked_shots'] = 0
                games_df['Away_blocked_shots'] = 0
                games_df['Home_hits'] = 0
                games_df['Away_hits'] = 0
                games_df['Home_takeaway'] = 0
                games_df['Away_takeaway'] = 0
                games_df['Home_giveaway'] = 0
                games_df['Away_giveaway'] = 0
                games_df['Home_penalty_minutes'] = 0
                games_df['Away_penalty_minutes'] = 0


                for index, row in games_df.iterrows():

                    if row['eventIdx'] == 0:
                        pass
                    else:
                        games_df['home'] = items2['home'][0]
                        games_df['away'] = items2['away'][0]
                        games_df['season'] = items2['season'][0]
                        games_df['date'] = items2['date'][0]
                        games_df['epoch_time'] = items2['epoch_time'][0]
                        games_df['game_type'] = items2['game_type'][0]
                        games_df['Game_ID'] = items2['Game_ID'][0]

                        event_id = row['eventIdx']
                        previous = games_df.loc[index - 1]
                        Homeshot = previous['Home_Shots']
                        Awayshot = previous['Away_Shots']
                        Home_faceoff = previous['Home_Faceoffs']
                        Away_faceoff = previous['Away_Faceoffs']
                        Home_Blocked = previous['Home_blocked_shots']
                        Away_Blocked = previous['Away_blocked_shots']
                        Home_Hits = previous['Home_hits']
                        Away_Hits = previous['Away_hits']
                        Home_tw = previous['Home_takeaway']
                        Away_tw = previous['Away_takeaway']
                        Home_gw = previous['Home_giveaway']
                        Away_gw = previous['Away_giveaway']
                        Home_pim = previous['Home_penalty_minutes']
                        Away_pim = previous['Away_penalty_minutes']
                        if (row['eventTypeId']) == 'SHOT' or (row['eventTypeId']) == 'MISSED_SHOT':
                            if row['id'] == items2['home'][0]:
                                Homeshot += 1
                            else:
                                Awayshot += 1

                        elif (row['eventTypeId']) == 'FACEOFF':
                            if row['id'] == items2['home'][0]:
                                Home_faceoff += 1
                            else:
                                Away_faceoff += 1

                        elif (row['eventTypeId']) == 'BLOCKED_SHOT':
                            if row['id'] == items2['home'][0]:
                                Home_Blocked += 1
                            else:
                                Away_Blocked += 1

                        elif (row['eventTypeId']) == 'TAKEAWAY':
                            if row['id'] == items2['home'][0]:
                                Home_tw += 1
                            else:
                                Away_tw += 1

                        elif (row['eventTypeId']) == 'HIT':
                            if row['id'] == items2['home'][0]:
                                Home_Hits += 1
                            else:
                                Away_Hits += 1

                        elif (row['eventTypeId']) == 'GIVEAWAY':
                            if row['id'] == items2['home'][0]:
                                Home_gw += 1
                            else:
                                Away_gw += 1

                        elif (row['eventTypeId']) == 'PENALTY':
                            if row['id'] == items2['home'][0]:
                                Home_pim += row['penaltyMinutes']
                            else:
                                Away_pim += row['penaltyMinutes']

                        else:
                            pass
                        games_df.at[index, 'Home_Shots'] = Homeshot
                        games_df.at[index, 'Away_Shots'] = Awayshot
                        games_df.at[index, 'Home_Faceoffs'] = Home_faceoff
                        games_df.at[index, 'Away_Faceoffs'] = Away_faceoff
                        games_df.at[index, 'Home_blocked_shots'] = Home_Blocked
                        games_df.at[index, 'Away_blocked_shots'] = Away_Blocked
                        games_df.at[index, 'Home_hits'] = Home_Hits
                        games_df.at[index, 'Away_hits'] = Away_Hits
                        games_df.at[index, 'Home_takeaway'] = Home_tw
                        games_df.at[index, 'Away_takeaway'] = Away_tw
                        games_df.at[index, 'Home_giveaway'] = Home_gw
                        games_df.at[index, 'Away_giveaway'] = Away_gw
                        games_df.at[index, 'Home_penalty_minutes'] = Home_pim
                        games_df.at[index, 'Away_penalty_minutes'] = Away_pim
                        games_df['time_left_in_period'] = games_df['periodTimeRemaining'].apply(time_string_to_minutes)



            else:
                items3 = pd.get_dummies(items2, columns=['home', 'away', 'game_type'], dtype=float)
                items4 = pd.concat([single_df, items3], ignore_index=True)
                items4 = items4.fillna(0)
                items4['home'] = items2['home'][0]
                items4['away'] = items2['away'][0]
                items4['description'] = 'Placeholder Game Schedule'
                events_map_df = pd.concat([events_map_df, items4], axis=0, ignore_index=True)

            special = pd.concat([special, games_df], axis=0, ignore_index=True)

    special = special.drop_duplicates()
    dummies = pd.get_dummies(special, columns=['home', 'away', 'game_type', 'penaltySeverity'], dtype=float)
    special_home = pd.concat([special['home'], dummies], axis=1)
    special = pd.concat([special['away'], special_home], axis=1)

    special = pd.concat([single_df, special], ignore_index=True)

    special = pd.concat([single_df, special], axis=0, ignore_index=True)

    special = pd.concat([events_map_df, special], axis=0, ignore_index=True)

    special = special.fillna(0)
    special = special.drop_duplicates()
    special = special.drop(columns=['dateTime', 'eventTypeId', 'emptyNet', 'gameWinningGoal', 'id'], axis=1)

    train_special = special.drop(
        columns=['periodTimeRemaining', 'home', 'strength_code', 'Game_ID', 'periodTime', 'secondaryType',
                 'strength_name', 'triCode', 'date', 'away', 'description'], axis=1)
    train_special = train_special.sort_index(axis=1)
    with open("scalar_model.pkl", "rb") as file:
        scalar = pickle.load(file)

    x_test = scalar.transform(train_special)

    with open("logreg.pkl", "rb") as f:
        loaded_model = pickle.load(f)
    predictions = loaded_model.predict(x_test)

    special['prediction'] = predictions
    special.drop(special.iloc[:, 32:98], axis=1,inplace=True)

    datas = special.to_dict(orient='records')
    for datum in datas:
        table.put_item(Item=datum)

    print('done')

import json
import boto3
import requests
import os
from datetime import datetime, timedelta


default_start_date = datetime.now() - timedelta(days=1000)
default_end_date = datetime.now()
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['DYNAMODB_TABLE_NAME']
start_date = os.getenv('START_DATE', default_start_date.strftime('%Y-%m-%d'))
end_date = os.getenv('END_DATE', default_end_date.strftime('%Y-%m-%d'))

table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    #setup code
    url = "https://statsapi.web.nhl.com/api/v1/schedule?startDate={}&endDate={}".format(start_date, end_date)
    schedule_response = requests.get(url)
    schedule_data = schedule_response.json()

    for date in schedule_data["dates"]:
        for game in date["games"]:
            if (game["gameType"]) == 'A' or (game["gameType"]) == 'PR':
                pass
            else:
                items = {'Game_ID': (game["gamePk"]), 'game_type': (game["gameType"]), 'season': (game["season"]),
                         'away': (game["teams"]['away']['team']['id']), 'home': (game["teams"]['home']['team']['id'])}
                table.put_item(Item=items)


    return {
        'statusCode': 200,
        'body': json.dumps('Data successfully written to DynamoDB')
    }

if __name__ == '__main__':
    lambda_handler(None, None)

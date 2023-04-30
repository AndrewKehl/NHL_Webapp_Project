import json
import boto3
import requests
import os
from datetime import datetime, timedelta

default_start_date = datetime.now() - timedelta(days=7)
default_end_date = datetime.now() + timedelta(days=7)
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['DYNAMODB_TABLE_NAME']
start_date = os.getenv('START_DATE', default_start_date.strftime('%Y-%m-%d'))
end_date = os.getenv('END_DATE', default_end_date.strftime('%Y-%m-%d'))

table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    url = "https://statsapi.web.nhl.com/api/v1/schedule?startDate={}&endDate={}".format(start_date, end_date)
    print("Scraping {}".format(url))
    response = requests.get(url).json()

    for date_obj in response['dates']:
        date = date_obj['date']
        for game in date_obj['games']:
            gamePk = game['gamePk']
            item = {
                'date': date,
                'gameId': str(gamePk)
            }
            table.put_item(Item=item)

    return {
        'statusCode': 200,
        'body': json.dumps('Data successfully written to DynamoDB')
    }

if __name__ == '__main__':
    lambda_handler(None, None)

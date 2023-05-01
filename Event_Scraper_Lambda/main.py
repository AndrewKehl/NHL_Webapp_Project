import json
import boto3
import requests
import os

dynamodb = boto3.resource('dynamodb')
in_table_name = os.environ['IN_DYNAMODB_TABLE_NAME']
out_table_name = os.environ['OUT_DYNAMODB_TABLE_NAME']
in_table = dynamodb.Table(in_table_name)
out_table = dynamodb.Table(out_table_name)


def get_game_data(game_id):
    url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"
    response = requests.get(url)
    return response.json()

def insert_items_to_dynamodb(items, table_name):
    table = dynamodb.Table(table_name)
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

def lambda_handler(event, context):

    # Scan the table and retrieve all items
    response = in_table.scan()
    items = response['Items']

    # Keep scanning if there are more items to retrieve
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    # Retrieve and append NHL API data to each DynamoDB item
    extended_items = []
    for item in items:
        game_id = item['Game_ID']
        game_data = get_game_data(game_id)

        for record in game_data['liveData']['plays']['allPlays']:
            uid = f"{game_id}_{record['event']['eventID']}"
            record.update(item)
            record['UID'] = uid
            extended_items.append(record)

    # Insert the extended items into the 'nhl_events' DynamoDB table
    insert_items_to_dynamodb(extended_items, out_table)

    # Print a confirmation message
    print(f"Inserted {len(extended_items)} items into the 'nhl_events' table.")

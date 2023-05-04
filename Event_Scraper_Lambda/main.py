import json
import boto3
import requests
import os
import time
import sys
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
in_table_name = os.environ['IN_DYNAMODB_TABLE_NAME']
out_table_name = os.environ['OUT_DYNAMODB_TABLE_NAME']
in_table = dynamodb.Table(in_table_name)
out_table = dynamodb.Table(out_table_name)

def float_to_decimal(data):
    if isinstance(data, list):
        return [float_to_decimal(item) for item in data]
    elif isinstance(data, dict):
        return {key: float_to_decimal(value) for key, value in data.items()}
    elif isinstance(data, float):
        return Decimal(str(data))
    else:
        return data

def get_game_data(game_id, retries=3):
    url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"

    for i in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error while fetching game data for Game_ID {game_id}: {e}")
            if i < retries - 1:
                time.sleep(2 ** i)  # Exponential backoff
            else:
                raise

def insert_items_to_dynamodb(items, table_name):
    # Add this line to print the total size of items in bytes
    #print(f"Total size of items being inserted: {sys.getsizeof(items)} bytes")

    with out_table.batch_writer() as batch:
        for item in items:
            # Add this line to print each item being inserted
            #print(f"Inserting item: {item}")

            batch.put_item(Item=item)

def lambda_handler(event, context):

    # Scan the table and retrieve all items
    response = in_table.scan()
    items = response['Items']

    # Keep scanning if there are more items to retrieve
    while 'LastEvaluatedKey' in response:
        response = in_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    # Retrieve and append NHL API data to each DynamoDB item
    extended_items = []

    for item in items[750:2000]:
        game_id = item['Game_ID']
        game_data = get_game_data(game_id)

        for record in game_data['liveData']['plays']['allPlays']:
            uid = f"{game_id}_{record['about']['eventIdx']}"
            record.update(item)
            record['UID'] = uid
            record = float_to_decimal(record)  # Add this line to convert float values to Decimal types
            extended_items.append(record)

    # Insert the extended items into the 'nhl_events' DynamoDB table
    insert_items_to_dynamodb(extended_items, out_table)

    # Print a confirmation message
    print(f"Inserted {len(extended_items)} items into the 'nhl_events' table.")

import json
import boto3
import requests

table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    teams_url = "https://statsapi.web.nhl.com/api/v1/teams"
    teams_response = requests.get(teams_url)
    teams_data = teams_response.json()
    for i in teams_data['teams']:
        tid = (i['id'])
        name = (i['name'])
        team = (i['teamName'])
        abb = (i['abbreviation'])
        location = (i['locationName'])
        division = (i['division']['name'])
        conf = (i['conference']['name'])
        inception = (i['firstYearOfPlay'])
        logo_url = f'https://www-league.nhlstatic.com/images/logos/teams-current-primary-light/{i}.svg'

        items = {'Team_ID': str(i['id']),'Name': (i['name']), 'team': (i['teamName']),
                'abbreviation': (i['abbreviation']), 'location': (i['locationName']),
                 'division': (i['division']['name']), 'conf': (i['conference']['name']),
                 'inception': (i['firstYearOfPlay']),
                 'logo_url': f'https://www-league.nhlstatic.com/images/logos/teams-current-primary-light/{i}.svg'}
        table.put_item(Item=items)


    return {
        'statusCode': 200,
        'body': json.dumps('Data successfully written to DynamoDB')
    }

if __name__ == '__main__':
    lambda_handler(None, None)

import os
import pandas as pd
import boto3
from functools import wraps
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, url_for, session, render_template

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
prediction_table = dynamodb.Table('predicted_events')
teams_table = dynamodb.Table('nhl_teams')

predict_response = prediction_table.scan()
predict_items = predict_response['Items']

teams_response = teams_table.scan()
teams_items = teams_response['Items']

predicted_events_df = pd.DataFrame(predict_items)
nhl_teams_df = pd.DataFrame(teams_items)

# Get the highest eventIdx for each game
max_events_df = predicted_events_df.groupby('Game_ID', as_index=False)['eventIdx'].max()

# Merge the highest eventIdx data with the original dataframe
merged_df = pd.merge(max_events_df, predicted_events_df, on=['Game_ID', 'eventIdx'], how='left')

# Replace team IDs with team abbreviations
merged_df['home'] = merged_df['home'].apply(lambda x: nhl_teams_df.loc[nhl_teams_df['Team_ID'] == x, 'abbreviation'].values[0])
merged_df['away'] = merged_df['away'].apply(lambda x: nhl_teams_df.loc[nhl_teams_df['Team_ID'] == x, 'abbreviation'].values[0])

# Initialize the server
server = Flask(__name__)
server.secret_key = os.environ.get('SERVER_SECRET_KEY', 'secret-key')

oauth = OAuth(server)
app = dash.Dash(__name__, server=server, url_base_pathname='/dash/')

# Define the layout of the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.H1('NHL Predicted Events'),

    html.Div(id='table-container')
])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('user', None)
        if user:
            return f(*args, **kwargs)
        return render_template('login.html')

    return decorated_function

@server.route('/google/')
def google():
    # Google Oauth Config
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

    # Redirect to google_auth function
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@server.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    session['user'] = token['userinfo']
    return redirect('/')

@server.route('/')
@login_required
def default_path():
    return redirect("/dash/", code=302)

@server.route('/logout')
def logout():
    session.pop('user', None)
    return

import os
import pandas as pd
import boto3
from functools import wraps
import dash
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

    html.H3('Select Date(s):'),
    dcc.Dropdown(
        id='date-dropdown',
        options=[{'label': i, 'value': i} for i in predicted_events_df['date'].unique()],
        multi=True,
        value=[predicted_events_df['date'].min()]
    ),

    html.H3('Select Game(s):'),
    dcc.Dropdown(
        id='game-dropdown',
        options=[{'label': i, 'value': i} for i in predicted_events_df['Game_ID'].unique()],
        multi=True
    ),

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
    return redirect('/')


# Callback to update table
@app.callback(
    Output('table-container', 'children'),
    [Input('date-dropdown', 'value'),
     Input('game-dropdown', 'value')]
)
def update_table(date_filter, game_filter):
    filtered_df = predicted_events_df

    if date_filter:
        filtered_df = filtered_df[filtered_df['date'].isin(date_filter)]

    if game_filter:
        filtered_df

if __name__ == '__main__':
    app.run_server(debug=True)


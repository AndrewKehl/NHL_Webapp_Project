import os
from functools import wraps
import boto3
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from authlib.integrations.flask_client import OAuth
from dash.dependencies import Input, Output
from flask import Flask, redirect, url_for, session, render_template

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
prediction_table = dynamodb.Table('predicted_events')
teams_table = dynamodb.Table('nhl_teams')

predict_response = prediction_table.scan()
predict_items = predict_response['Items']

teams_response = teams_table.scan()
teams_items = teams_response['Items']

# Convert data to pandas DataFrames
nhl_teams_df = pd.DataFrame(teams_items)
predicted_events_df = pd.DataFrame(predict_items)

# Initialize the server
server = Flask(__name__)
server.secret_key = os.environ.get('SERVER_SECRET_KEY', 'secret-key')

oauth = OAuth(server)
app = dash.Dash(__name__, server=server, url_base_pathname='/dash/')

# Define the layout of the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.H1('NHL Schedules'),
    html.Div([
        html.Label('Sort by date:'),
        dcc.Dropdown(
            id='date-dropdown',
            options=[{'label': date, 'value': date} for date in predicted_events_df['date'].unique()],
            multi=True
        ),
        html.Label('Sort by game:'),
        dcc.Dropdown(
            id='game-dropdown',
            options=[{'label': game_id, 'value': game_id} for game_id in predicted_events_df['Game_ID'].unique()],
            multi=True
        ),
        html.Br(),
        html.Div(id='table-container')
    ]),
])


# Callback to update table
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
        filtered_df = filtered_df[filtered_df['Game_ID'].isin(game_filter)]

    filtered_df = filtered_df.sort_values(by='eventIdx', ascending=False)

    filtered_df['away'] = filtered_df['away'].apply(lambda x: nhl_teams_df.loc[nhl_teams_df['Team_ID'] == x, 'abbreviation'].values[0])
    filtered_df['home'] = filtered_df['home'].apply(lambda x: nhl_teams_df.loc[nhl_teams_df['Team_ID'] == x, 'abbreviation'].values[0])

    # Select only the desired columns
    filtered_df = filtered_df[['home_goals', 'away_goals', 'home', 'away', 'description']]

    return html.Table([
        html.Thead([
            html.Tr([html.Th(col) for col in filtered_df.columns])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(filtered_df.iloc[i][col]) for col in filtered_df.columns
            ]) for i in range(len(filtered_df))
        ])
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
    # Get client_id and client_secret from environment variables
    # For developement purpose you can directly put it
    # here inside double quotes
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


@server.route('/quack')
def quack():
    return 'hello'

@server.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# Define app callback
@app.callback(Output('predicted_events', 'children'),
              Input('interval-component', 'n_intervals'))
def update_schedule(n):
    global predicted_events

    # Retrieve all items from DynamoDB table
    response = predicted_events.scan()
    items = response.get('Items')

    # Create list of items
    schedule_list = [
        html.Li(f"{item['home']} vs {item['away']} on {item['date']}")
        for item in items
    ]

    return schedule_list


@app.callback(Output('page-content', 'children'), #this changes the content
              [Input('url', 'pathname')]) #this listens for the url in use
def display_dash(pathname):
    user = dict(session).get('user', None)
    if user is None:
        return (dcc.Location(id="redirect", pathname="/"))

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)



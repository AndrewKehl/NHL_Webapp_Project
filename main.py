import dash
import boto3
import os
from flask import Flask, redirect, url_for, session, render_template
from functools import wraps
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output
from authlib.integrations.flask_client import OAuth
import pandas as pd
import requests

# Load Iris dataset
df = px.data.iris()

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
schedulesTable = dynamodb.Table('nhl-schedules')

# Initialize the server
server = Flask(__name__)
server.secret_key = os.environ.get('SERVER_SECRET_KEY', 'secret-key')
# server.config['SERVER_NAME'] = 'localhost:8050'

oauth = OAuth(server)
app = dash.Dash(__name__, server=server, url_base_pathname='/dash/')

# Define the layout of the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # this locates this structure to the url
    html.Div(id='page-content'),
    html.H1('NHL Schedules'),
    html.Ul(id='schedule-list'),
    html.H1('Iris Dataset'),
    dcc.Graph(
        id='scatter-plot',
        figure={
            'data': [
                {'x': df[df['species'] == 'setosa']['sepal_width'], 'y': df[df['species'] == 'setosa']['sepal_length'],
                 'type': 'scatter', 'mode': 'markers', 'name': 'Setosa'},
                {'x': df[df['species'] == 'versicolor']['sepal_width'],
                 'y': df[df['species'] == 'versicolor']['sepal_length'], 'type': 'scatter', 'mode': 'markers',
                 'name': 'Versicolor'},
                {'x': df[df['species'] == 'virginica']['sepal_width'],
                 'y': df[df['species'] == 'virginica']['sepal_length'], 'type': 'scatter', 'mode': 'markers',
                 'name': 'Virginica'}
            ],
            'layout': {
                'title': 'NHL stuff continuously deployed',
                'xaxis': {'title': 'Sepal Width'},
                'yaxis': {'title': 'Sepal Length'}
            }
        }
    ),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # in milliseconds
        n_intervals=0
    )
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
@app.callback(Output('schedule-list', 'children'),
              Input('interval-component', 'n_intervals'))
def update_schedule(n):
    global schedulesTable

    # Retrieve all items from DynamoDB table
    response = schedulesTable.scan()
    items = response.get('Items')

    # Create list of items
    schedule_list = [
        html.Li(f"{item['home_team']} vs {item['away_team']} on {item['date']}")
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
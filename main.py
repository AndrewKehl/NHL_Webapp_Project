import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

# Load Iris dataset
df = px.data.iris()

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1('Iris Dataset'),
    dcc.Graph(
        id='scatter-plot',
        figure={
            'data': [
                {'x': df[df['species'] == 'setosa']['sepal_width'], 'y': df[df['species'] == 'setosa']['sepal_length'], 'type': 'scatter', 'mode': 'markers', 'name': 'Setosa'},
                {'x': df[df['species'] == 'versicolor']['sepal_width'], 'y': df[df['species'] == 'versicolor']['sepal_length'], 'type': 'scatter', 'mode': 'markers', 'name': 'Versicolor'},
                {'x': df[df['species'] == 'virginica']['sepal_width'], 'y': df[df['species'] == 'virginica']['sepal_length'], 'type': 'scatter', 'mode': 'markers', 'name': 'Virginica'}
            ],
            'layout': {
                'title': 'NHL stuff continuously deployed',
                'xaxis': {'title': 'Sepal Width'},
                'yaxis': {'title': 'Sepal Length'}
            }
        }
    )
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)

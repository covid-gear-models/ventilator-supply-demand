import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from datetime import datetime
from model import run_SEIR

# Step 1. Launch the application
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Step 2. Import the dataset
# TODO: build interactivity with callbacks
FL_population = 21_992_985
population = FL_population
intensive_units = 5_604  # your country
date_of_first_infection = datetime.strptime('02-01-2020', '%m-%d-%Y')  # an estimate is fine
date_of_lockdown = datetime.strptime('04-01-2020', '%m-%d-%Y')

df = run_SEIR(population, intensive_units, date_of_first_infection, date_of_lockdown)

print(df.head())

# Step 3. Create a plotly figure
groups = df.groupby(by='type')
data = []
colors = ['red', 'blue', 'green', 'yellow', 'cyan']

for group, dataframe in groups:
    dataframe = dataframe.sort_values(by=['date'])
    trace = go.Scatter(x=dataframe['date'],
                       y=dataframe['count'],
                       marker=dict(color=colors[len(data)]),
                       name=group)
    data.append(trace)

layout = go.Layout(xaxis={'title': 'Time'},
                   yaxis={'title': 'count'},
                   margin={'l': 40, 'b': 40, 't': 50, 'r': 50},
                   hovermode='closest')

figure = go.Figure(data=data, layout=layout)
figure.update_layout(yaxis_type="log")

# figure.show()

# Step 4. Create a Dash layout
app.layout = html.Div([
    dcc.Graph(id='plot_id', figure=figure)
])

# Step 5. Add callback functions


if __name__ == '__main__':
    app.run_server(debug=True)

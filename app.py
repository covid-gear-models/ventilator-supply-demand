import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output

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

colors = ['red', 'blue', 'green', 'yellow', 'cyan']

data = []
groups = df.groupby(by='type')

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
app.layout = html.Div(children=[
    dcc.Input(id='population', value='330000000', type='text'),
    dcc.Input(id='date-of-lockdown', value='03-15-2020', type='text'),
    dcc.Graph(id='line-plot', figure=figure),
    html.Div(id='my-div'),
])


# Step 5. Add callback functions
@app.callback(
    Output(component_id='my-div', component_property='children'),
    [Input(component_id='population', component_property='value')],
)
def update_output_div(input_value):
    return f'The population is: "{input_value}"'

@app.callback(
    Output(component_id='line-plot', component_property='figure'),
    [Input(component_id='population', component_property='value')],
)
def update_line_plot(pop):
    try:
        pop = int(pop)
    except ValueError:
        print('Non-integer supplied as population'
              '')
    df = run_SEIR(pop, intensive_units, date_of_first_infection, date_of_lockdown)
    groups = df.groupby(by='type')

    data = []
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

    return figure

if __name__ == '__main__':
    app.run_server(debug=True)

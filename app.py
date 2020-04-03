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


# Step 2. Create a Dash layout
app.layout = html.Div(children=[
    html.Label('Population'),
    dcc.Input(id='population', value='330000000', type='text'),
    html.Label('Date of first infection'),
    dcc.Input(id='date-of-first-infection', value='01-15-2020', type='text'),
    html.Label('Date when social distancing begins'),
    dcc.Input(id='date-of-lockdown', value='03-15-2020', type='text'),
    html.Label('Number of intensive units available'),
    dcc.Input(id='intensive-units', value='5,000', type='text'),
    dcc.Graph(id='line-plot'),
    html.Div(id='my-div'),
])


@app.callback(
    Output(component_id='my-div', component_property='children'),
    [Input(component_id='population', component_property='value')],
)
def update_output_div(input_value):
    return f'The population is: "{input_value}"'


@app.callback(
    Output(component_id='line-plot', component_property='figure'),
    [Input(component_id='population', component_property='value'),
     Input(component_id='date-of-first-infection', component_property='value'),
     Input(component_id='date-of-lockdown', component_property='value'),
     Input(component_id='intensive-units', component_property='value')],
)
# Step 3. Run the model in a callback function
def update_line_plot(pop, date_of_first_infection, date_of_lockdown, intensive_units):

    intensive_units = intensive_units.replace(',', '')
    try:
        pop = int(pop.replace(',', ''))
    except ValueError:
        print('Non-integer supplied as population.')

    try:
        intensive_units = int(intensive_units.replace(',', ''))
    except ValueError:
        print('Non-integer supplied for intensive units.')

    try:
        date_of_first_infection = datetime.strptime(date_of_first_infection, '%m-%d-%Y')
    except ValueError:
        print('Bad date supplied for date of first infection.')

    try:
        date_of_lockdown = datetime.strptime(date_of_lockdown, '%m-%d-%Y')
    except ValueError:
        print('Bad date supplied for date of lockdown.')

    df = run_SEIR(pop, intensive_units, date_of_first_infection, date_of_lockdown)
    groups = df.groupby(by='type')

    colors = ['red', 'blue', 'green', 'yellow', 'cyan']
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

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from datetime import datetime
from model import run_SEIR

# Step 1. Launch the application
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = dash.Dash(__name__, )

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=external_stylesheets
)

# Step 2. Create a Dash layout
layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
)

app.layout = html.Div(
    children=[
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing 
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("necsi-logo.png"),
                            id="NECSI-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Corona Virus Ventilator Supply & Demand",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "Subtitle here", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("Learn More", id="learn-more-button"),
                            href="https://plot.ly/dash/pricing/",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(  # row 2
            [
                html.Div(  # left col
                    [
                        html.Label('Population'),
                        dcc.Input(id='population', value='10000000', type='number'),
                        html.Label('Date of first infection'),
                        dcc.Input(id='date-of-first-infection', value='01-15-2020', type='text'),
                        html.Label('Date when social distancing begins'),
                        dcc.Input(id='date-of-lockdown', value='03-15-2020', type='text'),
                    ],
                    className="pretty_container four columns",
                    id="demographic-options",
                ),
                html.Div(  # middle col
                    [
                        html.Label('Number of intensive units available'),
                        dcc.Input(id='intensive-units', value='5000', type='number'),
                        html.Label('Mean number of days person stays in ICU'),
                        dcc.Input(id='mean_days_icu', value='5', type='number'),
                        # ventilators
                        html.Label('Number of ventilators available to start.'),
                        dcc.Input(id='vents-units-start', value='5000', type='number'),
                        html.Label('Number of ventilators in first shipment.'),
                        dcc.Input(id='vents-units-shipment-1', value='200', type='number'),
                        html.Label('Date of first shipment.'),
                        dcc.Input(id='vents-date-shipment-1', value='03-20-2020', type='text'),
                    ],
                    className="pretty_container four columns",
                    id="medical-options",
                ),
                html.Div(  # middle col
                    [
                        html.Label('Switch to linear scale.'),
                        daq.ToggleSwitch(
                            id='y-axis-toggle',
                            value=False
                        ),
                    ],
                    className="pretty_container four columns",
                    id="visual-options",
                ),
            ],
            className="row flex-display",
        ),
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
     # intensive care units
     Input(component_id='intensive-units', component_property='value'),
     Input(component_id='mean_days_icu', component_property='value'),
     # ventilators
     Input(component_id='vents-units-start', component_property='value'),
     Input(component_id='vents-units-shipment-1', component_property='value'),
     Input(component_id='vents-date-shipment-1', component_property='value'),
     # vis
     Input(component_id='y-axis-toggle', component_property='value'),
     ],
)
# Step 3. Run the model in a callback function
def update_line_plot(pop, date_of_first_infection, date_of_lockdown,
                     intensive_units, mean_days_icu,
                     vents_units_start, vents_units_sh1, vents_date_sh1,
                     y_axis_toggle):



    pop, intensive_units, mean_days_icu, vents_units_start, vents_units_sh1 = int(pop), int(intensive_units), \
                                                           int(mean_days_icu), int(vents_units_start), int(vents_units_sh1)

    try:
        date_of_first_infection = datetime.strptime(date_of_first_infection, '%m-%d-%Y')
    except ValueError:
        print('Bad date supplied for date of first infection.')

    try:
        date_of_lockdown = datetime.strptime(date_of_lockdown, '%m-%d-%Y')
    except ValueError:
        print('Bad date supplied for date of lockdown.')

    try:
        vents_date_sh1 = datetime.strptime(vents_date_sh1, '%m-%d-%Y')
    except ValueError:
        print('Bad date supplied for date of first vents shipment.')

    if y_axis_toggle == False:
        y_axis_scale = 'log'
    else:
        y_axis_scale = 'linear'

    df = run_SEIR(pop, date_of_first_infection, date_of_lockdown,
                  intensive_units, mean_days_icu,
                  vents_units_start, vents_units_sh1, vents_date_sh1,
                  )

    groups = df.groupby(by='type')

    colors = ['red', 'blue', 'orange', 'green', 'cyan']
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
                       hovermode='closest',
                       width=1200,
                       height=800)

    figure = go.Figure(data=data, layout=layout)
    figure.update_layout(yaxis_type=f"{y_axis_scale}")

    return figure


if __name__ == '__main__':
    app.run_server(debug=True)

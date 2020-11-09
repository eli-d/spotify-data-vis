import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from dash.dependencies import Input, Output, State
from datetime import datetime as dt
import colorcet as cc
import bar_chart_race as bcr


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

#Import dataframes
df = pd.read_csv('data_clean.csv')
df_global = pd.read_csv('data_global.csv')
df_race = pd.read_csv('data_dates.csv',index_col='index')
artists_df = pd.read_csv('~/Uni/Grand-Challenges/Project 1/Data/artist_count.csv')
artist_streams = pd.read_csv('artist_streams.csv')
song_streams = pd.read_csv('song_streams.csv')
artist_weightings_df = pd.read_csv('artist_weightings.csv',index_col=0)
codes = pd.read_csv('country_codes.csv')

maps_template = 'Country: %{location}<br>Streams: %{z:.3s}<extra></extra>'

#create tab content
tab1_content = dbc.Card(
    dbc.CardBody(children=[

    html.H2('Select map display date:'),
    dcc.DatePickerSingle(
        id='date-picker-map',
        min_date_allowed=df['date'].min(),
        max_date_allowed=df['date'].max(),
        display_format='DD/MM/YY',
        initial_visible_month=dt(2017, 8, 5),
        date='2017-01-01' #initial date
),
    dbc.Row(children=[
        dbc.Col(dcc.Graph(
            id = 'clickdata')
        ),
        dbc.Col(dcc.Graph(
            id='pop-map',
        ))]),

    html.H2('Select dates:'),
    dcc.DatePickerRange(
        id='bar-range',
        updatemode='bothdates',
        with_portal=True,
        display_format='DD/MM/YY',
        min_date_allowed=df['date'].min(),
        max_date_allowed=df['date'].max(),
        initial_visible_month=dt(2017, 1, 5),
        start_date='2017-01-01',
        end_date='2017-01-03' #initial date
    ),
    dcc.Graph(
        id='bar-race'
    )
    ])
)

tab2_content = html.Div(children=[
    dbc.Card(
        dbc.CardBody(children=[
            dcc.RadioItems(
        options=[
            {'label': 'By Artist', 'value': 'artist'},
            {'label': 'By Song', 'value': 'song'},
            {'label': 'By Nationality', 'value': 'country'}
        ],
        value='artist',
        #labelStyle={'display': 'inline-block'},
        id='tabs2-selector',
        inputStyle={"margin-left": "10px", "margin-right" : "5px"}
            ),
        ])
    )],
    id = 'tabs2_graph'
)
tab2_graph_1 = dbc.Card(children=[
        dcc.Dropdown(
        id='artist-picker',
        options=[
            {'label' : x, 'value' : x} for x in sorted(df['artist'].unique())
        ],
        value='Adele',
        placeholder='Select an artist',
        clearable=False
    ),
    dcc.Graph(
        id='artist-overall-streams'
    )], body = True
)
tab2_graph_2 = dbc.Card(children=[
        dcc.Dropdown(
        id='song-picker',
        options=[
            {'label' : x, 'value' : x} for x in sorted(df['track_name'].unique())
        ],
        value='Shape of You',
        placeholder='Select a song',
        clearable=False
    ),
    dcc.Graph(
        id='song-overall-streams'
    )], body = True
)

tab2_graph_3 = dbc.Card(children=[
    dcc.Dropdown(
        id='artist-nationality-picker',
        options=[
            {'label' : x[0], 'value' : x[1]} for x in codes[codes['code_3'].isin(df['nationality'].dropna())][['country','code_3']].values
        ],
        value='AUS',
        placeholder='Select a country',
        clearable=False
    ),
    dcc.Graph(
        id='artist-nationality'
    )], body = True
)

tabs = html.Div(
    [
        dcc.Tabs(
            [
                dcc.Tab(label="Date-based Visualisations", value="tab-1"),
                dcc.Tab(label="Global Popularity Distributions", value="tab-2"),
            ],
            id="tabs",
            value="tab-1",
        ),
        html.Div(id="tab-content"),
    ]
)

#display app
app.layout = tabs


#switch between tabs
@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "value")])
def switch_tab(at):
    if at == "tab-1":
        return tab1_content
    elif at == "tab-2":
        return tab2_content
    return html.P("Error...")

#switch between graphs on tab 2
@app.callback(
    Output("tabs2_graph","children"),
    [Input("tabs2-selector","value")],
    [State("tabs2_graph","children")],
    [State("tabs2-selector","value")])
def choose_graph(type,children,v):
    if type == 'artist':
        if len(children) > 1:
            children[1] = tab2_graph_1
        else:
            children.append(tab2_graph_1)
       #return children#.append(tab2_graph_1)# html.Div(children=[children.append(tab2_graph_1)])
    elif type == 'song':
        if len(children) > 1:
            children[1] = tab2_graph_2
        else:
            children.append(tab2_graph_2)
    elif type == 'country':
        if len(children) > 1:
            children[1] = tab2_graph_3
        else:
            children.append(tab2_graph_3)
    return children #just for testing, should only return children 


##old_output + [html.Div('Thing {}'.format(n_clicks))]##

## Update global popularity map
@app.callback(
    Output(component_id='pop-map', component_property='figure'),
    [Input(component_id='date-picker-map', component_property='date')])
def update_map(date):
    #plot the most popular song in each country on a certain date
    #choose date/artist
    #cur_date = '2017-12-15'
    cmap = cc.glasbey_light

    df_small = df[df['date'] == date]
    df_cur_day = pd.DataFrame(columns=df_small.columns)
    for reg in set(df_small['region']):
        df_cur_day = df_cur_day.append(df_small[(df_small['position'] == 1) & (df_small['region'] == reg)])
    #print(date)
    template = '<b>%{hovertext}</b><br><br>Country: %{customdata[0]}<br>Artist: %{customdata[1]}<br>Streams: %{customdata[2]}<extra></extra>'
    #(use this for streams) df_cur_day['streams'] = df_cur_day['streams'].astype(int)
    #plot data
    fig = px.choropleth(df_cur_day, locations="region",
                        color="id",
                        hover_name="track_name", # column to add to hover information
                        color_discrete_sequence=cmap,
                        title="Most popular songs globally on " + date,
                        labels={"id" : "Song name"},
                        hover_data={'region': True, 'artist': True,'streams': True, 'id': False})
    fig.update_layout(showlegend = True)
    fig.update_traces(hovertemplate=template)
    #Change legend to song names instead of IDs
    for i in range(len(fig.data)):
        fig.data[i].name = fig.data[i].hovertext[0]
    return fig

## Update bar chart race figure
@app.callback(
    Output('bar-race','figure'),
    [Input('bar-range','start_date'),
    Input('bar-range','end_date')])
def update_fig(start, end):
    return bcr.bar_chart_race_plotly(df_race.loc[start:end].iloc[::2],steps_per_period=30, period_length=200,sort='asc',bar_textposition='auto',n_bars=10,title='Top 10 most streamed songs per day')

@app.callback(
    Output('clickdata','figure'),
    [Input('pop-map','clickData')],
    [State('pop-map','figure')])
def get_click(clickData,figure):
    if clickData is None:
        fig = go.Figure()
        fig.update_layout(title='No Artist Selected.')
        return fig
    points_artist = clickData['points'][0]['customdata'][1]#['hovertext']
    #return str(points)
    #extract only the needed artists from the artist dataframe
    df2 = artists_df
    df2 = df2[df2['artists'].isin(df['artist'])]

    #Get values for a specific artist
    artist = points_artist

    #if the artist is not in the database, return error message
    if df2[df2['artists'] == artist].shape[0] == 0:
        fig = go.Figure()
        fig.update_layout(title='Characteristics not found for ' + artist + '.')
        return fig
    df_artist = pd.DataFrame(df2[df2['artists'] == artist].iloc[0].drop(['artists','count','popularity','year','loudness','key','tempo','duration_ms','explicit','mode']))

    #Get the mean of all artists that exist in both dataframes
    df_artist_mean = pd.DataFrame(df2.mean().drop(['count','popularity','year','loudness','key','tempo','duration_ms','explicit','mode']))

    #Rename column to a generic name
    df_artist.rename(columns={df_artist.columns[0] : "values"},inplace=True)
    df_artist_mean.rename(columns={df_artist_mean.columns[0] : "values"},inplace=True)

    #Draw chart
    #artist
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=df_artist['values'].append(df_artist['values'].head(1)),
        theta=df_artist.index,
        fill='toself',
        name=artist,
    ))
    #mean
    fig.add_trace(go.Scatterpolar(
        r=df_artist_mean['values'].append(df_artist_mean['values'].head(1)),
        theta=df_artist_mean.index,
        fill='toself',
        name='Mean',
    ))
    fig.update_layout(title='Average song characteristics of ' + artist)
    return fig

@app.callback(
    Output('artist-overall-streams','figure'),
    [Input('artist-picker','value')]
)
def update_fig(artist):
    #create df of streams for one artist over the entire period of time
    artist_df = pd.DataFrame(artist_streams[artist_streams['artist'] == artist].iloc[:,1:].stack()).reset_index(1).rename(columns={'level_1' : 'region', 0: 'streams'})
    #plot data
    fig = px.choropleth(artist_df, locations="region",
                        color="streams", 
                        # hover_name="artist", # column to add to hover information
                        color_continuous_scale=px.colors.sequential.Aggrnyl,
                        title="Global Stream Count: " + artist,
                        labels={"streams" : "Stream Count"})
    fig.update_traces(hovertemplate=maps_template)
    return fig

@app.callback(
    Output('song-overall-streams','figure'),
    [Input('song-picker','value')]
)
def update_fig(song):
    #create df of streams for one song over the entire period of time
    song_df = pd.DataFrame(song_streams[song_streams['track_name'] == song].iloc[:,1:].stack()).reset_index(1).rename(columns={'level_1' : 'region', 0: 'streams'})
    #plot data
    fig = px.choropleth(song_df, locations="region",
                        color="streams", 
                        # hover_name="song", # column to add to hover information
                        color_continuous_scale=px.colors.sequential.Aggrnyl,
                        title="Global Stream Count: " + song,
                        labels={"streams" : "Stream Count"})
    fig.update_traces(hovertemplate=maps_template)
    return fig


@app.callback(
    Output('artist-nationality','figure'),
    [Input('artist-nationality-picker','value')]
)
def update_fig(nat):
    nat_df = artist_weightings_df[nat]
    fig = px.choropleth(nat_df,locations=nat_df.index, color=nat,hover_name=nat_df.index,color_continuous_scale=px.colors.sequential.Aggrnyl,title='Global popularity of artists from ' + codes[codes['code_3'] == nat]['country'].iloc[0],labels={"streams" : "Stream Count"})
    fig.update_traces(hovertemplate=maps_template)
    return fig
                        


if __name__ == '__main__':
    app.run_server(debug=False,dev_tools_ui=False,dev_tools_props_check=False)

#debug
# if __name__ == '__main__':
#     app.run_server(debug=True)

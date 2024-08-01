import pandas as pd
import streamlit as st
from functools import cache
import datetime as dt


agency = pd.read_csv('agency.txt')
calendar = pd.read_csv('calendar.txt')
routes = pd.read_csv('routes.txt')
shapes = pd.read_csv('shapes.txt')
stop_times = pd.read_csv('stop_times.txt')
stops = pd.read_csv('stops.txt')
trips = pd.read_csv('trips.txt')

@cache
class Structure():
    def agency():
        st.write(agency.head())
    def calendar():
        st.write(calendar.head())
    def routes():
        st.write(routes.head())
    def shapes():
        st.write(shapes.head())
    def stop_times():
        st.write(stop_times.head())
    def stops():
        st.write(stops.head())
    def trips():
        st.write(stops.head())

    Metro=st.selectbox("Metro Data:",["agency","calendar","routes","shapes","stop_times","stops","trips"])

    if Metro=="agency" or Metro==None:
        agency()
    elif Metro=="calendar":
        calendar()
    elif Metro=="routes":
        routes()
    elif Metro=="shapes":
        shapes()
    elif Metro=="stop_times":
        stop_times()
    elif Metro=="stops":
        stops()
    else:
        trips()


import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
trips_calendar = pd.merge(trips, calendar, on='service_id', how='left')
trip_counts = trips_calendar[['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']].sum()
stops_with_routes = pd.merge(pd.merge(stop_times, trips, on='trip_id'), routes, on='route_id')
stop_route_counts = stops_with_routes.groupby('stop_id')['route_id'].nunique().reset_index()
stop_route_counts = stop_route_counts.rename(columns={'route_id':'number_of_routes'})
def convert_to_time(time_str):
        try:
            return dt.datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            hour, minute, second = map(int, time_str.split(':'))
            return dt.time(hour % 24, minute, second)
stop_times['arrival_time_dt'] = stop_times['arrival_time'].apply(convert_to_time)

def time_difference(time1, time2):
        if pd.isna(time1) or pd.isna(time2):
            return None
        full_date_time1 = dt.datetime.combine(dt.date.today(), time1)
        full_date_time2 = dt.datetime.combine(dt.date.today(), time2)
        return (full_date_time2 - full_date_time1).seconds / 60

stop_times_sorted = stop_times.sort_values(by=['stop_id', 'arrival_time_dt'])
stop_times_sorted['next_arrival_time'] = stop_times_sorted.groupby('stop_id')['arrival_time_dt'].shift(-1)
stop_times_sorted['interval_minutes'] = stop_times_sorted.apply(lambda row:time_difference(row['arrival_time_dt'], row['next_arrival_time']), axis=1)
stop_times_intervals = stop_times_sorted.dropna(subset=['interval_minutes'])

def part_of_day(time):
        if time < dt.time(12, 0):
            return 'Morning'
        elif time < dt.time(17, 0):
            return 'Afternoon'
        else:
            return 'Evening'
stop_times_intervals['part_of_day'] = stop_times_intervals['arrival_time_dt'].apply(part_of_day)
average_intervals = stop_times_intervals.groupby('part_of_day')['interval_minutes'].mean().reset_index()


def classify_time_interval(time):
    if time < dt.time(6, 0):
        return 'Early Morning'
    elif time < dt.time(10, 0):
        return 'Morning Peak'
    elif time < dt.time(16, 0):
        return 'Midday'
    elif time < dt.time(20, 0):
        return 'Evening Peak'
    else:
        return 'Late Evening'

stop_times['time_interval'] = stop_times['arrival_time_dt'].apply(classify_time_interval)

trips_per_interval = stop_times.groupby('time_interval')['trip_id'].nunique().reset_index()
trips_per_interval = trips_per_interval.rename(columns={'trip_id': 'number_of_trips'})

ordered_intervals = ['Early Morning', 'Morning Peak', 'Midday', 'Evening Peak', 'Late Evening']
trips_per_interval['time_interval'] = pd.Categorical(trips_per_interval['time_interval'], categories=ordered_intervals, ordered=True)
trips_per_interval = trips_per_interval.sort_values('time_interval')

@cache
class Analysis():
    def Map():
        fig = px.scatter(shapes, 
                 x='shape_pt_lon', 
                 y='shape_pt_lat', 
                 color='shape_id', 
                 title='Geographical Paths of Delhi Metro Routes',
                 labels={'shape_pt_lon': 'Longitude', 'shape_pt_lat': 'Latitude'},
                 color_continuous_scale='viridis')

        fig.update_traces(marker=dict(size=5), showlegend=False)
        fig.update_layout(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            width=800,
            height=800
        )
        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)

        st.plotly_chart(fig)
    
    def Trips():
        fig = px.bar(trip_counts, 
             x=trip_counts.index, 
             y=trip_counts.values, 
             color_discrete_sequence=['red'], 
             title='Number of Trips per Day of the Week')
        fig.update_layout(
            xaxis_title='Day of the Week',
            yaxis_title='Number of Trips',
            title='Number of Trips per Day of the Week',
            width=800,
            height=600
        )
        fig.update_xaxes(tickangle=45)
        fig.update_layout(
            xaxis=dict(showgrid=True),
            yaxis=dict(showgrid=True)
        )
        st.plotly_chart(fig)
    
    def Geo():
        fig = px.scatter(stops, 
                 x='stop_lon', 
                 y='stop_lat', 
                 color_discrete_sequence=['red'], 
                 size_max=50, 
                 title='Geographical Distribution of Delhi Metro Stops')

        fig.update_layout(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            title='Geographical Distribution of Delhi Metro Stops',
            width=800,
            height=800,
            showlegend=False
        )

        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)

        st.plotly_chart(fig.show())

    def RPS():
        fig = px.scatter(stop_route_counts, 
                 x='stop_id', 
                 y='number_of_routes', 
                 size='number_of_routes', 
                 color='number_of_routes', 
                 color_continuous_scale='twilight', 
                 size_max=70, 
                 title='Number of Routes per Metro Stop in Delhi',
                 labels={'stop_lon': 'Longitude', 'stop_lat': 'Latitude', 'number_of_routes': 'Number of Routes'},
                 opacity=0.5)

        fig.update_layout(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            width=700,
            height=700,
            coloraxis_colorbar=dict(title='Number of Routes'),
            showlegend=True
        )

        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)
        st.plotly_chart(fig)
   
    def Weektrip():
        fig = px.bar(average_intervals, 
             x='part_of_day', 
             y='interval_minutes', 
             category_orders={'part_of_day': ['Morning', 'Afternoon', 'Evening']}, 
             color='part_of_day', 
             title='Average Interval Between Trips by Part of Day')
        fig.update_layout(
            xaxis_title='Part of Day',
            yaxis_title='Average Interval (minutes)',
            width=800,
            height=600
        )

        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)

        st.plotly_chart(fig)
    
    def TripsPer():
        fig = px.bar(trips_per_interval, 
             x='time_interval', 
             y='number_of_trips', 
             color='time_interval', 
             title='Number of Trips per Time Interval', 
             labels={'time_interval': 'Time Interval', 'number_of_trips': 'Number of Trips'},
             color_discrete_sequence=px.colors.qualitative.Set2)

        fig.update_layout(
            xaxis_title='Time Interval',
            yaxis_title='Number of Trips',
            width=800,
            height=600
        )

        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)

        st.plotly_chart(fig)
    
    def Optimised():
        fig = go.Figure()
        adjusted_trips_per_interval = trips_per_interval.copy()
        adjustment_factors = {'Morning Peak': 1.20, 'Evening Peak': 1.20, 'Midday': 0.90, 'Early Morning': 1.0, 'Late Evening': 0.90}

        adjusted_trips_per_interval['adjusted_number_of_trips'] = adjusted_trips_per_interval.apply(
    lambda row: int(row['number_of_trips'] * adjustment_factors[row['time_interval']]), axis=1)

        bar_width = 0.35

        fig.add_trace(go.Bar(
            x=adjusted_trips_per_interval['time_interval'],
            y=adjusted_trips_per_interval['number_of_trips'],
            name='Original',
            marker_color='blue',
            width=bar_width
        ))

        fig.add_trace(go.Bar(
            x=adjusted_trips_per_interval['time_interval'],
            y=adjusted_trips_per_interval['adjusted_number_of_trips'],
            name='Adjusted',
            marker_color='cyan',
            width=bar_width
        ))

        fig.update_layout(
            title='Original vs Adjusted Number of Trips per Time Interval',
            xaxis_title='Time Interval',
            yaxis_title='Number of Trips',
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1,
            width=800,
            height=600,
            legend=dict(title='Trip Type')
        )

        st.plotly_chart(fig )



    pic=st.selectbox("Analysis::",["Map","Trips","Geo","RPS","Weektrip","TripsPer","Optimised"])

    if pic=="Map" or pic== None:
        Map()
    elif pic=="Trips":
        Trips()
    elif pic=="Geo":
        Geo()
    elif pic=="RPS":
        RPS()
    elif pic=="Weektrip":
        Weektrip()
    elif pic=="TripsPer":
        TripsPer()
    else:
        Optimised()



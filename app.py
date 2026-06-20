import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# --- 1. Page Configuration ---
st.set_page_config(page_title="Astram Traffic Intelligence", page_icon="🚦", layout="wide")
st.title("🚦 Astram: Urban Traffic Incident Dashboard")
st.markdown("A real-time prototype for monitoring, analyzing, and resolving urban traffic incidents.")

# --- 2. Data Loading & Preprocessing ---
@st.cache_data
def load_data():
    # Load dataset from the data folder
    file_path = "data/Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
    
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"File not found. Please ensure your CSV is located at: {file_path}")
        return pd.DataFrame()

    # Clean coordinates
    df = df[(df['latitude'] != 0) & (df['longitude'] != 0)].dropna(subset=['latitude', 'longitude'])
    
    # Convert datetimes and extract useful temporal features
    df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
    df['closed_datetime'] = pd.to_datetime(df['closed_datetime'], errors='coerce')
    df['hour'] = df['start_datetime'].dt.hour
    
    # Fill empty zones and causes for better filtering
    df['zone'] = df['zone'].fillna('Unknown')
    df['event_cause'] = df['event_cause'].fillna('Unknown')
    df['status'] = df['status'].fillna('Unknown')

    return df

df = load_data()

if df.empty:
    st.stop() # Stop execution if data is missing

# --- 3. Sidebar Filters ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3211/3211429.png", width=100) # Placeholder logo
st.sidebar.header("Dashboard Filters")

# Filter logic
status_filter = st.sidebar.multiselect("Incident Status", options=df['status'].unique(), default=df['status'].unique())
cause_filter = st.sidebar.multiselect("Event Cause", options=df['event_cause'].unique(), default=df['event_cause'].unique())

# Apply filters
filtered_df = df[df['status'].isin(status_filter) & df['event_cause'].isin(cause_filter)]

# --- 4. Top Row: Key Metrics (KPIs) ---
st.markdown("### 📊 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

active_count = len(filtered_df[filtered_df['status'].str.lower() == 'active'])
closed_count = len(filtered_df[filtered_df['status'].str.lower() == 'closed'])
pothole_count = len(filtered_df[filtered_df['event_cause'].str.lower() == 'pot_holes'])

col1.metric("Total Incidents", f"{len(filtered_df):,}")
col2.metric("Active / Unresolved", f"{active_count:,}", delta_color="inverse")
col3.metric("Resolved Incidents", f"{closed_count:,}")
col4.metric("Pothole Hazards", f"{pothole_count:,}")

st.markdown("---")

# --- 5. Middle Row: Maps and Charts ---
map_col, chart_col = st.columns((2, 1))

with map_col:
    st.markdown("### 📍 Live Incident Hotspot Map")
    
    # Base map centered on average coordinates
    m = folium.Map(location=[filtered_df['latitude'].mean(), filtered_df['longitude'].mean()], zoom_start=11)
    
    # Plot markers (Limit to 1000 to prevent browser freezing)
    for idx, row in filtered_df.head(1000).iterrows():
        # Dynamic styling based on status
        if str(row['status']).lower() == 'active':
            icon_color = 'red'
            icon_type = 'info-sign'
        else:
            icon_color = 'green'
            icon_type = 'ok-circle'
            
        popup_html = f"""
        <b>Cause:</b> {row['event_cause']}<br>
        <b>Status:</b> {row['status']}<br>
        <b>Zone:</b> {row['zone']}<br>
        """
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=icon_color, icon=icon_type)
        ).add_to(m)

    st_folium(m, width=800, height=450, returned_objects=[])

with chart_col:
    st.markdown("### 📈 Incidents by Cause")
    # Plotly Donut Chart
    cause_counts = filtered_df['event_cause'].value_counts().reset_index()
    cause_counts.columns = ['Cause', 'Count']
    fig_pie = px.pie(cause_counts, values='Count', names='Cause', hole=0.4)
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# --- 6. Bottom Row: Analytics ---
st.markdown("### 🕒 Temporal & Zone Analytics")
col_bar, col_line = st.columns(2)

with col_bar:
    st.markdown("**Incidents by Zone**")
    zone_counts = filtered_df['zone'].value_counts().reset_index().head(10) # Top 10 zones
    zone_counts.columns = ['Zone', 'Incident Count']
    fig_bar = px.bar(zone_counts, x='Zone', y='Incident Count', text_auto=True, color='Incident Count', color_continuous_scale='Blues')
    st.plotly_chart(fig_bar, use_container_width=True)

with col_line:
    st.markdown("**Incident Frequency by Hour of Day**")
    hourly_counts = filtered_df.groupby('hour').size().reset_index(name='Count')
    fig_line = px.line(hourly_counts, x='hour', y='Count', markers=True, labels={'hour': 'Hour of Day (24H)', 'Count': 'Number of Incidents'})
    fig_line.update_xaxes(dtick=2)
    st.plotly_chart(fig_line, use_container_width=True)

# --- 7. Data Explorer ---
with st.expander("🔍 View Raw Incident Data"):
    st.dataframe(filtered_df[['id', 'start_datetime', 'event_cause', 'status', 'zone', 'address']].sort_values(by='start_datetime', ascending=False), use_container_width=True)
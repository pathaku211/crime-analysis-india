import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="India Crime Dashboard", layout="wide")

st.title("🔍 India Crime Data Explorer")
st.markdown("Analyze Indian crime statistics by state, district, year, and category.")

# === Load Data ===
DATA_FOLDER = r"crime"
csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]

if not csv_files:
    st.error("No CSV files found in the data folder.")
    st.stop()

selected_file = st.selectbox("📂 Select a Crime Dataset", csv_files)
file_path = os.path.join(DATA_FOLDER, selected_file)

# Try to read the CSV file
try:
    df = pd.read_csv(file_path)
except Exception as e:
    st.error(f"Failed to read the file: {e}")
    st.stop()

# === Standardize column names ===
df.columns = df.columns.str.strip().str.replace('\n', '').str.replace('\r', '').str.upper()

# === Rename columns to standard form ===
rename_map = {
    'STATES/UTS': 'STATE/UT',
    'STATE': 'STATE/UT',
    'DISTRICT': 'DISTRICT',  # If this column doesn't exist, we will add it manually later
    'YEAR': 'YEAR',  # If this column doesn't exist, we will add it manually later
    'TOTAL COGNIZABLE IPC CRIMES': 'TOTAL IPC CRIMES'
}
df.rename(columns=rename_map, inplace=True)

# === Manually Handle Missing 'DISTRICT' and 'YEAR' Columns ===
if 'DISTRICT' not in df.columns:
    df['DISTRICT'] = 'ALL'  # You can replace this with actual district data if available

if 'YEAR' not in df.columns:
    # Assuming the dataset corresponds to a specific year (e.g., 2012)
    df['YEAR'] = 2012  # Replace this with appropriate year if needed

# === Ensure essential columns exist ===
required_columns = {'STATE/UT', 'DISTRICT', 'YEAR'}
if not required_columns.issubset(df.columns):
    st.error("This dataset is missing required columns: 'STATE/UT', 'DISTRICT', or 'YEAR'")
    st.stop()

# === Sidebar Filters ===
with st.sidebar:
    st.header("🧪 Filters")

    # Ensure YEAR is numeric
    df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')  # Ensure YEAR is numeric
    df = df.dropna(subset=['STATE/UT', 'DISTRICT', 'YEAR'])  # Drop rows missing important data

    # Create the available states and districts
    states = sorted(df['STATE/UT'].unique())
    selected_state = st.selectbox("Select State/UT", states)

    # Filter data by selected state
    state_data = df[df['STATE/UT'] == selected_state]

    districts = sorted(state_data['DISTRICT'].unique())
    selected_district = st.selectbox("Select District", districts)

    years = sorted(state_data['YEAR'].unique())
    selected_year = st.selectbox("Select Year", years)

    crime_columns = [col for col in df.columns if col not in ['STATE/UT', 'DISTRICT', 'YEAR']]
    valid_defaults = [crime for crime in ['MURDER', 'RAPE'] if crime in crime_columns]
    selected_crimes = st.multiselect("Select Crime Types", crime_columns, default=valid_defaults)

# === Filtered Data ===
filtered_data = df[
    (df['STATE/UT'] == selected_state) &
    (df['DISTRICT'] == selected_district) &
    (df['YEAR'] == selected_year)
    ]

# Displaying filtered data
st.subheader(f"📍 Crime Data for {selected_district}, {selected_state} — {selected_year}")
if not filtered_data.empty and selected_crimes:
    st.dataframe(filtered_data[selected_crimes])

    # Total selected crimes
    st.subheader("🚨 Total Selected Crimes:")
    total_selected = filtered_data[selected_crimes].sum(numeric_only=True)
    st.write(total_selected)

    # Pie Chart
    st.subheader("📊 Crime Distribution (Pie Chart)")
    fig1, ax1 = plt.subplots()
    cleaned = pd.to_numeric(total_selected, errors='coerce').dropna()
    cleaned = cleaned[cleaned > 0]

    if not cleaned.empty:
        cleaned.plot.pie(autopct='%1.1f%%', startangle=90, ax=ax1)
        ax1.set_ylabel("")
        st.pyplot(fig1)
    else:
        st.info("No valid data for pie chart.")
else:
    st.warning("No data available for the selected filters or no crime types selected.")

# === Check if Total IPC Crimes Column is Present ===
if 'TOTAL IPC CRIMES' in df.columns:
    # Bar Chart: Top 5 States by IPC Crimes
    st.subheader("🏆 Top 5 States with Highest IPC Crimes")
    df['TOTAL IPC CRIMES'] = pd.to_numeric(df['TOTAL IPC CRIMES'], errors='coerce')
    top_states = df.groupby('STATE/UT')['TOTAL IPC CRIMES'].sum().sort_values(ascending=False).head(5)
    if not top_states.empty:
        st.bar_chart(top_states)
    else:
        st.warning("No data available for 'TOTAL IPC CRIMES' to generate bar chart.")

    # Line Chart: Crime Trend Over Years
    st.subheader(f"📈 Crime Trend Over Years in {selected_state}")
    trend = df[df['STATE/UT'] == selected_state].copy()
    trend['TOTAL IPC CRIMES'] = pd.to_numeric(trend['TOTAL IPC CRIMES'], errors='coerce')
    trend_data = trend.groupby('YEAR')['TOTAL IPC CRIMES'].sum().sort_index()
    if not trend_data.empty:
        st.line_chart(trend_data)
    else:
        st.warning("No data available for the crime trend chart.")
else:
    st.warning("No 'TOTAL IPC CRIMES' column found in the dataset to generate charts.")

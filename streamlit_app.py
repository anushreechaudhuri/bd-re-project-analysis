import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

def parse_capacity(capacity_str):
    """Parse capacity string and convert to numeric MW value"""
    if pd.isna(capacity_str) or capacity_str == "":
        return None
    try:
        # Extract numbers from capacity string (handles kWp, MWp, etc.)
        numbers = re.findall(r'\d+\.?\d*', str(capacity_str))
        if numbers:
            value = float(numbers[0])
            # Convert to MW if the string contains 'kW' or 'kWp'
            if 'kw' in str(capacity_str).lower():
                return value / 1000  # Convert kW to MW
            return value
    except:
        pass
    return None

# Page configuration
st.set_page_config(
    page_title="Renewable Energy Projects Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .project-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
        margin: 1rem 0;
    }
    .opposition-alert {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E8B57;
        color: white;
    }
    /* Fix text sizing issues */
    .stMetric {
        font-size: 0.9rem !important;
    }
    .stMetric [data-testid="metric-value"] {
        font-size: 1.2rem !important;
    }
    .stMetric [data-testid="metric-label"] {
        font-size: 0.8rem !important;
    }
    /* Responsive text */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .stMetric [data-testid="metric-value"] {
            font-size: 1rem !important;
        }
        .stMetric [data-testid="metric-label"] {
            font-size: 0.7rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and process the renewable energy projects data"""
    try:
        # Load CSV data
        csv_path = "renewable_energy_projects.csv"
        df = pd.read_csv(csv_path)
        
        # Parse coordinates
        def parse_coordinates(coord_str):
            if pd.isna(coord_str) or coord_str == "":
                return None, None
            try:
                # Extract numbers from coordinate string
                coords = re.findall(r'-?\d+\.?\d*', str(coord_str))
                if len(coords) >= 2:
                    return float(coords[0]), float(coords[1])
            except:
                pass
            return None, None
        
        df['latitude'] = df['detail_Latitude__Longitude'].apply(lambda x: parse_coordinates(x)[0])
        df['longitude'] = df['detail_Latitude__Longitude'].apply(lambda x: parse_coordinates(x)[1])
        
        # Filter out rows without coordinates and invalid coordinates (0,0)
        df_with_coords = df.dropna(subset=['latitude', 'longitude']).copy()
        # Remove invalid coordinates (0,0 or outside Bangladesh region)
        df_with_coords = df_with_coords[
            (df_with_coords['latitude'] != 0) & 
            (df_with_coords['longitude'] != 0) &
            (df_with_coords['latitude'] >= 20) & 
            (df_with_coords['latitude'] <= 27) &
            (df_with_coords['longitude'] >= 88) & 
            (df_with_coords['longitude'] <= 93)
        ].copy()
        
        # Load summary data
        summary_dir = Path("summary")
        summary_data = {}
        
        if summary_dir.exists():
            for summary_file in summary_dir.glob("*.json"):
                project_id = summary_file.stem
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary_data[project_id] = json.load(f)
                except Exception as e:
                    st.warning(f"Could not load summary for project {project_id}: {e}")
        
        # Parse capacity for all data
        df['capacity_numeric'] = df['capacity'].apply(parse_capacity)
        df_with_coords['capacity_numeric'] = df_with_coords['capacity'].apply(parse_capacity)
        
        return df, df_with_coords, summary_data
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, {}


def display_project_details(project_id, df, summary_data):
    """Display detailed information for a selected project"""
    project = df[df['project_id'] == project_id]
    
    if project.empty:
        st.error("Project not found")
        return
    
    project = project.iloc[0]
    
    # Project header
    st.markdown(f"### {project['project_name']}")
    st.markdown(f"**Project ID:** {project['project_id']}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        capacity_display = project['capacity']
        if pd.notna(project.get('capacity_numeric')):
            capacity_display += f" ({project['capacity_numeric']:.2f} MW)"
        st.metric("Capacity", capacity_display)
    
    with col2:
        st.metric("Status", project['present_status'])
    
    with col3:
        st.metric("Agency", project['agency'])
    
    with col4:
        st.metric("Location", f"{project['detail_District']}, {project['detail_Division']}")
    
    # Project details
    st.markdown("#### Project Details")
    
    details_cols = [
        'detail_System_Owner', 'detail_EPC', 'detail_Financing_Primary_Fund_Allocator__PFA_',
        'detail_Financing_Last_Mile_Financial_Distributor__LMFD_', 'detail_Completion_Date__COD_',
        'detail_DC_Capacity', 'detail_AC_Capacity', 'detail_Grid_Status',
        'detail_Important_Information_of_this_Project', 'detail_Expected_Energy_Generation_and_CO2Emission_reduction_during_System_Life'
    ]
    
    for col in details_cols:
        if col in project and pd.notna(project[col]) and project[col] != "":
            st.markdown(f"**{col.replace('detail_', '').replace('_', ' ').title()}:** {project[col]}")
    
    # Opposition analysis
    st.markdown("#### Opposition Analysis")
    
    if str(project_id) in summary_data:
        opposition = summary_data[str(project_id)]
        
        if opposition.get('has_opposition_evidence', False):
            st.markdown('<div class="opposition-alert">', unsafe_allow_html=True)
            st.markdown("⚠️ **Opposition Evidence Found**")
            st.markdown(f"**Confidence Score:** {opposition.get('confidence_score', 'N/A')}")
            
            if 'opposition_types' in opposition:
                st.markdown("**Types of Opposition:**")
                for opp_type in opposition['opposition_types']:
                    st.markdown(f"• {opp_type}")
            
            if 'summary' in opposition:
                st.markdown("**Summary:**")
                st.markdown(opposition['summary'])
            
            if 'sources' in opposition:
                st.markdown("**Sources:**")
                for source in opposition['sources']:
                    st.markdown(f"• [{source}]({source})")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.success("✅ No opposition evidence found for this project")
    else:
        st.info("ℹ️ **Opposition status unknown** - Analysis in progress")

def main():
    # Header
    st.markdown('<h1 class="main-header">🌱 Renewable Energy Projects Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    df, df_with_coords, summary_data = load_data()
    
    if df is None:
        st.error("Failed to load data. Please check if the CSV file exists.")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters & Search")
    
    # Search
    search_term = st.sidebar.text_input("Search projects", placeholder="Enter project name, location, or agency...")
    
    # Technology filter
    technologies = ['All'] + sorted(df['re_technology'].unique().tolist())
    selected_tech = st.sidebar.selectbox("Technology", technologies)
    
    # Status filter
    statuses = ['All'] + sorted(df['present_status'].unique().tolist())
    selected_status = st.sidebar.selectbox("Status", statuses)
    
    # Agency filter
    agencies = ['All'] + sorted(df['agency'].unique().tolist())
    selected_agency = st.sidebar.selectbox("Agency", agencies)
    
    # Capacity range
    min_capacity = st.sidebar.number_input("Min Capacity (MW)", min_value=0.0, value=0.0)
    max_capacity = st.sidebar.number_input("Max Capacity (MW)", min_value=0.0, value=float(df['capacity_numeric'].max()))
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        search_mask = (
            filtered_df['project_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['location'].str.contains(search_term, case=False, na=False) |
            filtered_df['agency'].str.contains(search_term, case=False, na=False) |
            filtered_df['detail_District'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    if selected_tech != 'All':
        filtered_df = filtered_df[filtered_df['re_technology'] == selected_tech]
    
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['present_status'] == selected_status]
    
    if selected_agency != 'All':
        filtered_df = filtered_df[filtered_df['agency'] == selected_agency]
    
    # Ensure capacity_numeric is available for filtering
    if 'capacity_numeric' not in filtered_df.columns:
        filtered_df['capacity_numeric'] = filtered_df['capacity'].apply(parse_capacity)
    
    # Filter by capacity range (handle NaN values)
    capacity_mask = (
        (filtered_df['capacity_numeric'] >= min_capacity) & 
        (filtered_df['capacity_numeric'] <= max_capacity)
    )
    filtered_df = filtered_df[capacity_mask]
    
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Project Explorer", "📊 Project List", "📈 Analytics", "📋 Raw Data"])
    
    with tab1:
        st.markdown("### Project Explorer")
        
        # Project selection
        st.markdown("### Select a Project for Details")
        project_options = {f"{row['project_name']} (ID: {row['project_id']})": row['project_id'] 
                         for _, row in filtered_df.iterrows()}
        
        if project_options:
            selected_project = st.selectbox("Choose a project:", list(project_options.keys()))
            
            if selected_project:
                project_id = project_options[selected_project]
                display_project_details(project_id, df, summary_data)
        else:
            st.warning("No projects found matching the selected filters.")
    
    with tab2:
        st.markdown("### Project List")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Projects", len(filtered_df))
        
        with col2:
            total_capacity = filtered_df['capacity_numeric'].sum() if 'capacity_numeric' in filtered_df.columns else 0
            st.metric("Total Capacity", f"{total_capacity:.1f} MW")
        
        with col3:
            st.metric("Projects with Opposition", len([pid for pid in filtered_df['project_id'].astype(str) if pid in summary_data and summary_data[pid].get('has_opposition_evidence', False)]))
        
        with col4:
            st.metric("Completed Projects", len(filtered_df[filtered_df['present_status'].str.contains('Completed', case=False, na=False)]))
        
        # Project cards
        for _, project in filtered_df.iterrows():
            with st.expander(f"{project['project_name']} - {project['capacity']} {project['re_technology']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Location:** {project['location']}")
                    st.markdown(f"**Agency:** {project['agency']}")
                    st.markdown(f"**Status:** {project['present_status']}")
                    if pd.notna(project['detail_Completion_Date__COD_']):
                        st.markdown(f"**Completion Date:** {project['detail_Completion_Date__COD_']}")
                
                with col2:
                    if pd.notna(project['latitude']) and pd.notna(project['longitude']):
                        st.markdown(f"**Coordinates:** {project['latitude']:.4f}, {project['longitude']:.4f}")
                    
                    # Opposition indicator
                    project_id_str = str(project['project_id'])
                    if project_id_str in summary_data:
                        if summary_data[project_id_str].get('has_opposition_evidence', False):
                            st.markdown("⚠️ **Opposition Evidence**")
                        else:
                            st.markdown("✅ **No Opposition**")
                    else:
                        st.markdown("ℹ️ **Status Unknown**")
                
                # Show opposition summary if available
                if project_id_str in summary_data:
                    opposition = summary_data[project_id_str]
                    if opposition.get('has_opposition_evidence', False):
                        st.markdown("**Opposition Summary:**")
                        st.markdown(opposition.get('summary', 'No summary available')[:500] + "...")
                        st.markdown(f"**Confidence:** {opposition.get('confidence_score', 'N/A')}")
    
    with tab3:
        st.markdown("### Analytics Dashboard")
        
        # Technology distribution
        tech_counts = filtered_df['re_technology'].value_counts()
        fig_tech = px.pie(values=tech_counts.values, names=tech_counts.index, title="Projects by Technology")
        st.plotly_chart(fig_tech, use_container_width=True)
        
        # Status distribution
        status_counts = filtered_df['present_status'].value_counts()
        if not status_counts.empty:
            fig_status = px.bar(
                x=status_counts.index, 
                y=status_counts.values, 
                title="Projects by Status",
                labels={'x': 'Status', 'y': 'Number of Projects'}
            )
            fig_status.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig_status, use_container_width=True)
        
        # Capacity distribution
        if not filtered_df.empty and 'capacity_numeric' in filtered_df.columns:
            # Filter out NaN values for capacity histogram
            capacity_data = filtered_df.dropna(subset=['capacity_numeric'])
            if not capacity_data.empty:
                fig_capacity = px.histogram(capacity_data, x='capacity_numeric', nbins=20, title="Capacity Distribution (MW)")
                st.plotly_chart(fig_capacity, use_container_width=True)
        
        # Agency analysis
        agency_counts = filtered_df['agency'].value_counts().head(10)
        if not agency_counts.empty:
            fig_agency = px.bar(
                x=agency_counts.values, 
                y=agency_counts.index, 
                orientation='h', 
                title="Top 10 Agencies by Project Count",
                labels={'x': 'Number of Projects', 'y': 'Agency'}
            )
            st.plotly_chart(fig_agency, use_container_width=True)
    
    with tab4:
        st.markdown("### Raw Data")
        
        # Show filtered data
        st.markdown(f"Showing {len(filtered_df)} projects")
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download filtered data as CSV",
            data=csv,
            file_name="filtered_renewable_energy_projects.csv",
            mime="text/csv"
        )
        
        # Data table
        st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="DTN Routing Results", layout="wide", page_icon="📡")

st.title("📡 Spatio-Semantic DTN Routing Analysis")
st.markdown("Interactive performance analysis of Epidemic, Spray & Wait, Semantic, and Spatio-Semantic routing protocols.")

# Load Data
@st.cache_data
def load_data():
    base_dir = "plots"
    try:
        epidemic = pd.read_csv(os.path.join(base_dir, "epidemic_results.csv"))
        spray = pd.read_csv(os.path.join(base_dir, "spray_results.csv"))
        semantic = pd.read_csv(os.path.join(base_dir, "semantic_results.csv"))
        spatio = pd.read_csv(os.path.join(base_dir, "spatio_semantic_results.csv"))
        
        # Add a column for algorithm name
        epidemic['Algorithm'] = 'Epidemic'
        spray['Algorithm'] = 'Spray & Wait'
        semantic['Algorithm'] = 'Semantic'
        spatio['Algorithm'] = 'Spatio-Semantic'
        
        # Combine all into one dataframe
        df = pd.concat([epidemic, spray, semantic, spatio], ignore_index=True)
        
        # Ensure categorical ordering
        df['Traffic'] = pd.Categorical(df['Traffic'], ["Low", "Medium", "High"])
        return df
    except Exception as e:
        st.error(f"Error loading CSV files: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # Sidebar controls
    st.sidebar.header("Filter Options")
    selected_algs = st.sidebar.multiselect(
        "Select Algorithms to Compare",
        options=df['Algorithm'].unique(),
        default=df['Algorithm'].unique()
    )
    
    filtered_df = df[df['Algorithm'].isin(selected_algs)]
    
    # Define colors
    color_discrete_map = {
        'Epidemic': '#EF553B',
        'Spray & Wait': '#00CC96',
        'Semantic': '#AB63FA',
        'Spatio-Semantic': '#19D3F3'
    }

    # Layout using Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Metric Trends (Line Charts)", "Performance Radar", "Raw Data Overview", "🧪 Live Hardware Simulation"])
    
    with tab1:
        st.subheader("Key Performance Metrics vs Traffic Level")
        col1, col2 = st.columns(2)
        
        with col1:
            fig_delivery = px.line(filtered_df, x="Traffic", y="DeliveryRatio", color="Algorithm", markers=True,
                                   title="Delivery Ratio", color_discrete_map=color_discrete_map,
                                   template="plotly_dark")
            fig_delivery.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_delivery, use_container_width=True)
            
            fig_overhead = px.line(filtered_df, x="Traffic", y="OverheadRatio", color="Algorithm", markers=True,
                                   title="Overhead Ratio", color_discrete_map=color_discrete_map,
                                   template="plotly_dark")
            fig_overhead.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_overhead, use_container_width=True)
            
        with col2:
            fig_delay = px.line(filtered_df, x="Traffic", y="AvgCriticalDelay", color="Algorithm", markers=True,
                                title="Avg Critical Delay (seconds)", color_discrete_map=color_discrete_map,
                                template="plotly_dark")
            fig_delay.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_delay, use_container_width=True)
            
            fig_drops = px.line(filtered_df, x="Traffic", y="BufferDrops", color="Algorithm", markers=True,
                                title="Buffer Drops", color_discrete_map=color_discrete_map,
                                template="plotly_dark")
            fig_drops.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_drops, use_container_width=True)

    with tab2:
        st.subheader("Multi-Objective Trade-off Analysis (Medium Traffic)")
        st.write("A radar chart helps judges immediately see the trade-offs of each algorithm.")
        
        medium_df = filtered_df[filtered_df['Traffic'] == 'Medium']
        
        if not medium_df.empty:
            # Normalize metrics for radar chart
            categories = ['DeliveryRatio', 'Inverted Delay (Faster=Better)', 'Inverted Overhead (Lower=Better)', 'Inverted Drops (Lower=Better)']
            
            fig_radar = go.Figure()
            
            for alg in medium_df['Algorithm']:
                row = medium_df[medium_df['Algorithm'] == alg].iloc[0]
                
                # Normalizing values roughly for display between 0 and 1
                r_vals = [
                    row['DeliveryRatio'],
                    1 - min((row['AvgDelay']/2000), 1),  # Max delay approx 2000s
                    1 - min((row['OverheadRatio']/50), 1), # Max overhead approx 50
                    1 - min((row['BufferDrops']/1000), 1)  # Max drops approx 1000
                ]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_vals,
                    theta=categories,
                    fill='toself',
                    name=alg,
                    line_color=color_discrete_map.get(alg)
                ))
                
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1])
                ),
                showlegend=True,
                template="plotly_dark",
                height=600
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    with tab3:
        st.subheader("Raw Simulation Results")
        st.dataframe(filtered_df, use_container_width=True)
        st.download_button(
            label="Download Aggregated Data as CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name='aggregated_results.csv',
            mime='text/csv',
        )

    with tab4:
        st.subheader("Scientific Sandbox Simulation Engine")
        st.write("Launch the hardware-accelerated, high-fidelity PyGame simulation directly from this dashboard.")
        st.write("This simulation locks pseudo-random state to perfectly compare **Epidemic**, **Spray & Wait**, and **Spatio-Semantic** algorithms simultaneously under **High Traffic** workloads.")
        
        st.markdown(
            """
            **Visual Legend:**
            - 🟡 **Drones**: Pulsing transmission waves
            - 🟦 **Civilians**: Standard nodes
            - 🟥 **Responders**: Fast moving active field agents
            - 🟩 **Shelter**: Static base stations
            - 🌟 **Glowing Halos**: Indicates heavily congested buffers
            - 🟢 **Green Rays**: Valid packet transmissions happening between nodes
            """
        )
        
        if st.button("▶️ LAUNCH COMPETITION DEMO (HIGH TRAFFIC)", type="primary"):
            import subprocess
            import sys
            
            st.info("Simulation launched in a new window! Please check your taskbar.")
            # Launch the Pygame script in the background detached
            subprocess.Popen([sys.executable, "modern_multi_demo.py"])
            
else:
    st.warning("No data found to display. Please verify that the CSV files are present in the 'plots/' directory.")

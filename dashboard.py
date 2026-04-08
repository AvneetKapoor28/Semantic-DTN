import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="DTN Routing Results", layout="wide", page_icon="📡")

st.title("📡 Spatio-Semantic DTN Routing Analysis")
st.markdown("Interactive performance analysis of **Epidemic**, **Spray & Wait**, **Semantic**, and **Spatio-Semantic** routing protocols across Low / Medium / High traffic.")

# Load Data
@st.cache_data
def load_data():
    base_dir = "plots"
    try:
        epidemic = pd.read_csv(os.path.join(base_dir, "epidemic_results.csv"))
        spray = pd.read_csv(os.path.join(base_dir, "spray_results.csv"))
        semantic = pd.read_csv(os.path.join(base_dir, "semantic_results.csv"))
        spatio = pd.read_csv(os.path.join(base_dir, "spatio_semantic_results.csv"))

        epidemic['Algorithm'] = 'Epidemic'
        spray['Algorithm'] = 'Spray & Wait'
        semantic['Algorithm'] = 'Semantic'
        spatio['Algorithm'] = 'Spatio-Semantic'

        df = pd.concat([epidemic, spray, semantic, spatio], ignore_index=True)
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Metric Trends",
        "🎯 Performance Radar",
        "📊 Raw Data",
        "🧪 Live Simulation"
    ])

    with tab1:
        st.subheader("Key Performance Metrics vs Traffic Level")

        col1, col2 = st.columns(2)

        with col1:
            fig_delivery = px.line(filtered_df, x="Traffic", y="DeliveryRatio", color="Algorithm", markers=True,
                                   title="Delivery Ratio", color_discrete_map=color_discrete_map,
                                   template="plotly_dark")
            fig_delivery.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_delivery, width="stretch")

            fig_critical = px.line(filtered_df, x="Traffic", y="CriticalDeliveryRatio", color="Algorithm", markers=True,
                                   title="Critical Delivery Ratio ★", color_discrete_map=color_discrete_map,
                                   template="plotly_dark")
            fig_critical.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_critical, width="stretch")

            fig_overhead = px.line(filtered_df, x="Traffic", y="OverheadRatio", color="Algorithm", markers=True,
                                   title="Overhead Ratio", color_discrete_map=color_discrete_map,
                                   template="plotly_dark")
            fig_overhead.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_overhead, width="stretch")

        with col2:
            fig_delay = px.line(filtered_df, x="Traffic", y="AvgCriticalDelay", color="Algorithm", markers=True,
                                title="Avg Critical Delay (seconds) ★", color_discrete_map=color_discrete_map,
                                template="plotly_dark")
            fig_delay.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_delay, width="stretch")

            fig_avg_delay = px.line(filtered_df, x="Traffic", y="AvgDelay", color="Algorithm", markers=True,
                                    title="Avg Overall Delay", color_discrete_map=color_discrete_map,
                                    template="plotly_dark")
            fig_avg_delay.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_avg_delay, width="stretch")

            fig_drops = px.line(filtered_df, x="Traffic", y="BufferDrops", color="Algorithm", markers=True,
                                title="Buffer Drops", color_discrete_map=color_discrete_map,
                                template="plotly_dark")
            fig_drops.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_drops, width="stretch")

    with tab2:
        st.subheader("Multi-Objective Trade-off Analysis")

        traffic_choice = st.selectbox("Select Traffic Level", ["Low", "Medium", "High"], index=1)
        selected_df = filtered_df[filtered_df['Traffic'] == traffic_choice]

        if not selected_df.empty:
            categories = [
                'Delivery Ratio',
                'Critical Delivery ★',
                'Speed (1/Delay)',
                'Efficiency (1/Overhead)',
                'Reliability (1/Drops)'
            ]

            fig_radar = go.Figure()

            for alg in selected_df['Algorithm']:
                row = selected_df[selected_df['Algorithm'] == alg].iloc[0]

                r_vals = [
                    row['DeliveryRatio'],
                    row.get('CriticalDeliveryRatio', row['DeliveryRatio']),
                    1 - min((row['AvgDelay'] / 2000), 1),
                    1 - min((row['OverheadRatio'] / 60), 1),
                    1 - min((row['BufferDrops'] / 5000), 1)
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
            st.plotly_chart(fig_radar, width="stretch")

            # Summary table
            st.subheader(f"📝 Summary at {traffic_choice} Traffic")
            summary_cols = ['Algorithm', 'DeliveryRatio', 'CriticalDeliveryRatio',
                            'AvgCriticalDelay', 'OverheadRatio', 'BufferDrops']
            avail_cols = [c for c in summary_cols if c in selected_df.columns]
            st.dataframe(selected_df[avail_cols].reset_index(drop=True), width="stretch")

    with tab3:
        st.subheader("Raw Simulation Results")
        st.dataframe(filtered_df, width="stretch")
        st.download_button(
            label="Download Aggregated Data as CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name='aggregated_results.csv',
            mime='text/csv',
        )

    with tab4:
        st.subheader("🧪 Live 4-Panel Simulation Engine")
        st.write("Launch the PyGame simulation to compare **Epidemic**, **Spray & Wait**, **Semantic**, and **Spatio-Semantic** algorithms simultaneously in a 4-panel side-by-side view.")

        st.markdown(
            """
            **Visual Legend:**
            - 🟡 **Drones**: Pulsing transmission range circles
            - 🟦 **Civilians**: Standard nodes (blue dots)
            - 🟥 **Responders**: Fast-moving agents (red dots)
            - 🟩 **Shelters**: Static base stations (green squares)
            - 🔴 **Critical Halos**: Nodes carrying critical messages
            - 🟢 **Green Lines**: Active packet transmissions
            - 📊 **Live Bars**: Real-time delivery ratio, critical delivery, and delay
            """
        )

        if st.button("▶️ LAUNCH COMPETITION DEMO", type="primary"):
            import subprocess
            import sys

            st.info("Simulation launched in a new window! Check your taskbar.")
            subprocess.Popen([sys.executable, "modern_multi_demo.py"])

else:
    st.warning("No data found. Run `python main.py` to generate results in the `plots/` directory.")

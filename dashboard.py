import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="DTN Routing Results", layout="wide", page_icon="📡")

st.title("📡 Spatio-Semantic DTN Routing Analysis")
st.markdown("Performance comparison: **Epidemic** vs **Spray & Wait** vs **Spatio-Semantic** across Low / Medium / High traffic.")


@st.cache_data
def load_data():
    base_dir = "plots"
    try:
        epidemic = pd.read_csv(os.path.join(base_dir, "epidemic_results.csv"))
        spray = pd.read_csv(os.path.join(base_dir, "spray_results.csv"))
        spatio = pd.read_csv(os.path.join(base_dir, "spatio_semantic_results.csv"))

        epidemic['Algorithm'] = 'Epidemic'
        spray['Algorithm'] = 'Spray & Wait'
        spatio['Algorithm'] = 'Spatio-Semantic'

        df = pd.concat([epidemic, spray, spatio], ignore_index=True)
        df['Traffic'] = pd.Categorical(df['Traffic'], ["Low", "Medium", "High"])
        return df
    except Exception as e:
        st.error(f"Error loading CSV files: {e}")
        return pd.DataFrame()


df = load_data()

if not df.empty:
    st.sidebar.header("Filter Options")
    selected_algs = st.sidebar.multiselect(
        "Select Algorithms to Compare",
        options=df['Algorithm'].unique(),
        default=df['Algorithm'].unique()
    )

    filtered_df = df[df['Algorithm'].isin(selected_algs)]

    color_map = {
        'Epidemic': '#EF553B',
        'Spray & Wait': '#00CC96',
        'Spatio-Semantic': '#19D3F3'
    }

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
            fig = px.line(filtered_df, x="Traffic", y="DeliveryRatio", color="Algorithm",
                          markers=True, title="Delivery Ratio", color_discrete_map=color_map,
                          template="plotly_dark")
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, width="stretch")

            fig = px.line(filtered_df, x="Traffic", y="CriticalDeliveryRatio", color="Algorithm",
                          markers=True, title="Critical Delivery Ratio ★", color_discrete_map=color_map,
                          template="plotly_dark")
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, width="stretch")

            fig = px.line(filtered_df, x="Traffic", y="OverheadRatio", color="Algorithm",
                          markers=True, title="Overhead Ratio", color_discrete_map=color_map,
                          template="plotly_dark")
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, width="stretch")

        with col2:
            fig = px.line(filtered_df, x="Traffic", y="AvgCriticalDelay", color="Algorithm",
                          markers=True, title="Avg Critical Delay (seconds) ★", color_discrete_map=color_map,
                          template="plotly_dark")
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, width="stretch")

            fig = px.line(filtered_df, x="Traffic", y="AvgDelay", color="Algorithm",
                          markers=True, title="Avg Overall Delay", color_discrete_map=color_map,
                          template="plotly_dark")
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, width="stretch")

            fig = px.line(filtered_df, x="Traffic", y="BufferDrops", color="Algorithm",
                          markers=True, title="Buffer Drops", color_discrete_map=color_map,
                          template="plotly_dark")
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, width="stretch")

    with tab2:
        st.subheader("Multi-Objective Trade-off Analysis")
        traffic_choice = st.selectbox("Select Traffic Level", ["Low", "Medium", "High"], index=1)
        sel = filtered_df[filtered_df['Traffic'] == traffic_choice]

        if not sel.empty:
            categories = [
                'Delivery Ratio',
                'Critical Delivery ★',
                'Speed (1/Delay)',
                'Efficiency (1/Overhead)',
                'Reliability (1/Drops)'
            ]
            fig_radar = go.Figure()
            for alg in sel['Algorithm']:
                row = sel[sel['Algorithm'] == alg].iloc[0]
                r_vals = [
                    row['DeliveryRatio'],
                    row.get('CriticalDeliveryRatio', row['DeliveryRatio']),
                    1 - min(row['AvgDelay'] / 2000, 1),
                    1 - min(row['OverheadRatio'] / 60, 1),
                    1 - min(row['BufferDrops'] / 5000, 1)
                ]
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_vals, theta=categories, fill='toself',
                    name=alg, line_color=color_map.get(alg)
                ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=True, template="plotly_dark", height=600
            )
            st.plotly_chart(fig_radar, width="stretch")

            st.subheader(f"📝 Summary at {traffic_choice} Traffic")
            cols = ['Algorithm', 'DeliveryRatio', 'CriticalDeliveryRatio',
                    'AvgCriticalDelay', 'OverheadRatio', 'BufferDrops']
            avail = [c for c in cols if c in sel.columns]
            st.dataframe(sel[avail].reset_index(drop=True), width="stretch")

    with tab3:
        st.subheader("Raw Simulation Results")
        st.dataframe(filtered_df, width="stretch")
        st.download_button(
            label="Download CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name='aggregated_results.csv',
            mime='text/csv',
        )

    with tab4:
        st.subheader("🧪 Live Fullscreen Simulation")
        st.write("Launch the PyGame simulation to compare **Epidemic**, **Spray & Wait**, and **Spatio-Semantic** in a fullscreen 3-panel view.")

        st.markdown("""
        **Legend:**
        - 🟡 **Drones**: Pulsing range circles, fast relays
        - 🟦 **Civilians**: Slow-moving carriers
        - 🟥 **Responders**: Fast agents
        - 🟩 **Shelters**: Static destinations (green squares)
        - 🔴 **Critical Halos**: Nodes carrying critical messages
        - 🟢 **Green Lines**: Active transmissions
        - Press **ESC** to exit fullscreen
        """)

        if st.button("▶️ LAUNCH FULLSCREEN DEMO", type="primary"):
            import subprocess, sys
            st.info("Simulation launched fullscreen! Press ESC to exit.")
            subprocess.Popen([sys.executable, "modern_multi_demo.py"])

else:
    st.warning("No data found. Run `python main.py` to generate results.")

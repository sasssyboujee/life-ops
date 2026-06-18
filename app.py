import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Life Operations Engine", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_ops.db")

# Custom Premium Styling
st.markdown("""
<style>
    /* Dark glassmorphic background & main body styling */
    .stApp {
        background: radial-gradient(circle at 20% 30%, #171923 0%, #0d0e12 100%);
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header typography */
    h1 {
        background: linear-gradient(135deg, #63B3ED 0%, #4FD1C5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem !important;
        margin-bottom: 2rem !important;
    }
    
    h2, h3 {
        color: #A0AEC0 !important;
        font-weight: 600;
    }

    /* Metric card styling */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #4FD1C5 !important;
    }
    
    /* Glassmorphic Container Cards */
    .card {
        background: rgba(26, 32, 44, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease-in-out;
    }
    .card:hover {
        transform: translateY(-4px);
        border-color: rgba(79, 209, 197, 0.2);
    }
</style>
""", unsafe_allow_html=True)

def load_data(query: str):
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.title("⚡ Life Operations Engine")

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("💳 Financial Dashboard")
    df_fin = load_data("SELECT * FROM transactions ORDER BY timestamp DESC")
    
    if df_fin.empty:
        st.info("No transaction records found. Add expenses via your Telegram bot.")
    else:
        total_spent = df_fin['amount_sgd'].sum()
        
        # Metric Layout
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Total Expenses", f"${total_spent:,.2f} SGD")
        with m_col2:
            st.metric("Transactions logged", len(df_fin))
            
        # Category breakdown chart
        fig_pie = px.pie(
            df_fin, 
            values='amount_sgd', 
            names='category', 
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Tealgrn,
            title="Spending by Category"
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#E2E8F0',
            margin=dict(t=40, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.subheader("Recent Ledger Entries")
        st.dataframe(
            df_fin[['timestamp', 'merchant', 'category', 'amount_sgd', 'notes']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Display receipts if any exist
        if 'image_blob' in df_fin.columns:
            df_fin_with_images = df_fin[df_fin['image_blob'].notna() & (df_fin['image_blob'] != b'')]
            if not df_fin_with_images.empty:
                st.write("---")
                st.subheader("🖼️ Logged Receipts")
                cols = st.columns(3)
                for idx, (_, row) in enumerate(df_fin_with_images.head(6).iterrows()):
                    with cols[idx % 3]:
                        st.image(
                            row['image_blob'], 
                            caption=f"{row['merchant']} - {row['amount_sgd']} SGD", 
                            use_container_width=True
                        )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("🏋️ Athletic Performance")
    df_gym = load_data("SELECT * FROM workouts ORDER BY timestamp DESC")
    
    if df_gym.empty:
        st.info("No workout records found. Log exercises via your Telegram bot.")
    else:
        df_gym['volume'] = df_gym['sets'] * df_gym['reps'] * df_gym['weight_kg']
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            max_volume = df_gym['volume'].max()
            st.metric("Peak Set Volume", f"{max_volume:,.0f} kg*reps")
        with m_col2:
            st.metric("Workouts logged", len(df_gym))
            
        # Workout volume chart
        fig_line = px.line(
            df_gym, 
            x='timestamp', 
            y='volume', 
            color='exercise',
            markers=True,
            color_discrete_sequence=px.colors.sequential.Electric,
            title="Volume Trajectory Over Time"
        )
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#E2E8F0',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
            margin=dict(t=40, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.subheader("Exercise Details")
        st.dataframe(
            df_gym[['timestamp', 'exercise', 'sets', 'reps', 'weight_kg', 'rpe', 'fatigue_flags']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Display workout log photos if any exist
        if 'image_blob' in df_gym.columns:
            df_gym_with_images = df_gym[df_gym['image_blob'].notna() & (df_gym['image_blob'] != b'')]
            if not df_gym_with_images.empty:
                st.write("---")
                st.subheader("📸 Workout Log Photos")
                cols = st.columns(3)
                for idx, (_, row) in enumerate(df_gym_with_images.head(6).iterrows()):
                    with cols[idx % 3]:
                        st.image(
                            row['image_blob'], 
                            caption=f"{row['exercise']} - {row['sets']}x{row['reps']} @ {row['weight_kg']}kg", 
                            use_container_width=True
                        )
    st.markdown('</div>', unsafe_allow_html=True)

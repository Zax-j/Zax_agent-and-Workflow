import streamlit as st

# 页面配置
st.set_page_config(
    page_title="AI项目演示中心",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义样式
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a2e;
        color: white;
    }
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        color: #00d4ff;
        margin-top: 100px;
    }
    .subtitle {
        text-align: center;
        font-size: 1rem;
        color: #aaa;
        margin-bottom: 50px;
    }
    .card {
        background-color: #16213e;
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        margin: 20px auto;
        width: 400px;
        box-shadow: 0 0 20px rgba(0,212,255,0.2);
        transition: 0.3s;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 30px rgba(0,212,255,0.4);
    }
</style>
""", unsafe_allow_html=True)

# 标题部分
st.markdown('<div class="main-title">好马须得配好鞍</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">/ 探索AI的无限可能 /</div>', unsafe_allow_html=True)

# 两列布局展示两个Demo
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <h3>🤖 Zax的智能体</h3>
        <p>全能型AI助手，支持RAG、知识图谱、OCR、图片理解多工具调用</p>
    </div>
    """, unsafe_allow_html=True)
   

with col2:
    st.markdown("""
    <div class="card">
        <h3>📋 工作日志生成器</h3>
        <p>LangGraph工作流，一键将零散日志生成标准周报</p>
    </div>
    """, unsafe_allow_html=True)

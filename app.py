# 🎯 社媒数据监控看板 - 小白专用版
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="📊 社媒监控看板", layout="wide", page_icon="📈")

# 侧边栏配置
st.sidebar.header("🔑 配置")
api_key = st.sidebar.text_input("TikHub API Key", type="password")
test_mode = st.sidebar.checkbox("🧪 调试模式", value=True)

# 主界面
st.title("📊 社媒数据监控看板")
st.markdown("*支持 TikTok • Instagram • Facebook • YouTube • X*")

# 输入区域
col1, col2, col3 = st.columns(3)
with col1:
    platform = st.selectbox("平台", ["tiktok", "instagram", "facebook", "youtube", "twitter"])
with col2:
    account_id = st.text_input("账号 ID/用户名", placeholder="如：charlidamelio")
with col3:
    data_type = st.selectbox("数据类型", ["用户信息", "视频列表", "评论数据"])

# 获取数据按钮
if st.button("🔍 查询数据", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ 请先在左侧输入 API Key")
        st.stop()
    if not account_id:
        st.error("❌ 请输入账号 ID")
        st.stop()
    
    with st.spinner(f"正在请求 {platform} 数据..."):
        try:
            # 智能拼接 URL
            prefixes = ["https://api.tikhub.io", "https://tikhub.io"]
            endpoint = f"/api/v1/{platform}/app/v3/fetch_user_post_videos_v3"
            
            success = False
            result = None
            for base in prefixes:
                url = f"{base}{endpoint}"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {"username": account_id, "count": 10}
                
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        success = True
                        break
                except:
                    continue
            
            if not success:
                st.error("❌ 请求失败，请检查：")
                st.markdown("- API Key 是否正确\n- 账号名称是否正确\n- TikHub 服务是否正常")
                st.stop()
            
            st.success(f"✅ 成功获取 {account_id} 的 {platform} 数据！")
            
            # 调试模式：显示原始数据
            if test_mode:
                with st.expander("🔧 查看原始返回数据"):
                    st.json(result)
            
            # 智能解析数据
            data_list = []
            if isinstance(result, dict):
                for key in ['data', 'results', 'videos', 'items', 'list']:
                    if key in result and isinstance(result[key], list):
                        data_list = result[key]
                        break
                if not data_list and 'data' in result and isinstance(result['data'], dict):
                    data_list = [result['data']]
            
            if data_list:
                df = pd.DataFrame(data_list)
                st.subheader("📋 数据预览")
                st.dataframe(df, use_container_width=True)
                
                numeric_cols = df.select_dtypes(include='number').columns.tolist()
                if numeric_cols:
                    st.subheader("📈 数据可视化")
                    x_col = st.selectbox("X 轴", df.columns.tolist())
                    y_col = st.selectbox("Y 轴", numeric_cols)
                    st.bar_chart(df.set_index(x_col)[y_col])
            else:
                st.warning("⚠️ 数据格式特殊，请查看原始 JSON")
                
        except Exception as e:
            st.error(f"❌ 错误：{str(e)}")
            st.info("💡 把错误信息发给我，我帮你改代码")

st.markdown("---")
st.caption("🛠️ AI 助手生成 | 有问题随时反馈")

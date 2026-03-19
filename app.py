# 🎯 Post Bridge 社媒数据监控看板 - 修正版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🌉 Post Bridge 数据看板", layout="wide", page_icon="🌉")

# ============================================
# 🔑 API Key 管理
# ============================================
def get_api_key():
    if "postbridge_api_key" in st.secrets:
        return st.secrets["postbridge_api_key"]
    
    with st.sidebar:
        api_key = st.text_input("Post Bridge API Key", type="password", 
                               help="格式：pb_live_xxxxxxxxxx")
        if api_key:
            st.session_state["api_key"] = api_key
    
    return st.session_state.get("api_key", None)

# ============================================
# 📡 API 请求函数
# ============================================
def fetch_social_accounts(api_key, limit=50, offset=0):
    """获取已连接的社交账号列表"""
    url = "https://api.post-bridge.com/v1/social-accounts"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"limit": limit, "offset": offset}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_analytics(api_key, account_id):
    """获取账号分析数据"""
    url = "https://api.post-bridge.com/v1/analytics"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"account_id": account_id}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("🌉 Post Bridge 社媒数据看板")
    st.markdown("*管理已连接的自有账号*")
    
    # 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ 请先在侧边栏输入 Post Bridge API Key")
        st.stop()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 设置")
        if st.button("🔄 刷新账号列表", use_container_width=True):
            st.session_state["refresh"] = True
    
    # 获取账号列表
    with st.spinner("正在获取账号列表..."):
        result = fetch_social_accounts(api_key, limit=50)
    
    if "error" in result:
        st.error(f"❌ 获取账号失败：{result['error']}")
        st.stop()
    
    # 解析数据 - 注意这里的数据结构！
    accounts_data = result.get("data", [])
    meta = result.get("meta", {})
    
    if not accounts_data:
        st.warning("⚠️ 未找到已连接的账号")
        st.markdown("""
        ### 📌 如何连接账号：
        1. 登录 [Post Bridge Dashboard](https://post-bridge.com)
        2. 点击 **Connect Account**
        3. 授权你的社交账号
        4. 刷新此页面
        """)
        st.stop()
    
    # 显示账号统计
    total_accounts = meta.get("total", len(accounts_data))
    st.subheader(f"📊 已连接 {total_accounts} 个账号")
    
    # 按平台分组统计
    platform_counts = {}
    for acc in accounts_data:
        platform = acc.get("platform", "unknown")
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总账号数", total_accounts)
    with col2:
        st.metric("平台数", len(platform_counts))
    with col3:
        st.metric("本次显示", len(accounts_data))
    
    # 显示平台分布
    st.write("**平台分布：**")
    platform_text = " | ".join([f"{k}: {v}" for k, v in platform_counts.items()])
    st.info(platform_text)
    
    st.divider()
    
    # 账号列表展示
    st.subheader("📱 账号列表")
    
    # 创建数据表格
    rows = []
    for idx, acc in enumerate(accounts_data):
        rows.append({
            "序号": idx + 1,
            "平台": acc.get("platform", "N/A").upper(),
            "用户名": f"@{acc.get('username', 'N/A')}",
            "账号ID": acc.get("id", "N/A")
        })
    
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 账号选择器
    st.divider()
    st.subheader("🔍 查看账号详情")
    
    account_options = {f"@{acc.get('username')} ({acc.get('platform').upper()})": acc 
                       for acc in accounts_data}
    
    selected_name = st.selectbox("选择账号", list(account_options.keys()))
    selected_account = account_options[selected_name]
    account_id = selected_account.get("id")
    
    st.write(f"**当前账号：** {selected_name} | **ID:** `{account_id}`")
    
    # 获取分析数据按钮
    if st.button("📊 获取分析数据", type="primary"):
        with st.spinner("正在获取分析数据..."):
            analytics_result = fetch_analytics(api_key, account_id)
        
        if "error" in analytics_result:
            st.error(f"❌ 获取分析数据失败：{analytics_result['error']}")
        else:
            st.success("✅ 数据获取成功！")
            
            # 显示原始数据（调试用）
            with st.expander("📄 查看原始 JSON"):
                st.json(analytics_result)
            
            # 尝试解析分析数据
            data = analytics_result.get("data", {})
            
            if isinstance(data, dict):
                # 显示常见指标
                st.subheader("📈 核心指标")
                
                metrics_to_show = {}
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        metrics_to_show[key] = value
                
                if metrics_to_show:
                    cols = st.columns(min(4, len(metrics_to_show)))
                    for idx, (key, value) in enumerate(metrics_to_show.items()):
                        with cols[idx % 4]:
                            label = key.replace("_", " ").title()
                            if isinstance(value, float) and value < 1:
                                st.metric(label, f"{value:.2%}")
                            else:
                                st.metric(label, f"{int(value):,}")
                else:
                    st.warning("⚠️ 未找到数值型指标")
            else:
                st.write("数据结构：", type(data))
                st.json(data)

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ powered by Post Bridge API & Streamlit")

if __name__ == "__main__":
    main()

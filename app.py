# 🎯 社媒数据监控看板 - Post Bridge 版本
# 用于管理已连接的自有账号
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📊 社媒监控看板", layout="wide", page_icon="📈")

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
# 📡 获取账号列表
# ============================================
def get_connected_accounts(api_key):
    """获取已连接的社交账号"""
    url = "https://api.post-bridge.com/v1/social-accounts"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# ============================================
# 📊 获取分析数据
# ============================================
def get_analytics(api_key, account_id=None):
    """获取账号分析数据"""
    url = "https://api.post-bridge.com/v1/analytics"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    params = {}
    if account_id:
        params["account_id"] = account_id
    
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
    st.title("📊 社媒数据监控看板")
    st.markdown("*Powered by Post Bridge • 管理已连接的自有账号*")
    
    # 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ **请先配置 API Key！**\n\n在左侧侧边栏输入你的 Post Bridge API Key")
        st.stop()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # 刷新数据按钮
        if st.button("🔄 刷新数据", use_container_width=True):
            st.session_state["refresh"] = True
        
        # 显示 API Key 状态
        if api_key.startswith("pb_live_"):
            st.success("✅ API Key 格式正确")
        else:
            st.warning("⚠️ API Key 格式可能不正确")
    
    # 获取已连接账号
    with st.spinner("正在获取已连接账号..."):
        accounts_data = get_connected_accounts(api_key)
    
    if "error" in accounts_data:
        st.error(f"❌ 获取账号失败：{accounts_data['error']}")
        st.info("💡 请检查：1) API Key 是否正确 2) 账号是否已在 Post Bridge 连接")
        st.stop()
    
    # 解析账号列表
    accounts = accounts_data.get("data", [])
    
    if not accounts:
        st.warning("⚠️ 未找到已连接的账号\n\n请先在 Post Bridge 后台连接你的 TikTok/Instagram 账号")
        st.markdown("""
        ### 📌 连接账号步骤：
        1. 登录 [Post Bridge](https://post-bridge.com)
        2. 进入 Dashboard
        3. 点击 Connect Account
        4. 授权你的 TikTok/Instagram 账号
        """)
        st.stop()
    
    # 账号选择器
    st.subheader("📱 选择账号")
    account_options = {f"{acc.get('platform', 'Unknown')} - @{acc.get('username', 'Unknown')}": acc 
                       for acc in accounts}
    
    selected_name = st.selectbox("选择要查看的账号", list(account_options.keys()))
    selected_account = account_options[selected_name]
    
    # 显示账号信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平台", selected_account.get("platform", "N/A"))
    with col2:
        st.metric("用户名", f"@{selected_account.get('username', 'N/A')}")
    with col3:
        st.metric("账号 ID", selected_account.get("id", "N/A")[:20] + "...")
    
    # 获取分析数据
    st.divider()
    st.subheader("📈 数据分析")
    
    with st.spinner("正在获取分析数据..."):
        analytics_data = get_analytics(api_key, selected_account.get("id"))
    
    if "error" in analytics_data:
        st.error(f"❌ 获取分析数据失败：{analytics_data['error']}")
    else:
        st.success("✅ 数据获取成功！")
        
        # 显示原始数据（可折叠）
        with st.expander("📄 查看原始 JSON 数据"):
            st.json(analytics_data)
        
        # 智能解析数据
        data = analytics_data.get("data", {})
        
        # 尝试不同的数据结构
        metrics = {}
        
        # 方案 1: 直接包含指标
        if isinstance(data, dict):
            metrics = data
        
        # 方案 2: 在 data 字段里
        elif "data" in analytics_data:
            metrics = analytics_data["data"]
        
        # 显示核心指标
        if metrics:
            st.subheader("📊 核心指标")
            
            # 常见指标映射
            metric_mapping = {
                "followers": "粉丝数",
                "following": "关注数",
                "posts": "帖子数",
                "likes": "点赞数",
                "comments": "评论数",
                "shares": "分享数",
                "views": "观看数",
                "engagement_rate": "互动率",
                "reach": "触达人数",
                "impressions": "展示次数"
            }
            
            # 显示找到的指标
            cols = st.columns(min(4, len(metrics)))
            for idx, (key, value) in enumerate(metrics.items()):
                if isinstance(value, (int, float)):
                    label = metric_mapping.get(key, key)
                    with cols[idx % 4]:
                        if isinstance(value, float) and value < 1:
                            st.metric(label, f"{value:.2%}")
                        else:
                            st.metric(label, f"{int(value):,}")
        
        # 显示帖子/视频列表（如果有）
        if "posts" in analytics_data or "videos" in analytics_data or "content" in analytics_data:
            st.divider()
            st.subheader("📹 内容列表")
            
            content_list = (analytics_data.get("posts") or 
                          analytics_data.get("videos") or 
                          analytics_data.get("content") or [])
            
            if content_list:
                # 创建数据表
                rows = []
                for item in content_list[:10]:  # 只显示前 10 条
                    row = {
                        "标题/描述": item.get("caption", item.get("title", "N/A"))[:50],
                        "发布时间": item.get("created_at", item.get("published_at", "N/A")),
                        "点赞": item.get("likes", item.get("like_count", 0)),
                        "评论": item.get("comments", item.get("comment_count", 0)),
                        "分享": item.get("shares", item.get("share_count", 0)),
                    }
                    rows.append(row)
                
                if rows:
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)
    
    # 下载按钮
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 下载账号数据 (JSON)", use_container_width=True):
            import json
            json_str = json.dumps(accounts_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="点击下载",
                data=json_str,
                file_name=f"accounts_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
    with col2:
        if st.button("📥 下载分析数据 (JSON)", use_container_width=True):
            import json
            json_str = json.dumps(analytics_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="点击下载",
                data=json_str,
                file_name=f"analytics_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ powered by Post Bridge API & Streamlit | 仅显示已连接的自有账号")

if __name__ == "__main__":
    main()

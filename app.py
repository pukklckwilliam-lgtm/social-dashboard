# 🎯 社媒数据监控看板 - Post Bridge 专属版
# 支持：已连接的自有账号数据分析
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📊 Post Bridge 数据看板", layout="wide", page_icon="🌉")

# ============================================
# 🔑 API Key 管理
# ============================================
def get_api_key():
    # 优先从 Secrets 读取
    if "postbridge_api_key" in st.secrets:
        return st.secrets["postbridge_api_key"]
    
    # 备用：侧边栏输入
    with st.sidebar:
        api_key = st.text_input("Post Bridge API Key", type="password", 
                               value="pb_live_KNdQj...",  # 默认填充你的 Key 格式
                               help="格式：pb_live_xxxxxxxxxx")
        if api_key:
            st.session_state["api_key"] = api_key
    
    return st.session_state.get("api_key", None)

# ============================================
# 📡 Post Bridge API 请求
# ============================================
def fetch_connected_accounts(api_key):
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

def fetch_account_analytics(api_key, account_id):
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

def fetch_account_posts(api_key, account_id, limit=10):
    """获取账号帖子/视频列表"""
    # 注意：Post Bridge 的帖子端点可能不同，这里尝试通用路径
    url = "https://api.post-bridge.com/v1/posts"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"account_id": account_id, "limit": limit}
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
    st.markdown("*仅显示已在 Post Bridge 后台连接的自有账号*")
    
    # 1. 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ 请先在侧边栏输入 Post Bridge API Key")
        st.stop()
    
    if not api_key.startswith("pb_live_"):
        st.error("❌ API Key 格式不正确，应以 pb_live_ 开头")
        st.stop()
    
    # 2. 获取已连接账号
    with st.spinner("正在获取已连接账号..."):
        accounts_result = fetch_connected_accounts(api_key)
    
    if "error" in accounts_result:
        st.error(f"❌ 获取账号列表失败：{accounts_result['error']}")
        st.info("💡 请检查：1) API Key 是否正确 2) 是否在 Post Bridge 后台连接了账号")
        st.stop()
    
    # 解析账号列表
    # 假设返回结构：{"data": [{"id": "123", "platform": "tiktok", "username": "xxx"}, ...]}
    accounts = accounts_result.get("data", [])
    
    # 筛选 TikTok 账号 (可根据需要扩展)
    tiktok_accounts = [acc for acc in accounts if acc.get("platform", "").lower() == "tiktok"]
    
    if not tiktok_accounts:
        st.warning("⚠️ 未找到已连接的 TikTok 账号")
        st.markdown("""
        ### 📌 如何连接账号：
        1. 登录 [Post Bridge Dashboard](https://post-bridge.com)
        2. 点击 **Connect Account**
        3. 授权你的 TikTok 账号
        4. 刷新此页面
        """)
        st.stop()
    
    # 3. 账号选择器
    st.sidebar.header("⚙️ 设置")
    account_options = {f"@{acc.get('username', 'Unknown')} ({acc.get('id', '')[:8]}...)": acc for acc in tiktok_accounts}
    selected_name = st.sidebar.selectbox("选择 TikTok 账号", list(account_options.keys()))
    selected_account = account_options[selected_name]
    account_id = selected_account.get("id")
    
    st.info(f"**当前账号：** {selected_name} | **ID:** `{account_id}`")
    
    # 4. 获取数据按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 刷新分析数据", use_container_width=True):
            st.session_state['load_analytics'] = True
    with col2:
        if st.button("🎬 刷新视频列表", use_container_width=True):
            st.session_state['load_posts'] = True
    
    # --- 显示分析数据 ---
    if st.session_state.get('load_analytics', False) or 'analytics_data' not in st.session_state:
        st.session_state['load_analytics'] = False
        with st.spinner("正在获取分析数据..."):
            analytics_result = fetch_account_analytics(api_key, account_id)
            st.session_state['analytics_data'] = analytics_result
        
        if "error" in st.session_state['analytics_data']:
            st.error(f"❌ 分析数据获取失败：{st.session_state['analytics_data']['error']}")
        else:
            st.subheader("📈 账号核心指标")
            # 尝试解析 Post Bridge 返回的指标
            data = st.session_state['analytics_data'].get("data", {})
            if isinstance(data, dict):
                cols = st.columns(4)
                metrics = [
                    ("总粉丝数", data.get("followers", data.get("follower_count", "N/A"))),
                    ("总关注数", data.get("following", data.get("following_count", "N/A"))),
                    ("总点赞数", data.get("likes", data.get("total_likes", "N/A"))),
                    ("总视频数", data.get("videos", data.get("video_count", "N/A")))
                ]
                for i, (label, value) in enumerate(metrics):
                    with cols[i % 4]:
                        st.metric(label, f"{value:,}" if isinstance(value, int) else value)
            else:
                st.json(data) # 如果结构不对，显示原始数据调试
    
    # --- 显示视频列表 ---
    if st.session_state.get('load_posts', False) or 'posts_data' not in st.session_state:
        st.session_state['load_posts'] = False
        with st.spinner("正在获取视频列表..."):
            posts_result = fetch_account_posts(api_key, account_id)
            st.session_state['posts_data'] = posts_result
            
        if "error" in st.session_state['posts_data']:
            st.error(f"❌ 视频列表获取失败：{st.session_state['posts_data']['error']}")
            st.info("💡 Post Bridge 可能需要不同的端点来获取帖子列表，请查阅文档。")
        else:
            st.subheader("🎬 最新视频")
            # 尝试解析帖子列表
            posts = st.session_state['posts_data'].get("data", [])
            
            if isinstance(posts, list) and len(posts) > 0:
                # 构建表格
                rows = []
                for post in posts[:10]: # 只显示前 10 个
                    # 根据实际返回结构调整字段
                    rows.append({
                        "帖子 ID": post.get("id", "N/A")[:15],
                        "类型": post.get("media_type", "video"),
                        "发布时间": post.get("created_at", post.get("timestamp", "N/A"))[:10],
                        "点赞数": post.get("like_count", post.get("likes", 0)),
                        "评论数": post.get("comment_count", post.get("comments", 0)),
                        "链接": f"[查看]({post.get('permalink', post.get('url', '#'))})"
                    })
                
                if rows:
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 简单图表
                    if "点赞数" in df.columns:
                        st.bar_chart(df.set_index("帖子 ID")["点赞数"])
                else:
                    st.warning("⚠️ 未解析到视频数据，请查看下方原始 JSON 调试")
                    st.json(posts)
            else:
                st.warning("⚠️ 返回数据格式不是列表，请查看原始 JSON")
                st.json(posts)
    
    # --- 调试区域 ---
    with st.expander("🔍 查看原始 API 返回 (调试用)"):
        st.write("**分析数据：**")
        st.json(st.session_state.get('analytics_data', {}))
        st.write("**视频数据：**")
        st.json(st.session_state.get('posts_data', {}))

if __name__ == "__main__":
    # 初始化 session_state
    if 'analytics_data' not in st.session_state:
        st.session_state['analytics_data'] = None
    if 'posts_data' not in st.session_state:
        st.session_state['posts_data'] = None
    main()

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ powered by Post Bridge API & Streamlit | 仅显示已连接的自有账号")

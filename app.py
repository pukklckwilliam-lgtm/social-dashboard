# 🎯 多产品社媒监控系统 - 可添加产品版
import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="📊 社媒监控系统", layout="wide", page_icon="📱")

# ============================================
# 💾 配置文件管理
# ============================================
CONFIG_FILE = "products_config.json"

def load_products_config():
    """加载产品配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    # 默认配置
    return {
        "PhotoRevive.AI": {
            "image": "https://p16-common-sign.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/a62a32b54c026de51797e4862fd4ecd2~tplv-tiktokx-cropcenter:300:300.webp",
            "description": "AI 照片修复工具",
            "accounts": {
                "TikTok": {
                    "username": "photorevive.ai",
                    "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v2",
                    "param_name": "unique_id"
                }
            }
        }
    }

def save_products_config(config):
    """保存产品配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"保存失败：{e}")
        return False

# 加载配置
PRODUCTS_CONFIG = load_products_config()

# ============================================
# 🔑 API Key
# ============================================
API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

def get_api_key():
    try:
        if hasattr(st, 'secrets') and "tikhub_api_key" in st.secrets:
            return st.secrets["tikhub_api_key"].strip()
    except:
        pass
    
    with st.sidebar:
        api_key = st.text_input("🔑 API Key", type="password", value=API_KEY)
        if api_key:
            st.session_state["api_key"] = api_key.strip()
    
    return st.session_state.get("api_key", API_KEY)

# ============================================
# 📡 数据抓取
# ============================================
def fetch_tiktok_data(username):
    """抓取 TikTok 数据"""
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"unique_id": username, "count": 20}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return result
        return None
    except:
        return None

# ============================================
# 🎨 页面状态管理
# ============================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False

# ============================================
# ➕ 添加产品表单
# ============================================
def render_add_product_form():
    """渲染添加产品表单"""
    st.title("➕ 添加新产品")
    
    if st.button("← 返回首页"):
        st.session_state.show_add_form = False
        st.rerun()
    
    with st.form("add_product_form", clear_on_submit=False):
        st.subheader("📝 产品信息")
        
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("产品名称 *", placeholder="例如：MyNewApp")
            description = st.text_input("产品描述", placeholder="例如：AI 工具")
        
        with col2:
            image_url = st.text_input("产品图片 URL", placeholder="https://...")
            tiktok_username = st.text_input("TikTok 账号名 *", placeholder="例如：myapp")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("✅ 添加产品", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ 取消", use_container_width=True)
        
        if cancel:
            st.session_state.show_add_form = False
            st.rerun()
        
        if submit:
            if not product_name or not tiktok_username:
                st.error("❌ 请填写产品名称和 TikTok 账号名")
            elif product_name in PRODUCTS_CONFIG:
                st.error(f"❌ 产品 '{product_name}' 已存在")
            else:
                # 添加新产品
                PRODUCTS_CONFIG[product_name] = {
                    "image": image_url if image_url else "https://via.placeholder.com/300/4A90E2/FFFFFF?text=" + product_name,
                    "description": description if description else "暂无描述",
                    "accounts": {
                        "TikTok": {
                            "username": tiktok_username,
                            "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v2",
                            "param_name": "unique_id"
                        }
                    }
                }
                
                # 保存配置
                if save_products_config(PRODUCTS_CONFIG):
                    st.success(f"✅ 产品 '{product_name}' 添加成功！")
                    st.info("🔄 正在返回首页...")
                    st.session_state.show_add_form = False
                    st.rerun()
                else:
                    st.error("❌ 保存配置失败")

# ============================================
# 🏠 首页：产品总览
# ============================================
def render_home_page():
    st.title("📊 社媒产品监控系统")
    st.markdown("*监控多产品社媒数据*")
    
    # 添加产品按钮
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("➕ 添加产品", use_container_width=True):
            st.session_state.show_add_form = True
            st.rerun()
    
    # 产品卡片网格
    cols = st.columns(min(3, len(PRODUCTS_CONFIG)))
    
    for idx, (product_name, config) in enumerate(PRODUCTS_CONFIG.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                # 产品图片
                try:
                    if config.get("image"):
                        st.image(config["image"], use_container_width=True)
                    else:
                        st.write("🖼️")
                except:
                    st.write("🖼️")
                
                # 产品名称
                st.subheader(product_name)
                st.caption(config.get("description", ""))
                
                # 账号数量
                st.metric("平台数", len(config.get("accounts", {})))
                
                # 按钮组
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("查看详情", key=f"view_{product_name}", use_container_width=True):
                        st.session_state.selected_product = product_name
                        st.session_state.current_page = "product"
                        st.rerun()
                with col2:
                    if st.button("🗑️ 删除", key=f"delete_{product_name}", use_container_width=True):
                        if product_name in PRODUCTS_CONFIG:
                            del PRODUCTS_CONFIG[product_name]
                            save_products_config(PRODUCTS_CONFIG)
                            st.rerun()

# ============================================
# 📱 产品详情页
# ============================================
def render_product_page():
    product_name = st.session_state.selected_product
    
    # 验证产品是否存在
    if not product_name or product_name not in PRODUCTS_CONFIG:
        st.warning("⚠️ 产品不存在或已删除")
        if st.button("← 返回首页"):
            st.session_state.current_page = "home"
            st.session_state.selected_product = None
            st.rerun()
        return
    
    config = PRODUCTS_CONFIG[product_name]
    
    # 返回按钮
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 返回"):
            st.session_state.current_page = "home"
            st.session_state.selected_product = None
            st.rerun()
    
    st.title(f"📱 {product_name}")
    st.markdown(f"*{config.get('description', '')}*")
    
    # 获取所有平台数据
    st.subheader("📊 各平台数据总览")
    
    # 存储各平台数据
    platform_data = {}
    
    # 获取 TikTok 数据
    if "TikTok" in config.get("accounts", {}):
        tiktok_config = config["accounts"]["TikTok"]
        username = tiktok_config["username"]
        
        with st.spinner(f"正在获取 TikTok @{username} ..."):
            result = fetch_tiktok_data(username)
            
            if result:
                data_content = result.get("data", {})
                video_list = data_content.get("aweme_list", [])
                
                if video_list:
                    # 账号信息
                    author = video_list[0].get("author", {})
                    platform_data["TikTok"] = {
                        "username": author.get("unique_id", username),
                        "nickname": author.get("nickname", ""),
                        "followers": author.get("follower_count", 0),
                        "following": author.get("following_count", 0),
                        "total_likes": author.get("total_favorited", 0),
                        "videos": video_list
                    }
                    
                    # 显示账号卡片
                    st.success(f"✅ TikTok: @{platform_data['TikTok']['username']}")
                    
                    # 核心指标
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("粉丝数", f"{platform_data['TikTok']['followers']:,}")
                    with col2:
                        st.metric("关注数", f"{platform_data['TikTok']['following']:,}")
                    with col3:
                        st.metric("总获赞", f"{platform_data['TikTok']['total_likes']:,}")
                    
                    # 主页链接
                    st.markdown(f"**🔗 [访问 TikTok 主页](https://tiktok.com/@{username})**")
                    
                    # 粉丝分布
                    st.divider()
                    st.subheader("📈 粉丝分布")
                    
                    pie_data = pd.DataFrame({
                        "平台": ["TikTok", "其他平台"],
                        "粉丝数": [platform_data['TikTok']['followers'], 0]
                    })
                    st.write("💡 待补充其他平台数据后显示完整分布")
                    st.dataframe(pie_data, use_container_width=True, hide_index=True)
                    
                    # 视频数据柱状图
                    st.divider()
                    st.subheader("📊 视频表现")
                    
                    video_stats = []
                    for i, video in enumerate(video_list[:10]):
                        stats = video.get("statistics", {})
                        video_stats.append({
                            "视频": f"视频{i+1}",
                            "播放量": stats.get("play_count", 0),
                            "点赞数": stats.get("digg_count", 0)
                        })
                    
                    df = pd.DataFrame(video_stats)
                    st.bar_chart(df.set_index('视频')['播放量'], use_container_width=True)
                    st.bar_chart(df.set_index('视频')['点赞数'], use_container_width=True)
                    
                    # 视频封面墙
                    st.divider()
                    st.subheader("🎬 视频列表")
                    
                    video_cols = st.columns(3)
                    for idx, video in enumerate(video_list[:9]):
                        with video_cols[idx % 3]:
                            cover_url = video.get("video", {}).get("cover", {}).get("url_list", [""])[0]
                            if cover_url:
                                st.image(cover_url, use_container_width=True)
                            
                            desc = video.get("desc", "无描述")[:50] + "..."
                            st.caption(desc)
                            
                            stats = video.get("statistics", {})
                            st.write(f"👁 {stats.get('play_count', 0):,} | ❤ {stats.get('digg_count', 0):,}")
                            
                            share_url = video.get("share_url", "")
                            if share_url:
                                st.markdown(f"[观看视频]({share_url})")
                    
                    if len(video_list) > 9:
                        if st.button(f"查看更多（共{len(video_list)}个视频）"):
                            st.info("显示全部视频功能开发中...")
                else:
                    st.warning("⚠️ 未找到视频数据")
            else:
                st.error("❌ 获取 TikTok 数据失败")
    
    # 其他平台（预留）
    st.divider()
    st.subheader("🚧 其他平台")
    st.info("Instagram、YouTube、X 平台功能开发中...")

# ============================================
# 🚀 主程序
# ============================================
def main():
    api_key = get_api_key()
    
    # 页面路由
    if st.session_state.get("show_add_form", False):
        render_add_product_form()
    elif st.session_state.current_page == "home":
        render_home_page()
    elif st.session_state.current_page == "product":
        render_product_page()

if __name__ == "__main__":
    main()

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ powered by TikHub API & Streamlit")

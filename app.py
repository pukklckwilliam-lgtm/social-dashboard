# 🎯 Post Bridge 社媒数据看板 - 调试版
import streamlit as st
import requests

st.set_page_config(page_title="🌉 Post Bridge 社媒数据看板", layout="wide")

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
def fetch_connected_accounts(api_key):
    """获取已连接的社交账号"""
    url = "https://api.post-bridge.com/v1/social-accounts"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json(), "status_code": response.status_code}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", 
                    "details": response.text[:500], "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": None}

# ============================================
# 🎨 主界面
# ============================================
st.title("🌉 Post Bridge 社媒数据看板 - 调试模式")
st.markdown("*调试 API 返回数据结构*")

# 获取 API Key
api_key = get_api_key()

if not api_key:
    st.warning("⚠️ 请先在侧边栏输入 Post Bridge API Key")
    st.stop()

if not api_key.startswith("pb_live_"):
    st.error("❌ API Key 格式不正确，应以 pb_live_ 开头")
    st.stop()

# 获取账号数据
st.subheader("📡 API 请求结果")
with st.spinner("正在获取数据..."):
    result = fetch_connected_accounts(api_key)

# 显示原始响应
st.write(f"**HTTP 状态码:** `{result.get('status_code')}`")

if result.get('success'):
    st.success("✅ 请求成功")
    
    # 显示原始 JSON
    st.subheader("📄 原始 JSON 数据")
    st.json(result['data'])
    
    # 分析数据结构
    st.subheader("🔍 数据结构分析")
    data = result['data']
    
    if isinstance(data, dict):
        st.write("**顶层键名：**", list(data.keys()))
        
        # 检查常见键
        for key in ['data', 'accounts', 'items', 'result']:
            if key in data:
                st.write(f"\n**'{key}' 字段内容：**")
                value = data[key]
                if isinstance(value, list):
                    st.write(f"- 类型：列表，长度：{len(value)}")
                    if len(value) > 0:
                        st.write(f"- 第一个元素类型：{type(value[0])}")
                        if isinstance(value[0], dict):
                            st.write(f"- 第一个元素的键：{list(value[0].keys())}")
                            # 检查 platform 字段
                            if 'platform' in value[0]:
                                st.write(f"- platform 字段值示例：{value[0]['platform']}")
                elif isinstance(value, dict):
                    st.write(f"- 类型：字典")
                    st.write(f"- 键：{list(value.keys())}")
    
    # 尝试不同的解析方式
    st.subheader("🔧 尝试不同的解析方式")
    
    # 方式1：直接检查 data 字段
    if 'data' in data and isinstance(data['data'], list):
        accounts = data['data']
        st.write(f"✅ 方式1成功：找到 {len(accounts)} 个账号")
        for acc in accounts[:3]:  # 只显示前3个
            st.write(f"- {acc.get('username', 'N/A')} | 平台：{acc.get('platform', 'N/A')}")
    
    # 方式2：检查 accounts 字段
    elif 'accounts' in data and isinstance(data['accounts'], list):
        accounts = data['accounts']
        st.write(f"✅ 方式2成功：找到 {len(accounts)} 个账号")
        for acc in accounts[:3]:
            st.write(f"- {acc.get('username', 'N/A')} | 平台：{acc.get('platform', 'N/A')}")
    
    # 方式3：检查 items 字段
    elif 'items' in data and isinstance(data['items'], list):
        accounts = data['items']
        st.write(f"✅ 方式3成功：找到 {len(accounts)} 个账号")
        for acc in accounts[:3]:
            st.write(f"- {acc.get('username', 'N/A')} | 平台：{acc.get('platform', 'N/A')}")
    
    else:
        st.warning("⚠️ 未找到标准的账号列表字段")
        st.write("请查看上面的原始 JSON 数据，告诉我账号数据在哪个字段里")

else:
    st.error(f"❌ 请求失败：{result.get('error')}")
    if 'details' in result:
        st.code(result['details'])

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ 调试模式 | 请截图或复制上面的 JSON 数据发给我")

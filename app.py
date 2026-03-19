# 🎯 TikHub API Tester
import streamlit as st
import requests

st.title("🔧 TikHub API Key Tester")

api_key = st.text_input("Enter your TikHub API Key:", type="password")

if st.button("Test API Key"):
    if not api_key:
        st.error("Please enter API Key")
        st.stop()
    
    # Test 1: Check user info endpoint
    st.write("### Test 1: Check User Info")
    url = "https://api.tikhub.io/api/v1/tikhub/user/get_user_info"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        st.write(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            st.success("✅ API Key is valid!")
            st.json(response.json())
        else:
            st.error(f"❌ API Key invalid: {response.status_code}")
            st.text(response.text)
    except Exception as e:
        st.error(f"Error: {e}")
    
    # Test 2: Try TikTok endpoint with different methods
    st.write("### Test 2: TikTok User Profile")
    url = "https://api.tikhub.io/api/v1/tiktok/web/fetch_user_profile"
    params = {"unique_id": "charlidamelio"}
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    st.write(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        st.success("✅ TikTok endpoint works!")
        st.json(response.json())
    else:
        st.error(f"❌ TikTok endpoint failed: {response.status_code}")
        st.text(response.text[:500])

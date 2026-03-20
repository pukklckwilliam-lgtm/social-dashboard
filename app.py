def fetch_tiktok_data_paginated(username, target_count=30):
    """分页抓取 TikTok 数据 - 根据工作流修复版"""
    
    # 第1步：获取 sec_user_id
    sec_user_id = get_sec_user_id(username)
    if not sec_user_id:
        return {"success": False, "error": "无法获取用户信息，请检查账号名是否正确"}
    
    # 第2步：循环抓取视频
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    cursor = "0"
    max_per_request = 20
    max_loops = 4  # ✅ 改成 4 次 = 80条
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for loop in range(max_loops):
        status_text.text(f"正在抓取第 {loop + 1}/{max_loops} 页...")
        
        params = {
            "sec_user_id": sec_user_id,
            "count": max_per_request,
            "max_cursor": cursor,
            "sort_type": 0
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    data = result.get('data', {})
                    video_list = data.get('aweme_list', [])
                    
                    if not video_list:
                        status_text.text("✅ 没有更多视频了")
                        break
                    
                    all_videos.extend(video_list)
                    
                    # 更新进度
                    progress = (loop + 1) / max_loops
                    progress_bar.progress(progress)
                    
                    status_text.text(f"✅ 已抓取 {len(all_videos)} 条视频")
                    
                    # 检查是否还有更多
                    if not data.get('has_more'):
                        status_text.text("✅ 已抓取所有可用视频")
                        break
                    
                    # 更新 cursor
                    cursor = str(data.get('max_cursor', '0'))
                    if cursor == '0':
                        break
                    
                else:
                    status_text.text(f"❌ API 错误：{result.get('message', '')}")
                    break
            else:
                status_text.text(f"❌ HTTP {response.status_code}")
                break
                
        except Exception as e:
            status_text.text(f"❌ 请求异常：{str(e)}")
            break
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ 完成！共抓取 {len(all_videos)} 条视频")
    
    return {
        "success": True,
        "videos": all_videos[:target_count] if target_count > 0 else all_videos,
        "total_fetched": len(all_videos)
    }

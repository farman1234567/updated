import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# ========================
# YOUTUBE API CONFIG
# ========================
API_KEY = "AIzaSyDiTQuy87y097i6Ya7M8joNSH4hKyM2-dU"

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

# ========================
# STREAMLIT UI
# ========================
st.set_page_config(
    page_title="Universal YouTube Trend Tool",
    layout="wide"
)

st.title("🚀 Multi-Niche YouTube Trend & Script Tool")

keyword = st.text_input("Enter Keyword (e.g., History, Cars, Quiz):", "")
days = st.number_input("Search videos from last X days", 1, 30, 7)
min_views = st.number_input("Minimum views", value=8000, step=1000)
max_subs = st.number_input("Maximum channel subscribers", value=3000, step=500)

MIN_DURATION_MINUTES = 5  # Filter: 5+ minutes

# ========================
# HELPERS
# ========================
def yt_get(url, params):
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def iso_duration_to_seconds(duration):
    """Convert ISO 8601 duration (PT1H2M3S) to seconds"""
    hours = minutes = seconds = 0
    duration = duration.replace("PT", "")
    if "H" in duration:
        hours = int(duration.split("H")[0])
        duration = duration.split("H")[1]
    if "M" in duration:
        minutes = int(duration.split("M")[0])
        duration = duration.split("M")[1]
    if "S" in duration:
        seconds = int(duration.replace("S",""))
    return hours*3600 + minutes*60 + seconds

# ========================
# SCRIPT GENERATOR
# ========================
def generate_generic_script(title, keyword):
    return f"""
{title}

Today, we explore {keyword.lower()}.

This topic has captured the attention of millions because it offers insight, excitement, or curiosity.

Let’s dive deep and uncover the stories, facts, and secrets behind {keyword.lower()}.

Stay tuned as we explore the most important points, the hidden gems, and the lessons you won’t want to miss.
"""

# ========================
# THUMBNAIL PROMPT GENERATOR
# ========================
def generate_thumbnail_prompt(title):
    return f"""
Ultra-cinematic YouTube thumbnail for "{title}" topic.

Central object or person representing "{title}" keyword.
Dynamic background representing excitement or mystery.
High contrast, cinematic lighting, ultra-realistic 8K detail.
No text included.
16:9 YouTube thumbnail.
"""

# ========================
# MAIN LOGIC
# ========================
if st.button("🚨 Fetch Trending Videos"):
    if not keyword.strip():
        st.warning("Please enter a keyword first!")
    else:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        results = []

        # 1️⃣ Search videos
        st.write(f"🔍 Searching videos for keyword: **{keyword}**")
        search_params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": start_date,
            "maxResults": 20,
            "videoDuration": "medium",
            "key": API_KEY
        }

        search_data = yt_get(SEARCH_URL, search_params)
        videos = search_data.get("items", [])

        if not videos:
            st.warning("No videos found for this keyword!")
        else:
            video_ids = [v["id"]["videoId"] for v in videos]
            channel_ids = list(set(v["snippet"]["channelId"] for v in videos))

            # 2️⃣ Fetch video stats + durations
            video_data = yt_get(VIDEOS_URL, {
                "part": "statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": API_KEY
            })

            video_map = {}
            for vid_item in video_data.get("items", []):
                vid_id = vid_item["id"]
                content = vid_item.get("contentDetails")
                if not content or "duration" not in content:
                    continue
                duration_iso = content["duration"]
                video_map[vid_id] = {
                    "views": int(vid_item.get("statistics", {}).get("viewCount", 0)),
                    "duration": iso_duration_to_seconds(duration_iso)
                }

            # 3️⃣ Fetch channel stats
            channel_data = yt_get(CHANNELS_URL, {
                "part": "statistics",
                "id": ",".join(channel_ids),
                "key": API_KEY
            })
            channel_map = {c["id"]: int(c.get("statistics", {}).get("subscriberCount",0)) for c in channel_data.get("items",[])}

            # 4️⃣ Process each video
            for v in videos:
                vid = v["id"]["videoId"]
                cid = v["snippet"]["channelId"]

                if vid not in video_map or cid not in channel_map:
                    continue

                views = video_map[vid]["views"]
                duration = video_map[vid]["duration"]
                subs = channel_map[cid]

                published = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z","+00:00"))
                age_days = (datetime.now(timezone.utc) - published).days

                # Filters
                if duration < MIN_DURATION_MINUTES * 60 or views < min_views or subs > max_subs:
                    continue

                # Trend detection
                trend = []
                if views >= subs * 5:
                    trend.append("🔥 Views/Subs Explosion")
                if age_days <= 3 and views >= 8000:
                    trend.append("⚡ Fast Growth")
                if views >= 50000:
                    trend.append("🚀 Breakout")

                results.append({
                    "title": v["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "views": views,
                    "subs": subs,
                    "duration": duration//60,
                    "trend": trend
                })

            # Display results
            if results:
                st.success(f"🚨 Found {len(results)} trending videos for '{keyword}'")
                results.sort(key=lambda x: (len(x["trend"]), x["views"]), reverse=True)

                for r in results:
                    st.markdown(
                        f"""
### 📜 {r['title']}
**Trend:** {' | '.join(r['trend']) if r['trend'] else 'Normal'}  
⏱ {r['duration']} min  
👁 {r['views']:,} views  
👥 {r['subs']:,} subs  
🔗 [Watch Video]({r['url']})
"""
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🎬 Generate Script", key=f"s_{r['url']}"):
                            st.text_area(
                                "Script",
                                generate_generic_script(r['title'], keyword),
                                height=250
                            )
                    with col2:
                        if st.button("🖼️ Generate Thumbnail Prompt", key=f"t_{r['url']}"):
                            st.text_area(
                                "Thumbnail Prompt",
                                generate_thumbnail_prompt(r['title']),
                                height=250
                            )

                    st.write("---")
            else:
                st.warning("No videos met the filters (duration/views/subs) for this keyword.")

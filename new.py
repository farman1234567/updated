import streamlit as st
import requests
from datetime import datetime, timedelta

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
    page_title="Echoes of Napoleon – History Content Engine",
    layout="wide"
)

st.title("🏛️ Echoes of Napoleon – Trend Alerts, Scripts & Thumbnails")

days = st.number_input("Search videos from last X days", 1, 30, 7)
min_views = st.number_input("Minimum views", value=8000, step=1000)
max_subs = st.number_input("Maximum channel subscribers", value=3000, step=500)

MIN_DURATION_MINUTES = 5  # Hard filter: NO Shorts

# ========================
# HISTORY KEYWORDS
# ========================
keywords = [
    "Napoleonic Wars documentary",
    "Napoleon Bonaparte history",
    "Peninsular War explained",
    "Battle of Waterloo explained",
    "Why Napoleon failed",
    "French Revolution documentary",
    "Empires that collapsed documentary",
    "Military history explained",
    "Greatest generals in history",
    "Rise and fall of empires"
]

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
# NAPOLEON SCRIPT GENERATOR
# ========================
def generate_napoleon_script(title, keyword):
    return f"""
{title}

Europe was holding its breath.

What began as a calculated decision — made with confidence and ambition —
would soon evolve into one of history’s most instructive moments.

At the center of this story lies {keyword.lower()}.

Power in Europe was not measured only in armies, but in perception.
To appear unstoppable was often enough to bend nations to your will.

And for a time, that illusion held.

But history resists certainty.

Supply lines stretched. Resistance hardened.
What once seemed inevitable slowly became fragile.

Then came the turning point.

Not a single defeat — but a realization.
Victory would no longer come swiftly.

When the dust settled, Europe was changed.

Borders shifted. Legends fractured.
And one truth remained:

Power is never permanent.
Even the greatest empires leave echoes behind.
"""

# ========================
# THUMBNAIL PROMPT GENERATOR
# ========================
def generate_thumbnail_prompt(title):
    return f"""
Ultra-cinematic YouTube thumbnail for a historical documentary.

Napoleon Bonaparte in dramatic three-quarter profile,
intense expression, bicorne hat, dark military coat.

Stormy European battlefield background,
smoke, distant cannons, collapsing flags.

High contrast cinematic lighting,
strong rim light on face,
dark moody shadows.

Ultra-realistic, painterly realism, 8K detail.
Sharp focus on face, blurred background.
No text included.

Emotion: power, downfall, fate.

16:9 YouTube thumbnail.
Inspired by Netflix historical documentaries.

Context title: "{title}"
"""

# ========================
# MAIN LOGIC
# ========================
if st.button("🚨 Scan for History Trend Opportunities"):
    start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
    results = []

    for keyword in keywords:
        st.write(f"🔍 Searching: **{keyword}**")

        # Search for videos
        search_params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": start_date,
            "maxResults": 15,
            "videoDuration": "medium",
            "key": API_KEY
        }

        search_data = yt_get(SEARCH_URL, search_params)
        videos = search_data.get("items", [])

        if not videos:
            continue

        # Collect video & channel IDs
        video_ids = [v["id"]["videoId"] for v in videos]
        channel_ids = list(set(v["snippet"]["channelId"] for v in videos))

        # Fetch video stats & durations
        video_data = yt_get(VIDEOS_URL, {
            "part": "statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": API_KEY
        })

        video_map = {}
        for v in video_data.get("items", []):
            vid = v["id"]
            duration_iso = v["contentDetails"]["duration"]
            video_map[vid] = {
                "views": int(v["statistics"].get("viewCount", 0)),
                "duration": iso_duration_to_seconds(duration_iso)
            }

        # Fetch channel stats
        channel_data = yt_get(CHANNELS_URL, {
            "part": "statistics",
            "id": ",".join(channel_ids),
            "key": API_KEY
        })

        channel_map = {c["id"]: int(c["statistics"].get("subscriberCount",0)) for c in channel_data.get("items",[])}

        # Process results
        for v in videos:
            vid = v["id"]["videoId"]
            cid = v["snippet"]["channelId"]

            if vid not in video_map or cid not in channel_map:
                continue

            views = video_map[vid]["views"]
            duration = video_map[vid]["duration"]
            subs = channel_map[cid]

            published = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z","+00:00"))
            age_days = (datetime.utcnow() - published).days

            # Filters
            if duration < MIN_DURATION_MINUTES * 60:
                continue
            if views < min_views or subs > max_subs:
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
                "keyword": keyword,
                "trend": trend
            })

    # Display results
    if results:
        st.success(f"🚨 {len(results)} History Opportunities Found!")
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
                        "Napoleon-Style Script",
                        generate_napoleon_script(r["title"], r["keyword"]),
                        height=350
                    )

            with col2:
                if st.button("🖼️ Generate Thumbnail Prompt", key=f"t_{r['url']}"):
                    st.text_area(
                        "Thumbnail Prompt",
                        generate_thumbnail_prompt(r["title"]),
                        height=350
                    )

            st.write("---")
    else:
        st.warning("No trend opportunities found.")

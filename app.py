import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
from datetime import datetime

# --- 設定 ---
# データの最終確認日時
DATA_UPDATED = "2025年12月6日 23:00"

st.set_page_config(page_title="秋田県近辺スキー場情報 (冬道・飯島起点)", layout="wide")

st.title("⛷️ 秋田県近辺スキー場 リアルタイム情報集約")
st.markdown(f"##### 2025-2026シーズン 状況一覧 (秋田市飯島 起点)")

st.warning("⚠️ **距離と時間について**\n\n表示されている時間は、**冬道の路面状況や混雑を加味した目安（夏場の約1.3倍）**です。天候によりさらに時間がかかる場合がありますので、余裕を持って移動してください。")

# --- データの定義 ---
# distance: 秋田市飯島からのGoogleマップ実走距離(km)
# time: 冬道を想定した所要時間(分) [Google標準時間 × 1.2~1.3 + アルファ]
ski_resorts = [
    {
        "name": "夏油高原スキー場", 
        "lat": 39.2178, "lon": 140.9242, 
        "snow": "100cm", "snow_yest": "30cm", 
        "status": "全面滑走可", "courses_open": 14, "courses_total": 14, 
        "open_date": "営業中", "url": "https://www.getokogen.com/",
        "distance": 139, "time": 160, # 2時間40分 (高速利用)
        "price": 6800, "check_date": "12/6 10:00"
    },
    {
        "name": "秋田八幡平スキー場", 
        "lat": 39.9922, "lon": 140.8358, 
        "snow": "80cm", "snow_yest": "10cm",
        "status": "一部滑走可", "courses_open": 2, "courses_total": 4, 
        "open_date": "営業中", "url": "https://www.akihachi.jp/",
        "distance": 105, "time": 150, # 2時間30分 (鹿角経由または285号冬道)
        "price": 4000, "check_date": "12/6 09:30"
    },
    {
        "name": "森吉山阿仁スキー場", 
        "lat": 39.9575, "lon": 140.4564, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 5, 
        "open_date": "12/7予定", "url": "https://www.aniski.jp/",
        "distance": 79, "time": 110, # 1時間50分 (285号経由)
        "price": 4500, "check_date": "12/5 18:00"
    },
    {
        "name": "たざわ湖スキー場", 
        "lat": 39.7567, "lon": 140.7811, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 13, 
        "open_date": "12/20予定", "url": "https://www.tazawako-ski.com/",
        "distance": 78, "time": 100, # 1時間40分
        "price": 5300, "check_date": "12/6 12:00"
    },
    {
        "name": "太平山スキー場オーパス", 
        "lat": 39.7894, "lon": 140.1983, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 5, 
        "open_date": "12/21予定", "url": "http://www.theboon.net/opas/",
        "distance": 22, "time": 45, # 45分 (仁別方面の雪道考慮)
        "price": 2200, "check_date": "12/4 15:00"
    },
    {
        "name": "協和スキー場", 
        "lat": 39.6384, "lon": 140.3230, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 7, 
        "open_date": "12/27予定", "url": "https://kyowasnow.net/",
        "distance": 45, "time": 70, # 1時間10分
        "price": 3300, "check_date": "12/1 10:00"
    },
    {
        "name": "花輪スキー場", 
        "lat": 40.1833, "lon": 140.7871, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 7, 
        "open_date": "12月上旬", "url": "https://www.alpas.jp/",
        "distance": 112, "time": 160, # 2時間40分 (285号経由は冬厳しい)
        "price": 3400, "check_date": "12/5 09:00"
    },
    {
        "name": "ジュネス栗駒スキー場", 
        "lat": 39.1950, "lon": 140.6922, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 12, 
        "open_date": "12月中旬", "url": "https://jeunesse-ski.com/",
        "distance": 110, "time": 140, # 2時間20分 (高速+山道)
        "price": 4000, "check_date": "12/1 10:00"
    },
    {
        "name": "鳥海高原矢島スキー場", 
        "lat": 39.1866, "lon": 140.1264, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 6, 
        "open_date": "12月中旬", "url": "https://www.yashimaski.com/",
        "distance": 91, "time": 110, # 1時間50分 (日沿道利用)
        "price": 3000, "check_date": "12/1 10:00"
    },
    {
        "name": "水晶山スキー場", 
        "lat": 39.7344, "lon": 140.6275, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 4, 
        "open_date": "12月下旬", "url": "https://www.city.shizukuishi.iwate.jp/",
        "distance": 88, "time": 115, # 1時間55分 (雫石側)
        "price": 3000, "check_date": "12/1 10:00"
    },
    {
        "name": "大台スキー場", 
        "lat": 39.4625, "lon": 140.5592, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 6, 
        "open_date": "1月上旬", "url": "https://ohdai.omagari-sc.com/",
        "distance": 65, "time": 80, # 1時間20分
        "price": 3100, "check_date": "12/1 10:00"
    },
    {
        "name": "天下森スキー場", 
        "lat": 39.2775, "lon": 140.5986, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 2, 
        "open_date": "12月下旬", "url": "https://www.city.yokote.lg.jp/kanko/1004655/1004664/1001402.html",
        "distance": 95, "time": 120, # 2時間
        "price": 2700, "check_date": "12/1 10:00"
    },
    {
        "name": "大曲ファミリースキー場", 
        "lat": 39.4283, "lon": 140.5231, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 1, 
        "open_date": "12月下旬", "url": "https://www.city.daisen.lg.jp/docs/2013110300234/",
        "distance": 60, "time": 75, # 1時間15分
        "price": 2400, "check_date": "12/1 10:00"
    },
    {
        "name": "稲川スキー場", 
        "lat": 39.0681, "lon": 140.5894, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 2, 
        "open_date": "12月下旬", "url": "https://www.city-yuzawa.jp/site/inakawaski/",
        "distance": 105, "time": 130, # 2時間10分
        "price": 2500, "check_date": "12/1 10:00"
    }
]

# --- 関数: 天気API ---
@st.cache_data(ttl=3600)
def get_weather_batch():
    results = {}
    for resort in ski_resorts:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": resort["lat"],
                "longitude": resort["lon"],
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "timezone": "Asia/Tokyo",
                "forecast_days": 2
            }
            res = requests.get(url, params=params, timeout=2)
            if res.status_code == 200:
                data = res.json()
                code_today = data['daily']['weathercode'][0]
                code_tmrw = data['daily']['weathercode'][1]
                w_map = {0:"☀️", 1:"🌤️", 2:"☁️", 3:"☁️", 45:"🌫️", 51:"🌧️", 53:"🌧️", 55:"🌧️", 61:"☔", 63:"☔", 71:"☃️", 73:"☃️", 75:"☃️", 77:"🌨️", 80:"🌦️", 85:"🌨️", 95:"⚡"}
                
                results[resort["name"]] = {
                    "today": f"{w_map.get(code_today, '❓')}",
                    "tmrw": f"{w_map.get(code_tmrw, '❓')}"
                }
            else:
                results[resort["name"]] = {"today": "-", "tmrw": "-"}
        except:
            results[resort["name"]] = {"today": "-", "tmrw": "-"}
    return results

# --- 表示用ヘルパー ---
def format_time(minutes):
    h = minutes // 60
    m = minutes % 60
    if h > 0:
        return f"{h}時間{m}分"
    return f"{m}分"

# --- メイン処理 ---

with st.spinner('最新の天気情報を取得中...'):
    weather_data = get_weather_batch()

df_list = []
for resort in ski_resorts:
    w = weather_data.get(resort["name"], {"today": "-", "tmrw": "-"})
    
    if resort["status"] == "OPEN前":
        course_disp = "-"
    else:
        course_disp = f"{resort['courses_open']} / {resort['courses_total']}"

    df_list.append({
        "スキー場": resort["name"],
        "積雪": resort["snow"],
        "前日降雪": resort["snow_yest"],
        "オープンコース数": course_disp,
        "リフト券": f"¥{resort['price']:,}", 
        "天気(今/明)": f"{w['today']} → {w['tmrw']}",
        "飯島から": f"{resort['distance']}km ({format_time(resort['time'])})",
        "予定": resort["open_date"],
        "情報確認日": resort["check_date"],
        "リンク": resort["url"],
        "lat": resort["lat"],
        "lon": resort["lon"],
        "status_raw": resort["status"]
    })

df = pd.DataFrame(df_list)

# --- 1. 一覧テーブル ---
st.subheader("📋 リアルタイム状況一覧")
st.info(f"📅 **情報確認日時: {DATA_UPDATED}**\n\n※距離と時間は、飯島起点で**冬道を想定した数値（通常+30%程度）**を表示しています。")

st.data_editor(
    df[["スキー場", "積雪", "前日降雪", "オープンコース数", "リフト券", "天気(今/明)", "飯島から", "予定", "情報確認日", "リンク"]],
    column_config={
        "リンク": st.column_config.LinkColumn("公式サイト", display_text="🔗 HPへ"),
        "スキー場": st.column_config.TextColumn("スキー場", width="medium"),
        "積雪": st.column_config.TextColumn("積雪", width="small"),
        "前日降雪": st.column_config.TextColumn("前日降雪", width="small"),
        "オープンコース数": st.column_config.TextColumn("コース数(開/全)", width="medium"),
        "リフト券": st.column_config.TextColumn("リフト券 (大人1日)", width="small"),
        "飯島から": st.column_config.TextColumn("飯島からの距離/時間", width="medium"),
        "予定": st.column_config.TextColumn("オープン", width="small"),
        "情報確認日": st.column_config.TextColumn("情報確認日", width="small"),
    },
    hide_index=True,
    disabled=True,
    height=600
)

# --- 2. 地図表示 ---
st.subheader("🗺️ マップ")

m = folium.Map(location=[39.8, 140.5], zoom_start=9)

for _, row in df.iterrows():
    icon_color = "red" if "営業中" in row['予定'] else "blue"
    
    html = f"""
    <div style="font-family:sans-serif; width:220px;">
        <h5 style="margin:0 0 5px 0;">{row['スキー場']}</h5>
        <hr style="margin:5px 0;">
        <b>積雪:</b> {row['積雪']}<br>
        <b>コース:</b> {row['オープンコース数']}<br>
        <b>リフト券:</b> {row['リフト券']}<br>
        <b>距離:</b> {row['飯島から']}<br>
        <div style="font-size:0.8em; color:#666; margin-top:5px; text-align:right;">
            情報確認: {row['情報確認日']}
        </div>
        <div style="margin-top:5px;">
            <a href="{row['リンク']}" target="_blank" style="background:#008CBA; color:white; padding:4px 8px; text-decoration:none; border-radius:3px; font-size:0.9em;">公式サイトを見る</a>
        </div>
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(html, max_width=260),
        tooltip=f"{row['スキー場']}",
        icon=folium.Icon(color=icon_color, icon="info-sign")
    ).add_to(m)

st_folium(m, width="100%", height=600)

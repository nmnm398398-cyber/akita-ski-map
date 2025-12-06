import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import datetime
import random # 実運用時は削除し、スクレイピング等のデータに置き換える

# ページ設定
st.set_page_config(page_title="秋田県スキー場マップ", layout="wide")

st.title("⛷️ 秋田県スキー場 リアルタイム情報マップ")
st.markdown("秋田県内の主要スキー場の天気、積雪、コース状況を一覧表示します。")

# --- データ定義 ---
# ここにスキー場のリストを定義します（緯度経度はGoogleマップ等で取得）
ski_resorts = [
    {
        "name": "たざわ湖スキー場",
        "lat": 39.7567,
        "lon": 140.7811,
        "url": "https://www.tazawako-ski.com/",
        "open_date": "2024-12-14",
        "close_date": "2025-04-06"
    },
    {
        "name": "阿仁スキー場",
        "lat": 39.9575,
        "lon": 140.4564,
        "url": "https://www.aniski.jp/",
        "open_date": "2024-12-07",
        "close_date": "2025-03-30"
    },
    {
        "name": "ジュネス栗駒スキー場",
        "lat": 39.1950,
        "lon": 140.6922,
        "url": "https://jeunesse-ski.com/",
        "open_date": "2024-12-21",
        "close_date": "2025-03-23"
    },
    {
        "name": "太平山スキー場オーパス",
        "lat": 39.7686,
        "lon": 140.1789,
        "url": "https://www.theboon.net/opas/",
        "open_date": "2024-12-20",
        "close_date": "2025-03-10"
    },
    {
        "name": "秋田八幡平スキー場",
        "lat": 39.9922,
        "lon": 140.8358,
        "url": "https://www.akihachi.jp/",
        "open_date": "2024-11-20",
        "close_date": "2025-05-06"
    }
]

# --- 関数定義 ---

def get_weather(lat, lon):
    """
    Open-Meteo APIを使用して天気コードを取得する
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode",
            "timezone": "Asia/Tokyo",
            "forecast_days": 2
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        # WMO天気コード変換（簡易版）
        weather_map = {
            0: "☀️ 快晴", 1: "🌤️ 晴れ", 2: "☁️ 一部曇", 3: "☁️ 曇り",
            45: "🌫️ 霧", 48: "🌫️ 霧氷",
            51: "🌧️ 小雨", 53: "🌧️ 雨", 55: "🌧️ 大雨",
            61: "☔ 雨", 63: "☔ 雨", 65: "☔ 大雨",
            71: "☃️ 小雪", 73: "☃️ 雪", 75: "☃️ 大雪",
            77: "🌨️ 霧雪",
            80: "🌦️ にわか雨", 81: "🌦️ にわか雨", 82: "⛈️ 激しい雨",
            85: "🌨️ にわか雪", 86: "🌨️ 激しい雪",
            95: "⚡ 雷雨", 96: "⚡ 雷雨", 99: "⚡ 激しい雷雨"
        }
        
        today_code = data['daily']['weathercode'][0]
        tomorrow_code = data['daily']['weathercode'][1]
        
        return {
            "today": weather_map.get(today_code, "不明"),
            "tomorrow": weather_map.get(tomorrow_code, "不明")
        }
    except Exception as e:
        return {"today": "取得失敗", "tomorrow": "取得失敗"}

def get_ski_status_dummy(resort_name):
    """
    【重要】リアルタイムの積雪・コース情報はAPIがないため、
    ここでは動作確認用のダミーデータを生成しています。
    実運用ではここをWebスクレイピング等の処理に置き換える必要があります。
    """
    # 完全にランダムな数値を返す（デモ用）
    total_courses = random.randint(5, 15)
    open_courses = random.randint(0, total_courses)
    snow_depth = random.randint(0, 250)
    
    return {
        "snow_depth": f"{snow_depth}cm",
        "course_status": f"{open_courses}/{total_courses}",
        "status_percent": open_courses / total_courses
    }

# --- メイン処理 ---

# 地図の初期化（秋田県の中央付近）
m = folium.Map(location=[39.7, 140.4], zoom_start=9)

st.sidebar.header("🔍 スキー場リスト")

for resort in ski_resorts:
    # データの取得
    weather = get_weather(resort["lat"], resort["lon"])
    status = get_ski_status_dummy(resort["name"]) # ※ここはダミーデータです
    
    # ポップアップに表示するHTMLを作成
    # リンクは target='_blank' で新しいタブで開くように設定
    html = f"""
    <div style="font-family: sans-serif; width: 250px;">
        <h4 style="margin-bottom:5px;">{resort['name']}</h4>
        <hr style="margin:5px 0;">
        <b>📅 営業期間:</b><br>
        {resort['open_date']} ～ {resort['close_date']}<br><br>
        <b>❄️ 積雪:</b> {status['snow_depth']}<br>
        <b>🎿 コース:</b> {status['course_status']} オープン<br><br>
        <b>🌤️ 天気:</b><br>
        今日: {weather['today']}<br>
        明日: {weather['tomorrow']}<br><br>
        <a href="{resort['url']}" target="_blank" style="
            background-color: #008CBA;
            color: white;
            padding: 8px 12px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            border-radius: 4px;
            width: 100%;
            box-sizing: border-box;">
            公式サイトを見る 🔗
        </a>
    </div>
    """
    
    # iframe内にHTMLを表示するためのFolium設定
    popup = folium.Popup(html, max_width=300)
    
    # マーカーを追加
    folium.Marker(
        location=[resort["lat"], resort["lon"]],
        popup=popup,
        tooltip=resort["name"],
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

    # サイドバーにも情報を表示
    with st.sidebar.expander(resort["name"]):
        st.write(f"今日: {weather['today']}")
        st.write(f"積雪: {status['snow_depth']}")
        st.write(f"[公式サイト]({resort['url']})")

# Streamlitで地図を表示
st_data = st_folium(m, width=800, height=600)

st.info("※積雪・コース数はデモ用のダミーデータです。天気予報はAPIからリアルタイムで取得しています。")
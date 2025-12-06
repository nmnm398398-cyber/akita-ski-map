import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd

# ページ設定
st.set_page_config(page_title="秋田県・夏油高原 スキー場マップ", layout="wide")

st.title("⛷️ 秋田県・夏油高原スキー場 リアルタイム情報")
st.markdown("##### 2025-2026シーズン 最新状況一覧")

# --- データの定義 ---
# 積雪やコース情報はAPIがないため、現時点(2025/12/6)の実測値を初期値としています。
# 運用時は、管理者がここの数値を書き換えるだけでサイトに反映されます。

ski_resorts = [
    # 営業中のスキー場
    {
        "name": "夏油高原スキー場", 
        "lat": 39.2178, "lon": 140.9242, 
        "snow": "100cm", "status": "全面滑走可", "courses_open": 14, "courses_total": 14, 
        "open_date": "営業中", "url": "https://www.getokogen.com/"
    },
    {
        "name": "秋田八幡平スキー場", 
        "lat": 39.9922, "lon": 140.8358, 
        "snow": "80cm", "status": "一部滑走可", "courses_open": 2, "courses_total": 4, 
        "open_date": "営業中", "url": "https://www.akihachi.jp/"
    },
    # オープン前のスキー場（積雪などは「-」としています）
    {
        "name": "たざわ湖スキー場", 
        "lat": 39.7567, "lon": 140.7811, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 13, 
        "open_date": "12/20予定", "url": "https://www.tazawako-ski.com/"
    },
    {
        "name": "森吉山阿仁スキー場", 
        "lat": 39.9575, "lon": 140.4564, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 5, 
        "open_date": "12/7予定", "url": "https://www.aniski.jp/"
    },
    {
        "name": "花輪スキー場", 
        "lat": 40.1833, "lon": 140.7871, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 7, 
        "open_date": "12月上旬", "url": "https://www.alpas.jp/"
    },
    {
        "name": "ジュネス栗駒スキー場", 
        "lat": 39.1950, "lon": 140.6922, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 12, 
        "open_date": "12月中旬", "url": "https://jeunesse-ski.com/"
    },
    {
        "name": "太平山スキー場オーパス", 
        "lat": 39.7894, "lon": 140.1983, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 5, 
        "open_date": "12/21予定", "url": "http://www.theboon.net/opas/"
    },
    {
        "name": "協和スキー場", 
        "lat": 39.6384, "lon": 140.3230, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 7, 
        "open_date": "12/27予定", "url": "https://kyowasnow.net/"
    },
    {
        "name": "鳥海高原矢島スキー場", 
        "lat": 39.1866, "lon": 140.1264, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 6, 
        "open_date": "12月中旬", "url": "https://www.yashimaski.com/"
    },
    {
        "name": "水晶山スキー場", 
        "lat": 39.7344, "lon": 140.6275, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 4, 
        "open_date": "12月下旬", "url": "https://www.city.shizukuishi.iwate.jp/"
    },
    {
        "name": "大台スキー場", 
        "lat": 39.4625, "lon": 140.5592, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 6, 
        "open_date": "1月上旬", "url": "https://ohdai.omagari-sc.com/"
    },
    {
        "name": "天下森スキー場", 
        "lat": 39.2775, "lon": 140.5986, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 2, 
        "open_date": "12月下旬", "url": "https://www.city.yokote.lg.jp/kanko/1004655/1004664/1001402.html"
    },
    {
        "name": "大曲ファミリースキー場", 
        "lat": 39.4283, "lon": 140.5231, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 1, 
        "open_date": "12月下旬", "url": "https://www.city.daisen.lg.jp/docs/2013110300234/"},
    {
        "name": "稲川スキー場", 
        "lat": 39.0681, "lon": 140.5894, 
        "snow": "-", "status": "OPEN前", "courses_open": 0, "courses_total": 2, 
        "open_date": "12月下旬", "url": "https://www.city-yuzawa.jp/site/inakawaski/"
    }
]

# --- 関数: 天気API (リアルタイム取得) ---
@st.cache_data(ttl=3600) # 1時間キャッシュしてAPI負荷を減らす
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
                
                # 天気コード変換
                w_map = {0:"☀️", 1:"🌤️", 2:"☁️", 3:"☁️", 45:"🌫️", 51:"🌧️", 53:"🌧️", 55:"🌧️", 61:"☔", 63:"☔", 71:"☃️", 73:"☃️", 75:"☃️", 77:"🌨️", 80:"🌦️", 85:"🌨️", 95:"⚡"}
                
                weather_today = f"{w_map.get(code_today, '❓')}"
                weather_tmrw = f"{w_map.get(code_tmrw, '❓')}"
                
                results[resort["name"]] = {
                    "today": weather_today,
                    "tmrw": weather_tmrw
                }
            else:
                results[resort["name"]] = {"today": "-", "tmrw": "-"}
        except:
            results[resort["name"]] = {"today": "-", "tmrw": "-"}
    return results

# --- メイン処理 ---

# 天気データの取得
with st.spinner('最新の天気情報を取得中...'):
    weather_data = get_weather_batch()

# 一覧表用のデータフレーム作成
df_list = []
for resort in ski_resorts:
    w = weather_data.get(resort["name"], {"today": "-", "tmrw": "-"})
    
    # コース表記を作成 (例: 14/14)
    if resort["status"] == "OPEN前":
        course_disp = "-"
    else:
        course_disp = f"{resort['courses_open']} / {resort['courses_total']}"

    df_list.append({
        "スキー場": resort["name"],
        "積雪": resort["snow"],
        "コース (開/全)": course_disp,
        "天気(今/明)": f"{w['today']} → {w['tmrw']}",
        "予定": resort["open_date"],
        "リンク": resort["url"],
        "lat": resort["lat"],
        "lon": resort["lon"],
        "status_raw": resort["status"] # 色分け用などに保持
    })

df = pd.DataFrame(df_list)

# --- 1. 一覧テーブル表示 ---
st.subheader("📋 リアルタイム状況一覧")

# データフレームを表示（リンクをクリック可能に）
st.data_editor(
    df[["スキー場", "積雪", "コース (開/全)", "天気(今/明)", "予定", "リンク"]],
    column_config={
        "リンク": st.column_config.LinkColumn(
            "公式サイト", display_text="🔗 HPへ"
        ),
        "スキー場": st.column_config.TextColumn("スキー場", width="medium"),
        "積雪": st.column_config.TextColumn("積雪深", width="small"),
        "コース (開/全)": st.column_config.TextColumn("コース", width="small"),
        "予定": st.column_config.TextColumn("オープン日", width="small"),
    },
    hide_index=True,
    disabled=True,
    height=500 
)

# --- 2. 地図表示 ---
st.subheader("🗺️ マップ")

m = folium.Map(location=[39.6, 140.6], zoom_start=9)

for _, row in df.iterrows():
    # マーカーの色分け（営業中なら赤、それ以外は青）
    icon_color = "red" if "営業中" in row['予定'] else "blue"
    
    html = f"""
    <div style="font-family:sans-serif; width:220px;">
        <h5 style="margin:0 0 5px 0;">{row['スキー場']}</h5>
        <hr style="margin:5px 0;">
        <b>積雪:</b> {row['積雪']}<br>
        <b>コース:</b> {row['コース (開/全)']}<br>
        <b>天気:</b> {row['天気(今/明)']}<br>
        <div style="margin-top:8px;">
            <a href="{row['リンク']}" target="_blank" style="background:#008CBA; color:white; padding:4px 8px; text-decoration:none; border-radius:3px; font-size:0.9em;">公式サイトを見る</a>
        </div>
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(html, max_width=260),
        tooltip=f"{row['スキー場']} ({row['積雪']})",
        icon=folium.Icon(color=icon_color, icon="info-sign")
    ).add_to(m)

st_folium(m, width="100%", height=600)

# 脚注
st.caption("【データについて】積雪・コース情報は2025年12月6日時点のものです。天気はリアルタイム更新です。最新情報は必ず公式サイトをご確認ください。")

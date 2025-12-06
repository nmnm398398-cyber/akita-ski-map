import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
from datetime import datetime

# ページ設定
st.set_page_config(page_title="秋田県＋夏油高原 スキー場マップ", layout="wide")

st.title("⛷️ 秋田県・夏油高原スキー場 リアルタイム情報")
st.markdown("指定された14スキー場の天気とオープン状況を表示します。積雪・コース情報の詳細は各公式サイトをご確認ください。")

# --- データ定義 (2025-2026シーズン想定) ---
# ※「水氷山」は「水晶山スキー場」として扱っています
ski_resorts = [
    {"name": "花輪スキー場", "lat": 40.1833, "lon": 140.7871, "open_date": "12月上旬", "url": "https://www.alpas.jp/"},
    {"name": "協和スキー場", "lat": 39.6384, "lon": 140.3230, "open_date": "12/27予定", "url": "https://kyowasnow.net/"},
    {"name": "大曲ファミリースキー場", "lat": 39.4283, "lon": 140.5231, "open_date": "12月下旬", "url": "https://www.city.daisen.lg.jp/docs/2013110300234/"},
    {"name": "大台スキー場", "lat": 39.4625, "lon": 140.5592, "open_date": "1月上旬", "url": "https://ohdai.omagari-sc.com/"},
    {"name": "鳥海高原矢島スキー場", "lat": 39.1866, "lon": 140.1264, "open_date": "12月中旬", "url": "https://www.yashimaski.com/"},
    {"name": "太平山スキー場オーパス", "lat": 39.7894, "lon": 140.1983, "open_date": "12/21予定", "url": "http://www.theboon.net/opas/"},
    {"name": "稲川スキー場", "lat": 39.0681, "lon": 140.5894, "open_date": "12月下旬", "url": "https://www.city-yuzawa.jp/site/inakawaski/"},
    {"name": "秋田八幡平スキー場", "lat": 39.9922, "lon": 140.8358, "open_date": "11月中旬", "url": "https://www.akihachi.jp/"},
    {"name": "ジュネス栗駒スキー場", "lat": 39.1950, "lon": 140.6922, "open_date": "12月中旬", "url": "https://jeunesse-ski.com/"},
    {"name": "水晶山スキー場", "lat": 39.7344, "lon": 140.6275, "open_date": "12月下旬", "url": "https://www.city.shizukuishi.iwate.jp/ (要確認)"}, # 鹿角市だが公式サイト分散のため
    {"name": "森吉山阿仁スキー場", "lat": 39.9575, "lon": 140.4564, "open_date": "12月上旬", "url": "https://www.aniski.jp/"},
    {"name": "たざわ湖スキー場", "lat": 39.7567, "lon": 140.7811, "open_date": "12/20予定", "url": "https://www.tazawako-ski.com/"},
    {"name": "天下森スキー場", "lat": 39.2775, "lon": 140.5986, "open_date": "12月下旬", "url": "https://www.city.yokote.lg.jp/kanko/1004655/1004664/1001402.html"},
    {"name": "夏油高原スキー場", "lat": 39.2178, "lon": 140.9242, "open_date": "12/5(営業中)", "url": "https://www.getokogen.com/"}
]

# --- 天気取得関数 (リアルタイム) ---
def get_weather_batch():
    """
    Open-Meteo APIから天気情報を取得
    """
    results = {}
    for resort in ski_resorts:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": resort["lat"],
                "longitude": resort["lon"],
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "timezone": "Asia/Tokyo",
                "forecast_days": 1
            }
            res = requests.get(url, params=params, timeout=2)
            if res.status_code == 200:
                data = res.json()
                code = data['daily']['weathercode'][0]
                t_max = data['daily']['temperature_2m_max'][0]
                t_min = data['daily']['temperature_2m_min'][0]
                
                # WMOコード変換
                w_map = {0:"☀️", 1:"🌤️", 2:"☁️", 3:"☁️", 45:"🌫️", 51:"🌧️", 53:"🌧️", 55:"🌧️", 61:"☔", 63:"☔", 71:"☃️", 73:"☃️", 75:"☃️", 77:"🌨️", 80:"🌦️", 85:"🌨️", 95:"⚡"}
                icon = w_map.get(code, "❓")
                results[resort["name"]] = f"{icon} {t_max}℃ / {t_min}℃"
            else:
                results[resort["name"]] = "取得不可"
        except:
            results[resort["name"]] = "エラー"
    return results

# --- メイン処理 ---

# 天気データのロード
with st.spinner('各スキー場の最新天気を取得中...'):
    weather_data = get_weather_batch()

# データフレームの作成（一覧表示用）
df_list = []
for resort in ski_resorts:
    df_list.append({
        "スキー場名": resort["name"],
        "オープン予定": resort["open_date"],
        "今日の天気 (最高/最低)": weather_data.get(resort["name"], "-"),
        "公式サイト": resort["url"], # リンク用URL
        "lat": resort["lat"],
        "lon": resort["lon"]
    })

df = pd.DataFrame(df_list)

# --- 1. 一覧表示 (Dataframe) ---
st.subheader("📋 スキー場一覧 & リンク")
st.markdown("クリックして公式サイトへアクセスできます。")

# LinkColumnを使ってURLをクリック可能にする
st.data_editor(
    df[["スキー場名", "オープン予定", "今日の天気 (最高/最低)", "公式サイト"]],
    column_config={
        "公式サイト": st.column_config.LinkColumn(
            "公式サイト",
            help="クリックして公式サイトを開く",
            validate="^https://.*",
            display_text="🔗 詳細を見る"
        ),
        "スキー場名": st.column_config.TextColumn("スキー場名", width="medium"),
    },
    hide_index=True,
    disabled=True, # 編集不可にする
)

# --- 2. 地図表示 ---
st.subheader("🗺️ マップ表示")

# マップ初期位置（秋田県中央）
m = folium.Map(location=[39.7, 140.6], zoom_start=9)

for _, row in df.iterrows():
    # ポップアップ情報の構築
    html = f"""
    <div style="font-family:sans-serif; width:200px;">
        <b>{row['スキー場名']}</b><br>
        <span style="font-size:0.9em; color:#555;">オープン: {row['オープン予定']}</span><br>
        <div style="margin-top:5px; padding:5px; background:#f0f2f6; border-radius:5px;">
            天気: {row['今日の天気 (最高/最低)']}
        </div>
        <a href="{row['公式サイト']}" target="_blank" style="display:block; margin-top:8px; text-align:center; background:#008CBA; color:white; padding:5px; text-decoration:none; border-radius:3px;">公式サイトへ</a>
    </div>
    """
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(html, max_width=250),
        tooltip=row['スキー場名'],
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

st_folium(m, width="100%", height=600)

st.caption("※オープン予定日は2025-2026シーズンの情報を元にしていますが、積雪状況により変動します。必ず公式サイトで最新情報をご確認ください。")

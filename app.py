import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 設定 ---
DATA_UPDATED = "2025年12月6日 23:30"

st.set_page_config(page_title="秋田県近辺スキー場情報 (飯島起点)", layout="wide")

# --- 日付の計算 ---
today = datetime.now()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)

str_today = today.strftime("%m/%d")
str_tmrw = tomorrow.strftime("%m/%d")
str_yest = yesterday.strftime("%m/%d")

# --- CSSスタイル（固定ヘッダー・列・縞模様） ---
st.markdown("""
<style>
    /* テーブル全体のコンテナ */
    .table-container {
        max-height: 600px;
        overflow: auto;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-family: sans-serif;
        font-size: 14px;
        white-space: nowrap; /* 改行を防ぐ */
    }
    th, td {
        padding: 12px 15px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    
    /* ヘッダーの固定 (Sticky Header) */
    thead th {
        position: sticky;
        top: 0;
        background-color: #008CBA; /* ヘッダー背景色 */
        color: white;
        z-index: 2; /* 最前面 */
        box-shadow: 0 2px 2px rgba(0,0,0,0.1);
    }

    /* 1列目（スキー場名）の固定 (Sticky Column) */
    th:first-child, td:first-child {
        position: sticky;
        left: 0;
        background-color: #008CBA; /* ヘッダーの1列目 */
        z-index: 3; /* ヘッダー×固定列の交差点は一番上 */
    }
    tbody td:first-child {
        background-color: #fff; /* 通常行の1列目 */
        z-index: 1;
        font-weight: bold;
        border-right: 2px solid #ddd; /* 固定列の境界線 */
    }
    
    /* 縞模様 (Zebra Striping) */
    tbody tr:nth-child(even) {
        background-color: #f8f9fa; /* 薄いグレー */
    }
    tbody tr:nth-child(even) td:first-child {
        background-color: #f8f9fa; /* 固定列も縞模様に合わせる */
    }

    /* リンクボタンのスタイル */
    .link-btn {
        background-color: #008CBA;
        color: white;
        padding: 6px 10px;
        text-decoration: none;
        border-radius: 4px;
        font-size: 12px;
        display: inline-block;
    }
    .link-btn:hover {
        background-color: #00779e;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("⛷️ 秋田県近辺スキー場 リアルタイム情報集約")
st.markdown(f"##### 2025-2026シーズン 状況一覧 (秋田市飯島 起点)")

# お知らせ
st.warning("""
**「リアルタイム渋滞情報は反映していません。」**
\n※表示時間はGoogleマップ標準時間＋35%（冬道想定）で算出しています。
""")

# --- データ定義 ---
ski_resorts = [
    {
        "name": "夏油高原スキー場", 
        "lat": 39.2178, "lon": 140.9242, 
        "snow": "100cm", "snow_yest": "30cm", 
        "status": "全面滑走可", "courses_open": 14, "courses_total": 14, 
        "open_date": "営業中", "url": "https://www.getokogen.com/",
        "distance": 139, "time": 115, 
        "price": 6800, "check_date": "12/6 10:00"
    },
    {
        "name": "秋田八幡平スキー場", 
        "lat": 39.9922, "lon": 140.8358, 
        "snow": "80cm", "snow_yest": "10cm",
        "status": "一部滑走可", "courses_open": 2, "courses_total": 4, 
        "open_date": "営業中", "url": "https://www.akihachi.jp/",
        "distance": 105, "time": 115, 
        "price": 4000, "check_date": "12/6 09:30"
    },
    {
        "name": "森吉山阿仁スキー場", 
        "lat": 39.9575, "lon": 140.4564, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 5, 
        "open_date": "12/7予定", "url": "https://www.aniski.jp/",
        "distance": 79, "time": 85, 
        "price": 4500, "check_date": "12/5 18:00"
    },
    {
        "name": "たざわ湖スキー場", 
        "lat": 39.7567, "lon": 140.7811, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 13, 
        "open_date": "12/20予定", "url": "https://www.tazawako-ski.com/",
        "distance": 78, "time": 90, 
        "price": 5300, "check_date": "12/6 12:00"
    },
    {
        "name": "太平山スキー場オーパス", 
        "lat": 39.7894, "lon": 140.1983, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 5, 
        "open_date": "12/21予定", "url": "http://www.theboon.net/opas/",
        "distance": 22, "time": 30, 
        "price": 2200, "check_date": "12/4 15:00"
    },
    {
        "name": "協和スキー場", 
        "lat": 39.6384, "lon": 140.3230, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 7, 
        "open_date": "12/27予定", "url": "https://kyowasnow.net/",
        "distance": 45, "time": 50, 
        "price": 3300, "check_date": "12/1 10:00"
    },
    {
        "name": "花輪スキー場", 
        "lat": 40.1833, "lon": 140.7871, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 7, 
        "open_date": "12月上旬", "url": "https://www.alpas.jp/",
        "distance": 112, "time": 115, 
        "price": 3400, "check_date": "12/5 09:00"
    },
    {
        "name": "ジュネス栗駒スキー場", 
        "lat": 39.1950, "lon": 140.6922, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 12, 
        "open_date": "12月中旬", "url": "https://jeunesse-ski.com/",
        "distance": 110, "time": 95, 
        "price": 4000, "check_date": "12/1 10:00"
    },
    {
        "name": "鳥海高原矢島スキー場", 
        "lat": 39.1866, "lon": 140.1264, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 6, 
        "open_date": "12月中旬", "url": "https://www.yashimaski.com/",
        "distance": 91, "time": 85, 
        "price": 3000, "check_date": "12/1 10:00"
    },
    {
        "name": "水晶山スキー場", 
        "lat": 39.7344, "lon": 140.6275, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 4, 
        "open_date": "12月下旬", "url": "https://www.city.shizukuishi.iwate.jp/",
        "distance": 88, "time": 90, 
        "price": 3000, "check_date": "12/1 10:00"
    },
    {
        "name": "大台スキー場", 
        "lat": 39.4625, "lon": 140.5592, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 6, 
        "open_date": "1月上旬", "url": "https://ohdai.omagari-sc.com/",
        "distance": 65, "time": 60, 
        "price": 3100, "check_date": "12/1 10:00"
    },
    {
        "name": "天下森スキー場", 
        "lat": 39.2775, "lon": 140.5986, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 2, 
        "open_date": "12月下旬", "url": "https://www.city.yokote.lg.jp/kanko/1004655/1004664/1001402.html",
        "distance": 95, "time": 85, 
        "price": 2700, "check_date": "12/1 10:00"
    },
    {
        "name": "大曲ファミリースキー場", 
        "lat": 39.4283, "lon": 140.5231, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 1, 
        "open_date": "12月下旬", "url": "https://www.city.daisen.lg.jp/docs/2013110300234/",
        "distance": 60, "time": 55, 
        "price": 2400, "check_date": "12/1 10:00"
    },
    {
        "name": "稲川スキー場", 
        "lat": 39.0681, "lon": 140.5894, 
        "snow": "-", "snow_yest": "-",
        "status": "OPEN前", "courses_open": 0, "courses_total": 2, 
        "open_date": "12月下旬", "url": "https://www.city-yuzawa.jp/site/inakawaski/",
        "distance": 105, "time": 95, 
        "price": 2500, "check_date": "12/1 10:00"
    }
]

# --- API処理 ---
@st.cache_data(ttl=3600)
def get_weather_batch():
    results = {}
    for resort in ski_resorts:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": resort["lat"],
                "longitude": resort["lon"],
                "daily": "weathercode",
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

def format_time(minutes):
    h = minutes // 60
    m = minutes % 60
    if h > 0: return f"{h}時間{m}分"
    return f"{m}分"

# --- データ生成 ---
with st.spinner('最新データを取得・整形中...'):
    weather_data = get_weather_batch()

df_list = []
for resort in ski_resorts:
    w = weather_data.get(resort["name"], {"today": "-", "tmrw": "-"})
    time_winter = int(resort["time"] * 1.35)
    
    if resort["status"] == "OPEN前":
        course_disp = "-"
    else:
        course_disp = f"{resort['courses_open']} / {resort['courses_total']}"
    
    # HTMLリンクボタンを作成
    link_html = f'<a href="{resort["url"]}" target="_blank" class="link-btn">公式サイト</a>'

    df_list.append({
        "スキー場名": resort["name"],
        "積雪": resort["snow"],
        f"前日降雪<br><span style='font-size:0.8em'>({str_yest})</span>": resort["snow_yest"],
        "コース数<br><span style='font-size:0.8em'>(開/全)</span>": course_disp,
        "リフト券<br><span style='font-size:0.8em'>(大人1日)</span>": f"¥{resort['price']:,}",
        f"天気<br><span style='font-size:0.8em'>({str_today}→{str_tmrw})</span>": f"{w['today']} → {w['tmrw']}",
        "飯島から<br><span style='font-size:0.8em'>(距離/時間)</span>": f"{resort['distance']}km<br>{format_time(time_winter)}",
        "オープン予定": resort["open_date"],
        "情報確認": resort["check_date"],
        "リンク": link_html,
        # 地図用データ
        "lat": resort["lat"],
        "lon": resort["lon"],
        "status_raw": resort["status"]
    })

df = pd.DataFrame(df_list)

# --- 1. 一覧テーブル (HTML描画) ---
st.subheader("📋 リアルタイム状況一覧")
st.info(f"📅 **情報確認日時: {DATA_UPDATED}**")

# HTMLへ変換（エスケープしないことでタグを有効化）
table_html = df.drop(columns=["lat", "lon", "status_raw"]).to_html(classes="table", escape=False, index=False)

# CSS適用済みコンテナ内に表示
st.markdown(f'<div class="table-container">{table_html}</div>', unsafe_allow_html=True)

# --- 2. 地図表示 ---
st.subheader("🗺️ マップ")

m = folium.Map(location=[39.8, 140.5], zoom_start=9)

for _, row in df.iterrows():
    icon_color = "red" if "営業中" in row['オープン予定'] else "blue"
    
    html = f"""
    <div style="font-family:sans-serif; width:220px;">
        <h5 style="margin:0 0 5px 0;">{row['スキー場名']}</h5>
        <hr style="margin:5px 0;">
        <b>積雪:</b> {row['積雪']}<br>
        <b>距離:</b> {row[f"飯島から<br><span style='font-size:0.8em'>(距離/時間)</span>"].replace('<br>', ' ')}<br>
        <div style="font-size:0.8em; color:#666; margin-top:5px; text-align:right;">
            情報確認: {row['情報確認']}
        </div>
        <div style="margin-top:5px;">
            {row['リンク']}
        </div>
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(html, max_width=260),
        tooltip=f"{row['スキー場名']}",
        icon=folium.Icon(color=icon_color, icon="info-sign")
    ).add_to(m)

st_folium(m, width="100%", height=600)

import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta, timezone
import re

# --- 設定 ---
CACHE_TTL = 3600 # 1時間キャッシュ

st.set_page_config(page_title="秋田県近辺スキー場情報", layout="wide")

# --- 時間設定 (JST) ---
JST = timezone(timedelta(hours=9), 'JST')
now_jst = datetime.now(timezone.utc).astimezone(JST)
ACCESS_TIME = now_jst.strftime("%Y年%m月%d日 %H:%M")
today_str = now_jst.strftime("%m/%d")
tmrw_str = (now_jst + timedelta(days=1)).strftime("%m/%d")

# --- CSS ---
st.markdown("""
<style>
    .table-container { max-height: 600px; overflow: auto; border: 1px solid #ddd; margin-bottom: 30px; }
    table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; white-space: nowrap; }
    th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #ddd; }
    thead th { position: sticky; top: 0; background-color: #008CBA; color: white; z-index: 2; }
    th:first-child, td:first-child { position: sticky; left: 0; background-color: #008CBA; z-index: 3; }
    tbody td:first-child { background-color: #fff; z-index: 1; font-weight: bold; border-right: 2px solid #ddd; }
    tbody tr:nth-child(even) { background-color: #f8f9fa; }
    tbody tr:nth-child(even) td:first-child { background-color: #f8f9fa; }
    
    .status-ok { color: green; font-weight: bold; background:#e6fffa; padding:2px 5px; border-radius:4px; }
    .status-ng { color: #d9534f; font-weight: bold; background:#fff5f5; padding:2px 5px; border-radius:4px; }
    .no-data { color: #999; font-size: 0.9em; }
    .link-btn { background: #fff; border: 1px solid #008CBA; color: #008CBA; padding: 2px 8px; border-radius: 4px; text-decoration: none; font-size: 0.8em;}
    .update-info { background:#fff3cd; padding:10px; border-radius:5px; margin-bottom:15px; font-size:0.9em; }
</style>
""", unsafe_allow_html=True)

st.title("⛷️ 秋田県近辺スキー場 リアルタイム情報集約")
st.markdown(f"##### 自動スクレイピング強化版")

# --- サイドバー ---
filter_open_only = st.sidebar.checkbox("営業中のみ表示", value=False)

# --- スクレイピング関数 ---
@st.cache_data(ttl=CACHE_TTL)
def scrape_resort(url, total_courses):
    """
    サイトから積雪、状況、そして「オープンしているコース数」を抽出する
    """
    data = {
        "snow": "未取得", 
        "status": "確認中", 
        "open_count": "?" # オープンコース数
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = res.apparent_encoding
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text().replace('\n', '').replace(' ', '')
            
            # 1. 積雪
            match = re.search(r'(積雪|山頂)[:：]*([0-9]{1,3})cm', text)
            if match: data["snow"] = f"{match.group(2)}cm"
            
            # 2. 状況判定
            if "全面滑走可" in text: 
                data["status"] = "✅ 全面可"
                data["open_count"] = total_courses # 全面可なら全コースオープン
            elif "一部滑走" in text: 
                data["status"] = "⚠️ 一部可"
                # 「Xコース滑走可」のような記述を探す
                match_c = re.search(r'([0-9]{1,2})([本|コース])(滑走|オープン|可)', text)
                if match_c:
                    data["open_count"] = int(match_c.group(1))
            elif "営業中" in text: 
                data["status"] = "✅ 営業中"
                # 明記がない場合は不明だが、営業中なら仮に「?」か、一部記述を探す
                match_c = re.search(r'([0-9]{1,2})([本|コース])(滑走|オープン|可)', text)
                if match_c:
                    data["open_count"] = int(match_c.group(1))
            elif "準備中" in text: 
                data["status"] = "⛔ 準備中"
                data["open_count"] = 0
            elif "クローズ" in text or "終了" in text: 
                data["status"] = "⛔ クローズ"
                data["open_count"] = 0
            
    except:
        pass
    return data

# --- データ定義 (スペック固定データ) ---
# ※「圧雪/非圧雪」の内訳や「全コース数」は物理的な施設情報のため固定値として持ちます
base_resorts = [
    {
        "name": "夏油高原", "full_name": "夏油高原スキー場", "url": "https://www.getokogen.com/", 
        "lat": 39.2178, "lon": 140.9242, "time": 115, "dist": 139, "price": 6800,
        "total": 14, "groom": 10, "ungroom": 4, 
        "yt_id": "Vo9xtIyktUY", "live": "https://www.youtube.com/@getokogen/live"
    },
    {
        "name": "秋田八幡平", "full_name": "秋田八幡平スキー場", "url": "https://www.akihachi.jp/", 
        "lat": 39.9922, "lon": 140.8358, "time": 115, "dist": 105, "price": 4000,
        "total": 4, "groom": 2, "ungroom": 2, 
        "live": "https://www.akihachi.jp/"
    },
    {
        "name": "阿仁", "full_name": "森吉山阿仁スキー場", "url": "https://www.aniski.jp/", 
        "lat": 39.9575, "lon": 140.4564, "time": 85, "dist": 79, "price": 4500,
        "total": 5, "groom": 3, "ungroom": 2, 
        "live": "https://www.aniski.jp/livecam/"
    },
    {
        "name": "たざわ湖", "full_name": "たざわ湖スキー場", "url": "https://www.tazawako-ski.com/", 
        "lat": 39.7567, "lon": 140.7811, "time": 90, "dist": 78, "price": 5300,
        "total": 13, "groom": 9, "ungroom": 4, 
        "live": "http://www.tazawako-ski.com/gelande/"
    },
    {
        "name": "オーパス", "full_name": "太平山スキー場オーパス", "url": "http://www.theboon.net/opas/", 
        "lat": 39.7894, "lon": 140.1983, "time": 30, "dist": 22, "price": 2200,
        "total": 5, "groom": 5, "ungroom": 0, 
        "live": "http://www.theboon.net/opas/livecam.html"
    },
    {
        "name": "ジュネス栗駒", "full_name": "ジュネス栗駒スキー場", "url": "https://jeunesse-ski.com/", 
        "lat": 39.1950, "lon": 140.6922, "time": 95, "dist": 110, "price": 4000,
        "total": 12, "groom": 10, "ungroom": 2, 
        "live": "https://jeunesse-ski.com/live-camera/"
    },
    {
        "name": "矢島", "full_name": "鳥海高原矢島スキー場", "url": "https://www.yashimaski.com/", 
        "lat": 39.1866, "lon": 140.1264, "time": 85, "dist": 91, "price": 3000,
        "total": 6, "groom": 5, "ungroom": 1, 
        "live": "https://ski.city.yurihonjo.lg.jp/live-camera/"
    },
    {
        "name": "協和", "full_name": "協和スキー場", "url": "https://kyowasnow.net/", 
        "lat": 39.6384, "lon": 140.3230, "time": 50, "dist": 45, "price": 3300,
        "total": 7, "groom": 7, "ungroom": 0, 
        "live": "https://kyowasnow.net/"
    },
    {
        "name": "花輪", "full_name": "花輪スキー場", "url": "https://www.alpas.jp/", 
        "lat": 40.1833, "lon": 140.7871, "time": 115, "dist": 112, "price": 3400,
        "total": 7, "groom": 7, "ungroom": 0, 
    },
    {
        "name": "水晶山", "full_name": "水晶山スキー場", "url": "https://www.city.shizukuishi.iwate.jp/", 
        "lat": 39.7344, "lon": 140.6275, "time": 90, "dist": 88, "price": 3000,
        "total": 4, "groom": 4, "ungroom": 0, 
    },
    {
        "name": "大台", "full_name": "大台スキー場", "url": "https://ohdai.omagari-sc.com/", 
        "lat": 39.4625, "lon": 140.5592, "time": 60, "dist": 65, "price": 3100,
        "total": 6, "groom": 6, "ungroom": 0, 
    },
    {
        "name": "天下森", "full_name": "天下森スキー場", "url": "https://www.city.yokote.lg.jp/kanko/1004655/1004664/1001402.html", 
        "lat": 39.2775, "lon": 140.5986, "time": 85, "dist": 95, "price": 2700,
        "total": 2, "groom": 2, "ungroom": 0, 
    },
    {
        "name": "大曲ファミリー", "full_name": "大曲ファミリースキー場", "url": "https://www.city.daisen.lg.jp/docs/2013110300234/", 
        "lat": 39.4283, "lon": 140.5231, "time": 55, "dist": 60, "price": 2400,
        "total": 1, "groom": 1, "ungroom": 0, 
    },
    {
        "name": "稲川", "full_name": "稲川スキー場", "url": "https://www.city-yuzawa.jp/site/inakawaski/", 
        "lat": 39.0681, "lon": 140.5894, "time": 95, "dist": 105, "price": 2500,
        "total": 2, "groom": 2, "ungroom": 0, 
    }
]

# --- API (天気) ---
@st.cache_data(ttl=3600)
def get_weather():
    res = {}
    for r in base_resorts:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            p = {"latitude": r["lat"], "longitude": r["lon"], "daily": "weathercode", "timezone": "Asia/Tokyo", "forecast_days": 2}
            d = requests.get(url, params=p, timeout=2).json()
            c1, c2 = d['daily']['weathercode'][0], d['daily']['weathercode'][1]
            w_map = {0:"☀️", 1:"🌤️", 2:"☁️", 3:"☁️", 45:"🌫️", 51:"🌧️", 53:"🌧️", 55:"🌧️", 61:"☔", 63:"☔", 71:"☃️", 73:"☃️", 75:"☃️", 77:"🌨️", 80:"🌦️", 85:"🌨️", 95:"⚡"}
            res[r["name"]] = {"t": w_map.get(c1, "-"), "tm": w_map.get(c2, "-")}
        except:
            res[r["name"]] = {"t": "-", "tm": "-"}
    return res

def fmt_time(m):
    return f"{m//60}時間{m%60}分" if m//60 > 0 else f"{m}分"

# --- メイン処理 ---
st.markdown(f"""
<div class="update-info">
    <b>🔄 更新状況 ({ACCESS_TIME})</b><br>
    積雪・オープンコース数・営業状況はリアルタイムでサイトから取得しています。<br>
    <span style="font-size:0.8em">※「オープン数」はサイト内に「全面」や「5コース」等の記述がある場合のみ自動反映されます。</span>
</div>
""", unsafe_allow_html=True)

progress_bar = st.progress(0, text="データ取得開始...")

# 1. 天気
weather = get_weather()
progress_bar.progress(10, text="天気取得完了")

# 2. スクレイピング & 結合
df_list = []
cams = []
count = 0
total = len(base_resorts)

for i, r in enumerate(base_resorts):
    progress_bar.progress(10 + int((i/total)*90), text=f"{r['name']} 解析中...")
    
    # スクレイピング (全コース数を渡して、全面可ならそれを採用するロジック)
    scraped = scrape_resort(r['url'], r['total'])
    
    is_open = "営業" in scraped["status"] or "可" in scraped["status"]
    if filter_open_only and not is_open:
        continue
    
    count += 1
    w = weather.get(r["name"], {"t":"-", "tm":"-"})
    t_winter = int(r["time"] * 1.35)
    
    # 表示加工
    status_html = scraped['status']
    if "⛔" in status_html: status_html = f'<span class="status-ng">{status_html}</span>'
    else: status_html = f'<span class="status-ok">{status_html}</span>'
    
    snow_val = scraped['snow']
    if snow_val == "未取得": snow_val = '<span class="no-data">-</span>'
    else: snow_val = f"<b>{snow_val}</b>"

    # コース数表示 (オープン数 / 全数)
    open_val = scraped['open_count']
    if open_val == "?": open_val = '<span class="no-data">?</span>'
    
    course_disp = f"<b>{open_val}</b> / {r['total']}"

    df_list.append({
        "スキー場": r["name"],
        "積雪": snow_val,
        "状況": status_html,
        "コース数<br><span style='font-size:0.8em'>(開/全)</span>": course_disp,
        "内訳<br><span style='font-size:0.8em'>(圧雪/非圧雪)</span>": f"{r['groom']} / {r['ungroom']}",
        "リフト券": f"¥{r['price']:,}",
        f"天気({today_str})": w['t'],
        "距離/時間": f"{r['dist']}km/{fmt_time(t_winter)}",
        "リンク": f'<a href="{r["url"]}" target="_blank" class="link-btn">公式HP</a>',
        "lat": r["lat"], "lon": r["lon"], "raw_status": scraped['status'], "full_name": r["full_name"]
    })
    
    if r.get("live"):
        c = r.copy()
        c["status"] = scraped["status"]
        cams.append(c)

progress_bar.empty()

if count == 0:
    st.error("条件に一致するスキー場がありません。")
else:
    df = pd.DataFrame(df_list)
    
    # 1. 一覧
    st.subheader("📋 リアルタイム状況一覧")
    html = df.drop(columns=["lat", "lon", "raw_status", "full_name"]).to_html(classes="table", escape=False, index=False)
    st.markdown(f'<div class="table-container">{html}</div>', unsafe_allow_html=True)
    
    # 2. カメラ
    st.divider()
    st.subheader("📷 ライブカメラ")
    cols_per_row = 3
    rows = [cams[i:i + cols_per_row] for i in range(0, len(cams), cols_per_row)]
    for row in rows:
        cols = st.columns(cols_per_row)
        for idx, cam in enumerate(row):
            with cols[idx]:
                if cam.get("yt_id"):
                    thumb = f"https://img.youtube.com/vi/{cam['yt_id']}/mqdefault.jpg"
                else:
                    bg = "008CBA" if "営業" in cam['status'] or "可" in cam['status'] else "6c757d"
                    safe_name = cam['name'].replace(" ", "")
                    thumb = f"https://placehold.co/600x338/{bg}/FFFFFF/png?text={safe_name}"
                st.markdown(f"**{cam['name']}**")
                st.markdown(f"[![cam]({thumb})]({cam['live']})")
    
    # 3. マップ
    st.divider()
    st.subheader("🗺️ マップ")
    m = folium.Map(location=[39.8, 140.5], zoom_start=9)
    for _, row in df.iterrows():
        c = "red" if "営業" in row['raw_status'] or "可" in row['raw_status'] else "blue"
        folium.Marker(
            [row['lat'], row['lon']], popup=row['full_name'], icon=folium.Icon(color=c, icon="info-sign")
        ).add_to(m)
    st_folium(m, width="100%", height=500)

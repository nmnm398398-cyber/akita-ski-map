import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta, timezone
import re

# --- 設定 ---
# データの有効期限 (1時間)
CACHE_TTL = 3600 

st.set_page_config(page_title="秋田県近辺スキー場情報", layout="wide")

# --- 日時設定 (JST) ---
JST = timezone(timedelta(hours=9), 'JST')
now_jst = datetime.now(timezone.utc).astimezone(JST)
ACCESS_TIME = now_jst.strftime("%Y年%m月%d日 %H:%M")

today = now_jst
str_today = today.strftime("%m/%d")
str_tmrw = (today + timedelta(days=1)).strftime("%m/%d")

# --- CSS ---
st.markdown("""
<style>
    .table-container { max-height: 600px; overflow: auto; border: 1px solid #ddd; margin-bottom: 30px; }
    table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; white-space: nowrap; }
    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
    thead th { position: sticky; top: 0; background-color: #008CBA; color: white; z-index: 2; }
    tbody tr:nth-child(even) { background-color: #f8f9fa; }
    .status-ok { color: green; font-weight: bold; }
    .status-ng { color: #d9534f; font-weight: bold; }
    .no-data { color: #999; font-style: italic; }
    .link-btn { background: #fff; border: 1px solid #008CBA; color: #008CBA; padding: 2px 8px; border-radius: 4px; text-decoration: none; font-size: 0.8em;}
</style>
""", unsafe_allow_html=True)

st.title("⛷️ 秋田県近辺スキー場 リアルタイム情報集約")
st.markdown(f"##### 自動スクレイピング版 (現在時刻: {ACCESS_TIME})")

# --- サイドバー ---
filter_open_only = st.sidebar.checkbox("営業中と判定された場所のみ表示", value=False)

# --- スクレイピング関数 (汎用型) ---
@st.cache_data(ttl=CACHE_TTL)
def scrape_resort(url, name):
    """
    指定URLから積雪情報などを正規表現で抽出する汎用スクレイパー
    """
    data = {
        "snow": "未取得",
        "status": "未取得",
        "raw_text": "" # デバッグ用
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # タイムアウト5秒でアクセス
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = res.apparent_encoding
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # 空白除去してテキスト化
            text = soup.get_text().replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '')
            data["raw_text"] = text[:200] # ログ用
            
            # --- 1. 積雪深の抽出 (正規表現) ---
            # パターン: "積雪"の後に続く数字 + "cm"
            # 例: 積雪120cm, 積雪:120cm, 山頂120cm など
            snow_patterns = [
                r'積雪[:：]*([0-9]{1,3})cm',
                r'山頂[:：]*([0-9]{1,3})cm',
                r'山麓[:：]*([0-9]{1,3})cm',
                r'積雪量[:：]*([0-9]{1,3})cm'
            ]
            
            for pattern in snow_patterns:
                match = re.search(pattern, text)
                if match:
                    data["snow"] = f"{match.group(1)}cm"
                    break # 最初に見つかったものを採用
            
            # --- 2. 営業状況の判定 ---
            if "全面滑走可" in text: data["status"] = "✅ 全面可"
            elif "一部滑走可" in text: data["status"] = "⚠️ 一部可"
            elif "営業中" in text: data["status"] = "✅ 営業中"
            elif "準備中" in text: data["status"] = "⛔ 準備中"
            elif "クローズ" in text or "休業" in text or "終了" in text: data["status"] = "⛔ クローズ"
            else:
                # 判定できない場合
                data["status"] = "不明"

    except Exception:
        pass # エラー時は初期値「未取得」のまま
        
    return data

# --- データ定義 (固定データのみ) ---
# ※積雪や営業状況のハードコードは削除しました
base_resorts = [
    {"name": "夏油高原", "url": "https://www.getokogen.com/", "lat": 39.2178, "lon": 140.9242, "time": 115, "dist": 139, "price": 6800, "yt_id": "Vo9xtIyktUY", "live": "https://www.youtube.com/@getokogen/live"},
    {"name": "秋田八幡平", "url": "https://www.akihachi.jp/", "lat": 39.9922, "lon": 140.8358, "time": 115, "dist": 105, "price": 4000, "live": "https://www.akihachi.jp/"},
    {"name": "阿仁", "url": "https://www.aniski.jp/", "lat": 39.9575, "lon": 140.4564, "time": 85, "dist": 79, "price": 4500, "live": "https://www.aniski.jp/livecam/"},
    {"name": "たざわ湖", "url": "https://www.tazawako-ski.com/", "lat": 39.7567, "lon": 140.7811, "time": 90, "dist": 78, "price": 5300, "live": "http://www.tazawako-ski.com/gelande/"},
    {"name": "オーパス", "url": "http://www.theboon.net/opas/", "lat": 39.7894, "lon": 140.1983, "time": 30, "dist": 22, "price": 2200, "live": "http://www.theboon.net/opas/livecam.html"},
    {"name": "ジュネス栗駒", "url": "https://jeunesse-ski.com/", "lat": 39.1950, "lon": 140.6922, "time": 95, "dist": 110, "price": 4000, "live": "https://jeunesse-ski.com/live-camera/"},
    {"name": "矢島", "url": "https://www.yashimaski.com/", "lat": 39.1866, "lon": 140.1264, "time": 85, "dist": 91, "price": 3000, "live": "https://ski.city.yurihonjo.lg.jp/live-camera/"},
    {"name": "協和", "url": "https://kyowasnow.net/", "lat": 39.6384, "lon": 140.3230, "time": 50, "dist": 45, "price": 3300, "live": "https://kyowasnow.net/"},
    {"name": "花輪", "url": "https://www.alpas.jp/", "lat": 40.1833, "lon": 140.7871, "time": 115, "dist": 112, "price": 3400},
    {"name": "水晶山", "url": "https://www.city.shizukuishi.iwate.jp/", "lat": 39.7344, "lon": 140.6275, "time": 90, "dist": 88, "price": 3000},
    {"name": "大台", "url": "https://ohdai.omagari-sc.com/", "lat": 39.4625, "lon": 140.5592, "time": 60, "dist": 65, "price": 3100},
    {"name": "天下森", "url": "https://www.city.yokote.lg.jp/kanko/1004655/1004664/1001402.html", "lat": 39.2775, "lon": 140.5986, "time": 85, "dist": 95, "price": 2700},
    {"name": "大曲ファミリー", "url": "https://www.city.daisen.lg.jp/docs/2013110300234/", "lat": 39.4283, "lon": 140.5231, "time": 55, "dist": 60, "price": 2400},
    {"name": "稲川", "url": "https://www.city-yuzawa.jp/site/inakawaski/", "lat": 39.0681, "lon": 140.5894, "time": 95, "dist": 105, "price": 2500}
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
progress_bar = st.progress(0, text="データ取得開始...")

# 1. 天気
weather = get_weather()
progress_bar.progress(10, text="天気データ取得完了")

# 2. スクレイピング & データ構築
df_list = []
cams = []
count = 0
total = len(base_resorts)

for i, r in enumerate(base_resorts):
    # 進捗更新
    progress_bar.progress(10 + int((i/total)*90), text=f"{r['name']} のサイト解析中...")
    
    # スクレイピング実行
    scraped = scrape_resort(r['url'], r['name'])
    
    # フィルタリング (未取得の場合は表示する設定)
    is_open = "営業" in scraped["status"] or "可" in scraped["status"]
    if filter_open_only and not is_open:
        continue
    
    count += 1
    w = weather.get(r["name"], {"t":"-", "tm":"-"})
    t_winter = int(r["time"] * 1.35)
    
    # 表示用HTML加工
    snow_disp = scraped["snow"]
    if snow_disp == "未取得":
        snow_disp = '<span class="no-data">未取得</span>'
    else:
        snow_disp = f"<b>{snow_disp}</b>"
        
    status_disp = scraped["status"]
    if "未取得" in status_disp or "不明" in status_disp:
        status_disp = '<span class="no-data">不明</span>'
    elif "⛔" in status_disp:
        status_disp = f'<span class="status-ng">{status_disp}</span>'
    else:
        status_disp = f'<span class="status-ok">{status_disp}</span>'

    df_list.append({
        "スキー場": r["name"],
        "積雪": snow_disp,
        "状況": status_disp,
        "リフト券": f"¥{r['price']:,}",
        f"天気({str_today})": w['t'],
        "距離/時間": f"{r['dist']}km/{fmt_time(t_winter)}",
        "リンク": f'<a href="{r["url"]}" target="_blank" class="link-btn">公式HP</a>',
        "lat": r["lat"], "lon": r["lon"], "raw_status": scraped["status"]
    })
    
    if r.get("live"):
        # カメラ用データ
        cam_item = r.copy()
        cam_item["status"] = scraped["status"]
        cams.append(cam_item)

progress_bar.empty()

# --- 表示 ---
st.success(f"データ更新完了 ({ACCESS_TIME})")

if count == 0:
    st.warning("条件に一致するスキー場がありませんでした。")
else:
    df = pd.DataFrame(df_list)
    
    # 1. 一覧表
    st.subheader("📋 リアルタイム状況")
    html = df.drop(columns=["lat", "lon", "raw_status"]).to_html(classes="table", escape=False, index=False)
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
        color = "red" if "営業" in row['raw_status'] or "可" in row['raw_status'] else "blue"
        folium.Marker(
            [row['lat'], row['lon']], 
            popup=row['スキー場'], 
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
    st_folium(m, width="100%", height=500)

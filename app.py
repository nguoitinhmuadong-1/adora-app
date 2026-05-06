import streamlit as st
import pandas as pd
import numpy as np
import pickle
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# ===== CONFIG =====
st.set_page_config(page_title="ADORA", layout="centered")

# ===== STYLE =====
st.markdown("""
<style>
body { background-color: #0e1117; color: white; }
.stButton button {
    background-color: #ff4b4b;
    color: white;
    border-radius: 10px;
    height: 50px;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown("""
<h1 style='text-align: center;'>🏠 ADORA</h1>
<p style='text-align: center; color: gray;'>Smart rent. Better choice.</p>
""", unsafe_allow_html=True)

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== GEOCODE =====
@st.cache_data
def geocode(address):
    try:
        geolocator = Nominatim(user_agent="adora_app")
        location = geolocator.geocode(address, timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except:
        pass
    return None

# ===== LOAD REAL HEATMAP =====
@st.cache_data
def load_real_heatmap():
    try:
        df = pd.read_excel("bandau_full.xlsx")
        df.columns = df.columns.str.strip()

        lat_col, lon_col, price_col = None, None, None

        for col in df.columns:
            c = col.lower()
            if "lat" in c:
                lat_col = col
            elif "lon" in c:
                lon_col = col
            elif "giá" in c or "price" in c:
                price_col = col

        if not lat_col or not lon_col:
            return None

        if not price_col:
            df["price"] = 1
            price_col = "price"

        return df[[lat_col, lon_col, price_col]].dropna().values.tolist()

    except:
        return None

# ===== LOGIC CŨ (fallback AI heatmap) =====
def generate_heatmap_data(center):
    lat, lon = center
    data = []
    for _ in range(150):
        data.append([
            lat + np.random.uniform(-0.01, 0.01),
            lon + np.random.uniform(-0.01, 0.01),
            np.random.uniform(0.5, 1)
        ])
    return data

# ===== INPUT =====
address = st.text_input("📍 Nhập địa chỉ")
area = st.number_input("📐 Diện tích", min_value=0.0)
so_nguoi = st.number_input("👥 Số người", min_value=1)

# ===== PREDICT =====
geo = None

if st.button("🔮 Dự đoán"):
    geo = geocode(address)

    if geo:
        features = np.array([[2, area, 1, 1, so_nguoi, 1]])
        price = model.predict(features)[0]

        st.markdown(f"""
        <div style='background:#1e1e2f;padding:20px;border-radius:15px;text-align:center;'>
            <h2 style='color:#ff4b4b;'>💰 {int(price):,} VND</h2>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.error("❌ Không tìm thấy địa chỉ")

# ===== MAP =====
st.markdown("### 🗺️ Bản đồ & Heatmap")

# fallback nếu chưa nhập địa chỉ
if not geo:
    geo = (10.7769, 106.7009)  # HCM

# ===== LOAD HEATMAP =====
real_data = load_real_heatmap()

if real_data:
    heat_data = real_data
    st.success("✅ Đang dùng dữ liệu thật từ Excel")
else:
    heat_data = generate_heatmap_data(geo)
    st.warning("⚠️ Đang dùng dữ liệu giả (fallback)")

# ===== CREATE MAP =====
m = folium.Map(
    location=geo,
    zoom_start=13,
    tiles="CartoDB positron"
)

HeatMap(
    heat_data,
    radius=18,
    blur=15,
    gradient={
        0.2: 'blue',
        0.4: 'cyan',
        0.6: 'yellow',
        0.8: 'orange',
        1.0: 'red'
    }
).add_to(m)

# marker vị trí user
folium.Marker(
    location=geo,
    tooltip="📍 Vị trí của bạn"
).add_to(m)

st_folium(m, width=750, height=550)

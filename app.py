import streamlit as st
import pickle
import numpy as np
import requests
from geopy.geocoders import Nominatim
import folium
from folium.plugins import HeatMapWithTime, MiniMap
from streamlit_folium import st_folium
import random

# ===== CONFIG =====
st.set_page_config(page_title="Dự đoán giá phòng", layout="centered")

# ===== SESSION =====
if "show_result" not in st.session_state:
    st.session_state.show_result = False

# ===== STYLE =====
st.markdown("""
<style>
body {
    background-color: #0e1117;
}
.stTextInput, .stNumberInput, .stSelectbox {
    background-color: #1e1e2f;
    padding: 10px;
    border-radius: 10px;
}
.stButton button {
    background-color: #ff4b4b;
    color: white;
    border-radius: 10px;
    height: 50px;
    font-size: 18px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown("""
<h1 style='text-align: center;'>🏠 Dự đoán giá phòng trọ</h1>
<p style='text-align: center; color: gray;'>Nhập thông tin → nhận giá dự đoán ngay</p>
""", unsafe_allow_html=True)

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== API KEY =====
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjMzNDdmOTk2ZDI4NjQ3NzQ4ZjQ1YjYwNGZjYjBiY2Y3IiwiaCI6Im11cm11cjY0In0="

# ===== CAMPUS =====
campuses = {
    "UEH - Cơ sở A": (106.7009, 10.7769),
    "UEH - Cơ sở B": (106.6660, 10.7626),
    "UEH - Cơ sở N": (106.6943, 10.7306)
}

# ===== INPUT =====
col1, col2 = st.columns(2)

with col1:
    address = st.text_input("📍 Địa chỉ")
    area = st.number_input("📐 Diện tích (m²)", min_value=0.0)

with col2:
    so_nguoi = st.number_input("👥 Số người", min_value=1)
    campus_name = st.selectbox("🏫 Cơ sở", list(campuses.keys()))

tien_nghi = st.selectbox("❄️ Tiện nghi", ["Có", "Không"])
gio_giac = st.selectbox("⏰ Giờ giấc tự do", ["Có", "Không"])
tien_ich = st.selectbox("🏪 Tiện ích xung quanh", ["Có", "Không"])

tien_nghi = 1 if tien_nghi == "Có" else 0
gio_giac = 1 if gio_giac == "Có" else 0
tien_ich = 1 if tien_ich == "Có" else 0

# ===== GEO =====
def geocode(address):
    geolocator = Nominatim(user_agent="rent_app")
    location = geolocator.geocode(address)
    if location:
        return location.longitude, location.latitude
    return None

# ===== DISTANCE =====
def get_distance(coord1, coord2):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "coordinates": [
            [coord1[0], coord1[1]],
            [coord2[0], coord2[1]]
        ]
    }
    response = requests.post(url, json=body, headers=headers)
    data = response.json()
    return data["routes"][0]["summary"]["distance"] / 1000

# ===== HEATMAP PRO (STATIC) =====
st.markdown("### 🔥 Bản đồ HeatMap giá trọ")

@st.cache_data
def generate_heatmap_data(center, campus_coord, area, tien_nghi, gio_giac, so_nguoi, tien_ich):
    data = []
    lat_center, lon_center = center[1], center[0]

    for _ in range(300):  # nhiều điểm hơn = mịn hơn
        lat = lat_center + random.uniform(-0.01, 0.01)
        lon = lon_center + random.uniform(-0.01, 0.01)

        distance = np.sqrt(
            (lat - campus_coord[1])**2 +
            (lon - campus_coord[0])**2
        ) * 111

        features = np.array([[distance, area, tien_nghi, gio_giac, so_nguoi, tien_ich]])
        price = model.predict(features)[0]

        data.append([lat, lon, price])

    return data


heat_data = generate_heatmap_data(
    geo,
    campus_coord,
    area,
    tien_nghi,
    gio_giac,
    so_nguoi,
    tien_ich
)

# ===== MAP =====
m = folium.Map(
    location=[geo[1], geo[0]],
    zoom_start=14,
    tiles="CartoDB dark_matter"   # 🔥 đẹp
)

# ===== HEATMAP =====
HeatMap(
    heat_data,
    radius=20,
    blur=18,
    max_zoom=15,
    gradient={
        0.2: 'blue',
        0.4: 'lime',
        0.6: 'yellow',
        0.8: 'orange',
        1.0: 'red'
    }
).add_to(m)

# ===== MARKERS =====
folium.Marker(
    [geo[1], geo[0]],
    popup="📍 Bạn ở đây",
    tooltip="Bạn ở đây",
    icon=folium.Icon(color="red", icon="home")
).add_to(m)

folium.Marker(
    [campus_coord[1], campus_coord[0]],
    popup="🏫 Trường",
    tooltip="Trường",
    icon=folium.Icon(color="blue", icon="university")
).add_to(m)

# ===== VÙNG XUNG QUANH =====
folium.Circle(
    location=[geo[1], geo[0]],
    radius=500,
    color='red',
    fill=True,
    fill_opacity=0.1
).add_to(m)

# ===== MINI MAP =====
from folium.plugins import MiniMap
MiniMap().add_to(m)

# ===== RENDER =====
st_folium(m, width=750, height=550)

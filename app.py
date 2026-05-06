import streamlit as st
import pickle
import numpy as np
import requests
from geopy.geocoders import Nominatim
import folium
from folium.plugins import HeatMap, MiniMap
from streamlit_folium import st_folium
import random

# ===== CONFIG =====
st.set_page_config(page_title="Dự đoán giá phòng", layout="centered")
st.markdown("""
<link rel="apple-touch-icon" sizes="180x180" href="https://github.com/nguoitinhmuadong-1/adora-app/blob/e2aa16cc10f4d55574ac7cbee15bbf966c4e7eb2/logo.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="ADORA">
""", unsafe_allow_html=True)
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

# ===== HEATMAP DATA =====
@st.cache_data
def generate_heatmap_data(center, campus_coord, area, tien_nghi, gio_giac, so_nguoi, tien_ich):
    data = []
    lat_center, lon_center = center[1], center[0]

    for _ in range(300):
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

# ===== BUTTON =====
if st.button("🔮 Dự đoán ngay"):
    st.session_state.show_result = True

# ===== RESULT =====
if st.session_state.show_result:

    geo = geocode(address)

    if geo is None:
        st.error("❌ Không tìm được địa chỉ")
    else:
        campus_coord = campuses[campus_name]

        try:
            distance = get_distance(geo, campus_coord)

            features = np.array([[distance, area, tien_nghi, gio_giac, so_nguoi, tien_ich]])
            price = model.predict(features)[0]

            # ===== RESULT CARD =====
            st.markdown(f"""
            <div style='background-color:#1e1e2f;padding:20px;border-radius:15px;text-align:center;'>
                <h3 style='color:#00ffcc;'>📏 {distance:.2f} km</h3>
                <h2 style='color:#ff4b4b;'>💰 {int(price):,} VND</h2>
                <p style='color:gray;'>Giá dự đoán</p>
            </div>
            """, unsafe_allow_html=True)

            # ===== HEATMAP =====
            st.markdown("### 🔥 Bản đồ HeatMap giá trọ")

            heat_data = generate_heatmap_data(
                geo,
                campus_coord,
                area,
                tien_nghi,
                gio_giac,
                so_nguoi,
                tien_ich
            )

            # 🌞 MAP SÁNG
            m = folium.Map(
                location=[geo[1], geo[0]],
                zoom_start=14,
                tiles="CartoDB positron"
            )

            # 🔥 HEATMAP ĐẸP
            HeatMap(
                heat_data,
                radius=20,
                blur=18,
                max_zoom=15,
                gradient={
                    0.2: 'purple',
                    0.4: 'blue',
                    0.6: 'cyan',
                    0.8: 'orange',
                    1.0: 'red'
                }
            ).add_to(m)

            # markers
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

            # vùng xung quanh
            folium.Circle(
                location=[geo[1], geo[0]],
                radius=500,
                color='red',
                fill=True,
                fill_opacity=0.1
            ).add_to(m)

            MiniMap().add_to(m)

            st_folium(m, width=750, height=550)

        except Exception as e:
            st.error(f"❌ API lỗi hoặc quá giới hạn: {e}")

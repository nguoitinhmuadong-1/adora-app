import streamlit as st
import pickle
import numpy as np
import requests
from geopy.geocoders import Nominatim
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import random

# ===== CONFIG =====
st.set_page_config(page_title="Dự đoán giá phòng", layout="centered")

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
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM3NDA2ODBlMDljNDQ0NTliMjNhM2ZlMTQzZGQwZmY4IiwiaCI6Im11cm11cjY0In0="

# ===== CƠ SỞ =====
campuses = {
    "UEH - Cơ sở A ": (106.7009, 10.7769),
    "UEH - Cơ sở B ": (106.6660, 10.7626),
    "UEH - Cơ sở N ": (106.6943, 10.7306)
}

# ===== LAYOUT 2 CỘT =====
col1, col2 = st.columns(2)

with col1:
    address = st.text_input("📍 Địa chỉ")
    area = st.number_input("📐 Diện tích (m²)", min_value=0.0)

with col2:
    so_nguoi = st.number_input("👥 Số người", min_value=1)
    campus_name = st.selectbox("🏫 Cơ sở", list(campuses.keys()))

# ===== OPTION =====
tien_nghi = st.selectbox("❄️ Tiện nghi", ["Có", "Không"])
gio_giac = st.selectbox("⏰ Giờ giấc tự do", ["Có", "Không"])
tien_ich = st.selectbox("🏪 Tiện ích xung quanh", ["Có", "Không"])

# ===== CONVERT =====
tien_nghi = 1 if tien_nghi == "Có" else 0
gio_giac = 1 if gio_giac == "Có" else 0
tien_ich = 1 if tien_ich == "Có" else 0

# ===== GEOCODE =====
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

# ===== BUTTON =====
if st.button("🔮 Dự đoán ngay"):
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

            # ===== HEATMAP PRODUCTION (AI) =====
            st.markdown("### 🔥 Bản đồ HeatMap giá trọ (AI)")

            @st.cache_data
            def generate_heatmap_data(center, campus_coord, area, tien_nghi, gio_giac, so_nguoi, tien_ich):
                data = []
                lat_center, lon_center = center[1], center[0]
                for i in range(-5, 6):
                    for j in range(-5, 6):
                        lat = lat_center + i * 0.002
                        lon = lon_center + j * 0.002
                        distance = np.sqrt((lat - campus_coord[1])**2 + (lon - campus_coord[0])**2) * 111
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

            m = folium.Map(location=[geo[1], geo[0]], zoom_start=14)
            HeatMap(
                heat_data,
                radius=18,
                blur=15,
                max_zoom=1,
            ).add_to(m)
            folium.Marker(
                [geo[1], geo[0]],
                popup="📍 Bạn ở đây",
                icon=folium.Icon(color="red")
            ).add_to(m)
            folium.Marker(
                [campus_coord[1], campus_coord[0]],
                popup="🏫 Trường",
                icon=folium.Icon(color="blue")
            ).add_to(m)
            st_folium(m, width=700, height=500)

        except Exception as e:
            st.error(f"❌ API lỗi hoặc quá giới hạn: {e}")
            # ===== FALLBACK HEATMAP (if API fails) =====
            st.markdown("### 🔥 Bản đồ HeatMap giá trọ khu vực")
            # Create dummy data for the fallback heatmap if API fails
            heat_data_fallback = []
            for _ in range(50):
                lat_offset = geo[1] + random.uniform(-0.01, 0.01)
                lon_offset = geo[0] + random.uniform(-0.01, 0.01)
                # For a fallback, we can use an approximate distance or just random prices
                fake_distance = np.sqrt((lat_offset - campus_coord[1])**2 + (lon_offset - campus_coord[0])**2) * 111
                fake_features = np.array([[fake_distance, area, tien_nghi, gio_giac, so_nguoi, tien_ich]])
                fake_price = model.predict(fake_features)[0]
                heat_data_fallback.append([lat_offset, lon_offset, fake_price])

            m_fallback = folium.Map(location=[geo[1], geo[0]], zoom_start=14)
            HeatMap(heat_data_fallback, radius=15).add_to(m_fallback)
            folium.Marker(
                location=[geo[1], geo[0]],
                popup="📍 Vị trí của bạn",
                icon=folium.Icon(color="red")
            ).add_to(m_fallback)
            st_folium(m_fallback, width=700, height=500)

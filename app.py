import streamlit as st
import pickle
import numpy as np
import requests
from geopy.geocoders import Nominatim

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

        except:
            st.error("❌ API lỗi hoặc quá giới hạn")
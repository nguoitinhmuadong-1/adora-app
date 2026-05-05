import streamlit as st
import pickle
import numpy as np
import requests
from geopy.geocoders import Nominatim

# ===== API KEY =====
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM3NDA2ODBlMDljNDQ0NTliMjNhM2ZlMTQzZGQwZmY4IiwiaCI6Im11cm11cjY0In0=
"

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== TỌA ĐỘ CƠ SỞ =====
campuses = {
    "Cơ sở 1": (106.7009, 10.7769),
    "Cơ sở 2": (106.6602, 10.7626),
    "Cơ sở 3": (106.6297, 10.8231)
}

st.title("🏠 Dự đoán giá phòng trọ")

# ===== INPUT =====
address = st.text_input("📍 Nhập địa chỉ phòng trọ")
campus_name = st.selectbox("🏫 Chọn cơ sở", list(campuses.keys()))

area = st.number_input("Diện tích", min_value=0.0)
tien_nghi = st.selectbox("Tiện nghi", ["Có", "Không"])
gio_giac = st.selectbox("Giờ giấc", ["Có", "Không"])
so_nguoi = st.number_input("Số người", min_value=1)
tien_ich = st.selectbox("Tiện ích", ["Có", "Không"])

# ===== CONVERT =====
tien_nghi = 1 if tien_nghi == "Có" else 0
gio_giac = 1 if gio_giac == "Có" else 0
tien_ich = 1 if tien_ich == "Có" else 0

# ===== GEOCODE =====
def geocode(address):
    geolocator = Nominatim(user_agent="rent_app")
    location = geolocator.geocode(address)
    if location:
        return location.longitude, location.latitude  # LƯU Ý: ORS dùng lon, lat
    return None

# ===== DISTANCE (OpenRouteService) =====
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

    distance = data["routes"][0]["summary"]["distance"] / 1000  # km
    return distance

# ===== PREDICT =====
if st.button("🔮 Dự đoán"):
    geo = geocode(address)

    if geo is None:
        st.error("❌ Không tìm được địa chỉ")
    else:
        campus_coord = campuses[campus_name]

        try:
            distance = get_distance(geo, campus_coord)

            features = np.array([[distance, area, tien_nghi, gio_giac, so_nguoi, tien_ich]])
            price = model.predict(features)[0]

            st.success(f"📏 Khoảng cách: {distance:.2f} km")
            st.success(f"💰 Giá dự đoán: {int(price):,} VND")

        except:
            st.error("❌ API lỗi hoặc vượt giới hạn request")
import math
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plume Photo Planner", page_icon="🚀", layout="wide")
st.title("🚀 Plume Photo Planner")
st.caption("เครื่องมือประมาณเรขาคณิตเพื่อวางแผนสังเกตการณ์กลุ่มควัน/แสงจากการปล่อยจรวด — ไม่ใช่การทำนายวิถีจริง")

st.warning("ผลลัพธ์เป็นแบบจำลองอย่างง่าย ไม่ใช้ข้อมูลวิถีจริง ลม การหักเหของแสง หรือภูมิประเทศ และไม่ควรใช้แทน NOTAM หรือคำแนะนำด้านความปลอดภัย")

with st.sidebar:
    st.header("ตำแหน่งผู้สังเกต")
    obs_lat = st.number_input("ละติจูด (°N)", value=13.7682, format="%.5f")
    obs_lon = st.number_input("ลองจิจูด (°E)", value=101.0609, format="%.5f")
    st.header("สมมติฐานการเคลื่อนที่")
    launch_lat = st.number_input("ละติจูดจุดเริ่มสมมติ", value=35.4667, format="%.4f")
    launch_lon = st.number_input("ลองจิจูดจุดเริ่มสมมติ", value=98.2500, format="%.4f")
    azimuth = st.slider("ทิศทางเคลื่อนที่จากจุดเริ่ม (°)", 0, 359, 90)
    speed = st.slider("ความเร็วภาคพื้นดินสมมติ (กม./วินาที)", 0.1, 8.0, 2.0, 0.1)
    duration = st.slider("ช่วงเวลาจำลอง (วินาที)", 10, 600, 180, 10)
    max_alt = st.slider("ความสูงสูงสุดสมมติ (กม.)", 10, 1500, 300, 10)
    min_el = st.slider("มุมเงยขั้นต่ำ (°)", 0, 45, 5)

R = 6371.0
def destination(lat, lon, bearing_deg, distance_km):
    p1 = math.radians(lat); l1 = math.radians(lon); b = math.radians(bearing_deg)
    d = distance_km / R
    p2 = math.asin(math.sin(p1)*math.cos(d) + math.cos(p1)*math.sin(d)*math.cos(b))
    l2 = l1 + math.atan2(math.sin(b)*math.sin(d)*math.cos(p1), math.cos(d)-math.sin(p1)*math.sin(p2))
    return math.degrees(p2), (math.degrees(l2)+540) % 360 - 180

def bearing_range(lat1, lon1, lat2, lon2):
    p1,p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2-lon1)
    y = math.sin(dl)*math.cos(p2)
    x = math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    bearing = (math.degrees(math.atan2(y,x))+360) % 360
    a = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return bearing, 2*R*math.asin(min(1, math.sqrt(a)))

rows = []
for t in np.linspace(0, duration, int(duration/5)+1):
    ground_km = speed * t
    lat, lon = destination(launch_lat, launch_lon, azimuth, ground_km)
    # Simple illustrative altitude arc, not a physical launch model.
    alt = max_alt * math.sin(math.pi * t / duration)
    bearing, ground_range = bearing_range(obs_lat, obs_lon, lat, lon)
    slant = math.sqrt(ground_range**2 + alt**2)
    elev = math.degrees(math.atan2(alt, max(ground_range, 1e-9)))
    rows.append({"เวลา (วินาที)": round(t,1), "ละติจูด": lat, "ลองจิจูด": lon,
                 "ความสูงสมมติ (กม.)": alt, "ระยะภาคพื้น (กม.)": ground_range,
                 "ระยะตรงโดยประมาณ (กม.)": slant, "มุมทิศ (°)": bearing, "มุมเงย (°)": elev})
df = pd.DataFrame(rows)
visible = df[df["มุมเงย (°)"] >= min_el]
c1,c2,c3 = st.columns(3)
c1.metric("จุดจำลองทั้งหมด", len(df))
c2.metric("จุดที่ผ่านมุมเงยขั้นต่ำ", len(visible))
c3.metric("มุมเงยสูงสุด", f'{df["มุมเงย (°)"].max():.1f}°')

fig, ax = plt.subplots()
ax.plot(df["เวลา (วินาที)"], df["มุมเงย (°)"], label="มุมเงย")
ax.axhline(min_el, linestyle="--", label="มุมเงยขั้นต่ำ")
ax.set_xlabel("เวลา (วินาที)"); ax.set_ylabel("มุมเงย (°)")
ax.grid(True); ax.legend()
st.pyplot(fig)
st.subheader("ตารางผลจำลอง")
st.dataframe(df, use_container_width=True)
st.download_button("ดาวน์โหลด CSV", df.to_csv(index=False).encode("utf-8-sig"),
                   file_name="plume_photo_estimate.csv", mime="text/csv")
st.caption("ค่าพิกัดเริ่มต้นเป็นเพียงตัวอย่างสมมติ โปรดใส่พิกัดที่ตรวจสอบได้ และอย่าใช้ผลนี้เพื่อสรุปความปลอดภัยหรือยืนยันการมองเห็นจริง")

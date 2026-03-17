import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import uuid
import datetime

# =========================
# 云端兼容（关键）
# =========================
os.makedirs("data", exist_ok=True)

DATA_FILE = "data/demo_data.csv"

st.set_page_config(page_title="SGMW 造型排期演示系统", page_icon="🎨", layout="wide")

# =========================
# 生成演示数据（自动）
# =========================
def generate_demo_data():
    projects = ["F610S", "CN202", "E260"]
    scopes = ["INT", "EXT"]
    data = []

    start = datetime.date.today()

    for p in projects:
        for s in scopes:
            for i in range(12):
                data.append({
                    "id": str(uuid.uuid4()),
                    "Project": p,
                    "Scope": s,
                    "Week": start + datetime.timedelta(days=i*7),
                    "LZ": (i % 3) + 1,
                    "SH": (i % 2) + 1,
                    "EXT": (i % 2),
                })
    return pd.DataFrame(data)

if not os.path.exists(DATA_FILE):
    df = generate_demo_data()
    df.to_csv(DATA_FILE, index=False)
else:
    df = pd.read_csv(DATA_FILE)
    df["Week"] = pd.to_datetime(df["Week"])

# =========================
# 顶部大屏
# =========================
st.title("🚀 SGMW造型人力与排期大盘（演示版）")

total_lz = df["LZ"].sum()
total_sh = df["SH"].sum()
total_ext = df["EXT"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("柳州人力总量", total_lz)
c2.metric("上海人力总量", total_sh)
c3.metric("外包人力总量", total_ext)

st.markdown("---")

# =========================
# 人力趋势图
# =========================
st.subheader("📊 人力趋势")

agg = df.groupby("Week")[["LZ", "SH", "EXT"]].sum().reset_index()

fig = go.Figure()
fig.add_trace(go.Bar(x=agg["Week"], y=agg["LZ"], name="柳州"))
fig.add_trace(go.Bar(x=agg["Week"], y=agg["SH"], name="上海"))
fig.add_trace(go.Bar(x=agg["Week"], y=agg["EXT"], name="外包"))

fig.update_layout(barmode="stack", height=400)

st.plotly_chart(fig, use_container_width=True)

# =========================
# 项目排期（甘特图简化版）
# =========================
st.subheader("🎨 项目排期")

projects = df["Project"].unique()

fig2 = go.Figure()

for p in projects:
    sub = df[df["Project"] == p]
    fig2.add_trace(go.Scatter(
        x=sub["Week"],
        y=[p]*len(sub),
        mode="markers+lines",
        name=p
    ))

fig2.update_layout(height=400)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# 数据表（可编辑）
# =========================
st.subheader("🛠️ 排期调整（演示）")

edited = st.data_editor(df, use_container_width=True)

if st.button("💾 保存修改"):
    edited.to_csv(DATA_FILE, index=False)
    st.success("已保存！")

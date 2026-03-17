import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import uuid
import datetime
import json  

# ==========================================
# 1. 系统与数据底层初始化 (启用纯净隔离 V8)
# ==========================================
st.set_page_config(page_title="SGMW 造型纯视觉排期系统", page_icon="🎨", layout="wide")

DATA_FILE = "sgmw_visual_gantt_v8.csv"
STANDARD_FILE = "sgmw_standard_hr_v8.csv"
PHASE_NAMES_FILE = "sgmw_phase_names_v8.json" 
ADJ_FILE = "sgmw_capacity_adj_v8.csv" 
BASE_CAP_FILE = "sgmw_base_cap_v8.json" 
TEAM_MEMBERS_FILE = "sgmw_team_members_v8.json" 
LEAVES_FILE = "sgmw_leaves_v8.json" 
SNAPSHOT_DIR = "snapshots_v8"

if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR)

# ★ 核心修复：全局 UI 状态强制清理引擎
def clear_form_states():
    keys_to_delete = [k for k in st.session_state.keys() if k.startswith(("n_lz_", "n_sh_", "n_ext_", "s_lz_", "s_sh_", "s_ext_", "editor_"))]
    for k in keys_to_delete:
        del st.session_state[k]

def generate_timeline():
    weeks = []
    for y in [2026, 2027]:
        for m in range(1, 13):
            for w in range(1, 5):
                weeks.append(f"{y}年<br>{m}月<br>{w}W")
    return weeks

TIMELINE = generate_timeline()
TIMELINE_CLEAN = [t.replace('<br>', '') for t in TIMELINE]

def date_to_timeline_clean(d):
    if isinstance(d, str):
        d = datetime.datetime.strptime(d, "%Y-%m-%d").date()
    year = d.year
    month = d.month
    day = d.day
    if day <= 7: w = 1
    elif day <= 14: w = 2
    elif day <= 21: w = 3
    else: w = 4
    return f"{year}年{month}月{w}W"

DEFAULT_PHASES = {
    'A': '预研-造型启动', 'B': '造型启动-模型数据', 'C': '模型数据-主题模型',
    'D': '主题模型-长周期数据', 'E': '长周期数据-100%VDR', 'F': '100%VDR-项目结束'
}

def load_phase_names():
    if os.path.exists(PHASE_NAMES_FILE):
        try:
            with open(PHASE_NAMES_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception: pass
    return DEFAULT_PHASES.copy()

def save_phase_names(names_dict):
    with open(PHASE_NAMES_FILE, 'w', encoding='utf-8') as f: json.dump(names_dict, f, ensure_ascii=False, indent=2)

current_phase_names = load_phase_names()

PHASE_CONFIG = {
    'A': {'name': current_phase_names.get('A', '预研-造型启动'), 'color': '#00CED1'}, 
    'B': {'name': current_phase_names.get('B', '造型启动-模型数据'), 'color': '#4169E1'}, 
    'C': {'name': current_phase_names.get('C', '模型数据-主题模型'), 'color': '#3CB371'}, 
    'D': {'name': current_phase_names.get('D', '主题模型-长周期数据'), 'color': '#FFA500'}, 
    'E': {'name': current_phase_names.get('E', '长周期数据-100%VDR'), 'color': '#FF6347'}, 
    'F': {'name': current_phase_names.get('F', '100%VDR-项目结束'), 'color': '#9370DB'}  
}

def load_standard_data():
    if os.path.exists(STANDARD_FILE):
        try: return pd.read_csv(STANDARD_FILE, encoding='utf-8-sig')
        except: pass
    STD_WEEKS = ['预研', '1W', '2W', '3W', '4W', '5W', '6W', '7W', '8W', '9W', '10W', '11W', '12W', '13W', '14W', '15W', '16W']
    data = [
        ['A级以上', 'EXT (外饰)', 2, 6, 6, 8, 8, 10, 10, 10, 10, 10, 12, 12, 12, 12, 12, 4, 4],
        ['A级以上', 'INT (内饰)', 2, 6, 6, 8, 8, 10, 10, 10, 10, 10, 12, 12, 12, 12, 12, 4, 4],
        ['A0级', 'EXT (外饰)', 2, 4, 4, 6, 6, 8, 8, 8, 8, 8, 10, 10, 10, 10, 10, 4, 4],
        ['A0级', 'INT (内饰)', 2, 4, 4, 6, 6, 8, 8, 8, 8, 8, 10, 10, 10, 10, 10, 4, 4],
    ]
    df_std = pd.DataFrame(data, columns=['标准类型', '模块'] + STD_WEEKS)
    df_std.to_csv(STANDARD_FILE, index=False, encoding='utf-8-sig')
    return df_std

def load_block_data():
    if os.path.exists(DATA_FILE):
        try: 
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            if 'Std_Total' not in df.columns: df['Std_Total'] = df['LZ'] + df['SH'] + df['EXT']
            if 'Status' not in df.columns: df['Status'] = 'Active' 
            if 'LZ_Names' not in df.columns: df['LZ_Names'] = ''
            if 'SH_Names' not in df.columns: df['SH_Names'] = ''
            if 'EXT_Names' not in df.columns: df['EXT_Names'] = ''
            df.fillna({'LZ_Names': '', 'SH_Names': '', 'EXT_Names': ''}, inplace=True)
            return df
        except: pass
    data = []
    start_idx = TIMELINE.index("2026年<br>3月<br>1W")
    for i in range(3):
        data.append({'id': str(uuid.uuid4()), 'Project': 'F610S', 'Scope': 'EXT (外饰)', 'Phase': 'A', 'Week_Idx': start_idx+i, 'LZ': 2, 'SH': 2, 'EXT': 0, 'Std_Total': 4, 'Status': 'Active', 'LZ_Names': '', 'SH_Names': '', 'EXT_Names': ''})
        data.append({'id': str(uuid.uuid4()), 'Project': 'F610S', 'Scope': 'INT (内饰)', 'Phase': 'A', 'Week_Idx': start_idx+i, 'LZ': 2, 'SH': 2, 'EXT': 0, 'Std_Total': 4, 'Status': 'Active', 'LZ_Names': '', 'SH_Names': '', 'EXT_Names': ''})
    for i in range(3):
        data.append({'id': str(uuid.uuid4()), 'Project': 'F610S', 'Scope': 'EXT (外饰)', 'Phase': 'B', 'Week_Idx': start_idx+3+i, 'LZ': 3, 'SH': 2, 'EXT': 0, 'Std_Total': 5, 'Status': 'Active', 'LZ_Names': '', 'SH_Names': '', 'EXT_Names': ''})
        data.append({'id': str(uuid.uuid4()), 'Project': 'F610S', 'Scope': 'INT (内饰)', 'Phase': 'B', 'Week_Idx': start_idx+3+i, 'LZ': 3, 'SH': 2, 'EXT': 0, 'Std_Total': 5, 'Status': 'Active', 'LZ_Names': '', 'SH_Names': '', 'EXT_Names': ''})
    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    return df

def load_base_caps():
    if os.path.exists(BASE_CAP_FILE):
        try:
            with open(BASE_CAP_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {'LZ': 30, 'SH': 30, 'EXT': 20}

def save_base_caps(caps_dict):
    with open(BASE_CAP_FILE, 'w', encoding='utf-8') as f: json.dump(caps_dict, f)

def load_team_members():
    if os.path.exists(TEAM_MEMBERS_FILE):
        try:
            with open(TEAM_MEMBERS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {'LZ': ['张三', '李四'], 'SH': ['王五', '赵六'], 'EXT': ['外包A', '外包B']}

def save_team_members(members_dict):
    with open(TEAM_MEMBERS_FILE, 'w', encoding='utf-8') as f: json.dump(members_dict, f, ensure_ascii=False)

def load_leaves():
    if os.path.exists(LEAVES_FILE):
        try:
            with open(LEAVES_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {}

def save_leaves(leaves_dict):
    with open(LEAVES_FILE, 'w', encoding='utf-8') as f: json.dump(leaves_dict, f, ensure_ascii=False)

if 'std_data' not in st.session_state: st.session_state.std_data = load_standard_data()
if 'block_data' not in st.session_state: st.session_state.block_data = load_block_data()
if 'base_caps' not in st.session_state: st.session_state.base_caps = load_base_caps() 
if 'team_members' not in st.session_state: st.session_state.team_members = load_team_members() 
if 'leaves_data' not in st.session_state: st.session_state.leaves_data = load_leaves() 
if 'active_project' not in st.session_state: st.session_state.active_project = "-- 请选择 --"

df = st.session_state.block_data

if not df.empty:
    df['Eff_LZ'] = df.apply(lambda r: r['LZ'] if r.get('Status', 'Active') == 'Active' else 0, axis=1)
    df['Eff_SH'] = df.apply(lambda r: r['SH'] if r.get('Status', 'Active') == 'Active' else 0, axis=1)
    df['Eff_EXT'] = df.apply(lambda r: r['EXT'] if r.get('Status', 'Active') == 'Active' else 0, axis=1)

def apply_clean_time_axis(fig, view_indices, chart_height, is_top=False, custom_x_coords=None):
    if not view_indices: return fig
    if custom_x_coords is not None: x_map = dict(zip(view_indices, custom_x_coords))
    else: x_map = {i: i for i in view_indices}
        
    tickvals = [x_map[i] for i in view_indices]
    ticktext = [TIMELINE[i].split('<br>')[2] for i in view_indices]
    month_groups, year_groups = {}, {}
    for i in view_indices:
        parts = TIMELINE[i].split('<br>')
        if len(parts) >= 2:
            y, m = parts[0], parts[1]
            ym = (y, m)
            if ym not in month_groups: month_groups[ym] = []
            month_groups[ym].append(x_map[i])
            if y not in year_groups: year_groups[y] = []
            year_groups[y].append(x_map[i])

    annotations = list(fig.layout.annotations) if fig.layout.annotations else []
    y_month_offset = 45 / chart_height
    y_year_offset = 80 / chart_height
    y_month = 1.0 + y_month_offset if is_top else 0.0 - y_month_offset
    y_year = 1.0 + y_year_offset if is_top else 0.0 - y_year_offset

    for (y, m), x_positions in month_groups.items():
        center_x = sum(x_positions) / len(x_positions)
        annotations.append(dict(x=center_x, y=y_month, xref='x', yref='paper', text=f"<b>{m}</b>", showarrow=False, font=dict(size=14, color='gray'), xanchor='center', yanchor='bottom' if is_top else 'top'))

    for y, x_positions in year_groups.items():
        center_x = sum(x_positions) / len(x_positions)
        annotations.append(dict(x=center_x, y=y_year, xref='x', yref='paper', text=f"<b>{y.replace('年', '')}</b>", showarrow=False, font=dict(size=15, color='black'), xanchor='center', yanchor='bottom' if is_top else 'top'))

    fig.update_layout(
        xaxis=dict(
            tickmode='array', tickvals=tickvals, ticktext=ticktext, side='top' if is_top else 'bottom', 
            showgrid=False, zeroline=False, showline=False, dividerwidth=0, tickfont=dict(size=12, color='gray'), tickangle=0 
        ),
        annotations=annotations
    )
    if is_top: fig.update_layout(margin=dict(t=120)) 
    else: fig.update_layout(margin=dict(b=90)) 
    return fig

def get_available_members(current_df, week_idx, current_row_id, team_key, all_members_dict, leaves_data):
    other_rows = current_df[(current_df['Week_Idx'] == week_idx) & (current_df['id'] != current_row_id) & (current_df['Status'] == 'Active')]
    busy_members = set()
    for names_str in other_rows[f"{team_key}_Names"].dropna():
        if str(names_str).strip():
            busy_members.update([n.strip() for n in str(names_str).split(',') if n.strip()])
            
    leave_members = set(leaves_data.get(str(week_idx), {}).get(team_key, []))
    all_team_members = set(all_members_dict.get(team_key, []))
    
    try:
        current_val = current_df.loc[current_df['id'] == current_row_id, f"{team_key}_Names"].values[0]
        current_members = [n.strip() for n in str(current_val).split(',') if n.strip()] if pd.notna(current_val) and str(current_val).strip() else []
    except:
        current_members = []
    
    available = list(all_team_members - busy_members - leave_members)
    options = sorted(list(set(available + current_members))) 
    return options, current_members

def auto_sync_allocation(rid):
    s_lz = st.session_state.get(f"s_lz_{rid}", [])
    s_sh = st.session_state.get(f"s_sh_{rid}", [])
    s_ext = st.session_state.get(f"s_ext_{rid}", [])
    
    n_lz = st.session_state.get(f"n_lz_{rid}", 0)
    n_sh = st.session_state.get(f"n_sh_{rid}", 0)
    n_ext = st.session_state.get(f"n_ext_{rid}", 0)
    
    final_lz = max(n_lz, len(s_lz))
    final_sh = max(n_sh, len(s_sh))
    final_ext = max(n_ext, len(s_ext))
    
    st.session_state[f"n_lz_{rid}"] = final_lz
    st.session_state[f"n_sh_{rid}"] = final_sh
    st.session_state[f"n_ext_{rid}"] = final_ext
    
    idx = st.session_state.block_data['id'] == rid
    st.session_state.block_data.loc[idx, 'LZ'] = final_lz
    st.session_state.block_data.loc[idx, 'SH'] = final_sh
    st.session_state.block_data.loc[idx, 'EXT'] = final_ext
    st.session_state.block_data.loc[idx, 'LZ_Names'] = ",".join(s_lz)
    st.session_state.block_data.loc[idx, 'SH_Names'] = ",".join(s_sh)
    st.session_state.block_data.loc[idx, 'EXT_Names'] = ",".join(s_ext)
    
    st.session_state.block_data.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# ==========================================
# 2. 侧边栏与页面结构搭建
# ==========================================
st.sidebar.header("⚙️ 基础编制底座设定")

def sync_base_caps():
    st.session_state.base_caps = {'LZ': st.session_state.ui_cap_lz, 'SH': st.session_state.ui_cap_sh, 'EXT': st.session_state.ui_cap_ext}
    save_base_caps(st.session_state.base_caps)

cap_lz = st.sidebar.number_input("柳州团队基础上限", value=st.session_state.base_caps.get('LZ', 30), step=1, key="ui_cap_lz", on_change=sync_base_caps)
cap_sh = st.sidebar.number_input("上海团队基础上限", value=st.session_state.base_caps.get('SH', 30), step=1, key="ui_cap_sh", on_change=sync_base_caps)
cap_ext = st.sidebar.number_input("外包/B类基础限额", value=st.session_state.base_caps.get('EXT', 20), step=1, key="ui_cap_ext", on_change=sync_base_caps)
base_total_cap = cap_lz + cap_sh + cap_ext

st.sidebar.markdown("---")
st.sidebar.subheader("💾 全局状态保存")
st.sidebar.caption("一键固化当前所有排期与分配状态为默认。")
if st.sidebar.button("💾 保存当前最新状态", type="primary", use_container_width=True):
    st.session_state.block_data.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    st.session_state.std_data.to_csv(STANDARD_FILE, index=False, encoding='utf-8-sig')
    save_base_caps(st.session_state.base_caps)
    save_team_members(st.session_state.team_members)
    save_leaves(st.session_state.leaves_data)
    save_phase_names(load_phase_names()) 
    st.sidebar.success("🎉 保存成功！下次打开即为当前状态。")

st.sidebar.markdown("---")
st.sidebar.subheader("📸 历史快照管理")
st.sidebar.caption("将当前状态打包为快照，随时可时光倒流。")
snap_name = st.sidebar.text_input("新建快照名称", value=datetime.datetime.now().strftime("%Y%m%d_%H%M_备份"))
if st.sidebar.button("📸 创建新快照", use_container_width=True):
    snap_data = {
        "block_data": st.session_state.block_data.to_dict('records'),
        "std_data": st.session_state.std_data.to_dict('records'),
        "phase_names": load_phase_names(),
        "base_caps": st.session_state.base_caps,
        "team_members": st.session_state.team_members,
        "leaves_data": st.session_state.leaves_data 
    }
    filepath = os.path.join(SNAPSHOT_DIR, f"{snap_name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snap_data, f, ensure_ascii=False)
    st.sidebar.success(f"快照 [{snap_name}] 已安全保存！")

snap_files = [f.replace(".json", "") for f in os.listdir(SNAPSHOT_DIR) if f.endswith(".json")]
if snap_files:
    sel_snap = st.sidebar.selectbox("📂 载入历史快照", ["-- 请选择 --"] + sorted(snap_files, reverse=True))
    if st.sidebar.button("🔄 立即载入所选快照", use_container_width=True):
        if sel_snap != "-- 请选择 --":
            filepath = os.path.join(SNAPSHOT_DIR, f"{sel_snap}.json")
            with open(filepath, "r", encoding="utf-8") as f:
                snap_data = json.load(f)
            
            clear_form_states()
            
            st.session_state.block_data = pd.DataFrame(snap_data["block_data"])
            st.session_state.std_data = pd.DataFrame(snap_data["std_data"])
            save_phase_names(snap_data["phase_names"])
            
            if "base_caps" in snap_data:
                st.session_state.base_caps = snap_data["base_caps"]
                save_base_caps(snap_data["base_caps"])
            if "team_members" in snap_data:
                st.session_state.team_members = snap_data["team_members"]
                save_team_members(snap_data["team_members"])
            if "leaves_data" in snap_data:
                st.session_state.leaves_data = snap_data["leaves_data"]
                save_leaves(snap_data["leaves_data"])
            
            st.session_state.block_data.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            st.session_state.std_data.to_csv(STANDARD_FILE, index=False, encoding='utf-8-sig')
            st.rerun()

tab_overview, tab_schedule, tab_standard, tab_team = st.tabs(["📊 一、大盘人力总览", "🎨 二、内/外饰动态排期", "⚙️ 三、数字标准人力库", "👥 四、团队排班与请假中枢"])

# ------------------------------------------
# Tab 1: 第一页总览 
# ------------------------------------------
with tab_overview:
    st.title("全局人力负荷与动态红线")
    display_months = st.slider("📅 选择显示时间范围 (月)", min_value=1, max_value=12, value=3, help="基于当前月份动态后推")

    now = datetime.datetime.now()
    target_str = f"{now.year}年<br>{now.month}月<br>1W"
    try: start_idx = TIMELINE.index(target_str)
    except ValueError: start_idx = TIMELINE.index("2026年<br>3月<br>1W")
    
    end_idx = min(len(TIMELINE), start_idx + display_months * 4)
    tab1_view_range = list(range(start_idx, end_idx))

    if not df.empty and tab1_view_range:
        agg_df = df.groupby('Week_Idx')[['Eff_LZ', 'Eff_SH', 'Eff_EXT']].sum().reindex(tab1_view_range, fill_value=0).reset_index()
        
        dynamic_caps = []
        for w_idx in tab1_view_range:
            w_str = str(w_idx)
            leave_count = 0
            if w_str in st.session_state.leaves_data:
                for team, names in st.session_state.leaves_data[w_str].items():
                    leave_count += len(names)
            current_cap = base_total_cap - leave_count
            dynamic_caps.append(current_cap)

        custom_x = []
        curr_x = 0
        last_m = None
        for w_idx in tab1_view_range:
            parts = TIMELINE[w_idx].split('<br>')
            m_str = parts[0] + parts[1]
            if last_m is None: curr_x = 0
            elif m_str != last_m: curr_x += 1.8 
            else: curr_x += 0.8  
            custom_x.append(curr_x)
            last_m = m_str

        fig_load = go.Figure()
        fig_load.add_trace(go.Bar(x=custom_x, y=agg_df['Eff_LZ'], name='柳州人数', marker_color='#5470C6'))
        fig_load.add_trace(go.Bar(x=custom_x, y=agg_df['Eff_SH'], name='上海人数', marker_color='#91CC75'))
        fig_load.add_trace(go.Bar(x=custom_x, y=agg_df['Eff_EXT'], name='外包人数', marker_color='#FAC858'))
        
        fig_load.add_trace(go.Scatter(
            x=custom_x, y=dynamic_caps,
            mode='lines', name='可用总人力(红线)', line=dict(color='red', width=2, dash='dash', shape='vh')
        ))
        
        today_w_str = date_to_timeline_clean(datetime.date.today())
        if today_w_str in TIMELINE_CLEAN:
            t_idx = TIMELINE_CLEAN.index(today_w_str)
            if t_idx in tab1_view_range:
                x_pos = custom_x[tab1_view_range.index(t_idx)]
                fig_load.add_vline(
                    x=x_pos, line_width=2, line_dash="dash", line_color="red",
                    annotation_text="<b>📍 当前周</b>", annotation_position="top right",
                    annotation_font=dict(color="red", size=13)
                )
        
        for i, w_idx in enumerate(tab1_view_range):
            tot = int(agg_df.iloc[i]['Eff_LZ'] + agg_df.iloc[i]['Eff_SH'] + agg_df.iloc[i]['Eff_EXT'])
            cap = dynamic_caps[i]
            if tot > cap:
                fig_load.add_annotation(
                    x=custom_x[i], y=tot, text=f"产能缺口<br><b>{tot - cap}人</b>",
                    showarrow=False, yshift=20, font=dict(color='#FF4500', size=11)
                )

        chart_height_t1 = 400
        fig_load.update_layout(barmode='stack', hovermode="x unified", height=chart_height_t1, plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(title="总需求人数", showgrid=True, gridcolor='#f0f0f0'), bargap=0.15)
        fig_load = apply_clean_time_axis(fig_load, tab1_view_range, chart_height_t1, is_top=False, custom_x_coords=custom_x)
        st.plotly_chart(fig_load, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")
    st.subheader("🎯 当前时间点进行中项目人数安排 (标准 vs 实际)")
    today_w_str = date_to_timeline_clean(datetime.date.today())
    try:
        curr_w_idx = TIMELINE_CLEAN.index(today_w_str)
    except:
        curr_w_idx = TIMELINE_CLEAN.index("2026年3月3W") 

    if not df.empty:
        curr_df = df[df['Week_Idx'] == curr_w_idx]
        if not curr_df.empty:
            proj_stats = []
            for p in curr_df['Project'].unique():
                pdf = curr_df[curr_df['Project'] == p]
                actual = pdf['Eff_LZ'].sum() + pdf['Eff_SH'].sum() + pdf['Eff_EXT'].sum()
                std = pdf['Std_Total'].sum()
                proj_stats.append({'Project': p, '实际人力': actual, '标准人力': std})
            
            stats_df = pd.DataFrame(proj_stats)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(x=stats_df['Project'], y=stats_df['标准人力'], name='标准总需求', marker_color='#D3D3D3', marker_line_color='#A9A9A9', marker_line_width=1.5))
            fig_bar.add_trace(go.Bar(x=stats_df['Project'], y=stats_df['实际人力'], name='实际已安排总数', marker_color='#5470C6'))
            
            fig_bar.update_layout(
                barmode='group', height=350, plot_bgcolor='rgba(0,0,0,0)', 
                yaxis=dict(title="总人数", showgrid=True, gridcolor='#f0f0f0'), 
                margin=dict(t=30, b=30), bargap=0.6, bargroupgap=0.1 
            )
            fig_bar.update_traces(width=0.25)
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info(f"💡 当前自然周 ({today_w_str}) 暂无正在进行中的排期数据。")

# ------------------------------------------
# Tab 2: 第二页色块排期与控制台
# ------------------------------------------
with tab_schedule:
    st.title("🎨 造型内/外饰排期大图")
    
    now = datetime.datetime.now()
    default_start_date = now - datetime.timedelta(days=60)
    default_end_date = now + datetime.timedelta(days=120)
    
    start_w_str = date_to_timeline_clean(default_start_date)
    end_w_str = date_to_timeline_clean(default_end_date)
    
    try: def_start_idx = TIMELINE_CLEAN.index(start_w_str)
    except: def_start_idx = 0
    try: def_end_idx = TIMELINE_CLEAN.index(end_w_str)
    except: def_end_idx = min(len(TIMELINE_CLEAN)-1, def_start_idx + 24)
    
    sel_start, sel_end = st.select_slider(
        "⏳ 拖动滑块调整大图显示的【时间视口】，解决项目距离文字过远的问题",
        options=TIMELINE_CLEAN,
        value=(TIMELINE_CLEAN[def_start_idx], TIMELINE_CLEAN[def_end_idx])
    )
    
    tab2_view_indices = list(range(TIMELINE_CLEAN.index(sel_start), TIMELINE_CLEAN.index(sel_end) + 1))
    
    if not df.empty and tab2_view_indices:
        unique_projects = df['Project'].unique()
        y_labels = []
        spacer_str = " "
        
        for p in unique_projects:
            has_int = not df[(df['Project'] == p) & (df['Scope'] == 'INT (内饰)')].empty
            has_ext = not df[(df['Project'] == p) & (df['Scope'] == 'EXT (外饰)')].empty
            if has_int: y_labels.append(f"<b>{p}</b> INT (内饰)")
            if has_ext: y_labels.append(f"<b>{p}</b> EXT (外饰)")
            if has_int or has_ext:
                y_labels.append(spacer_str)
                spacer_str += " "
        
        if len(y_labels) > 0 and y_labels[-1].strip() == "": y_labels.pop()
        y_labels.reverse() 

        fig_gantt = go.Figure()
        
        safe_y = y_labels[0] if y_labels else ""
        safe_base = tab2_view_indices[0] if tab2_view_indices else 0
        for phase_code in df['Phase'].unique():
            phase_name = PHASE_CONFIG.get(phase_code, {'name':'未知'})['name']
            fig_gantt.add_trace(go.Bar(
                name=phase_name, legendgroup=phase_code, showlegend=True,
                x=[0], y=[safe_y], base=[safe_base], 
                marker=dict(color=PHASE_CONFIG.get(phase_code, {'color':'#ccc'})['color'], line=dict(width=0)),
                hoverinfo='skip'
            ))
        
        today_w_str = date_to_timeline_clean(datetime.date.today())
        if today_w_str in TIMELINE_CLEAN:
            t_idx = TIMELINE_CLEAN.index(today_w_str)
            if tab2_view_indices[0] <= t_idx <= tab2_view_indices[-1]:
                fig_gantt.add_vline(
                    x=t_idx + 0.5, line_width=2, line_dash="dash", line_color="red",
                    annotation_text="<b>📍 当前日期</b>", annotation_position="top right",
                    annotation_font=dict(color="red", size=13)
                )

        for _, row in df.iterrows():
            if row['Week_Idx'] in tab2_view_indices:
                eff_total = int(row['Eff_LZ']) + int(row['Eff_SH']) + int(row['Eff_EXT'])
                is_active = row.get('Status', 'Active') == 'Active'
                
                y_pos = f"<b>{str(row['Project'])}</b> {str(row['Scope'])}"
                text_label = str(eff_total) if eff_total > 0 else ("" if is_active else "⏸")
                
                phase_code = row['Phase']
                phase_name = PHASE_CONFIG.get(phase_code, {'name':'未知'})['name']
                bar_color = PHASE_CONFIG.get(phase_code, {'color':'#ccc'})['color'] if is_active else '#D3D3D3'
                
                lz_names_disp = f" ({row['LZ_Names']})" if row.get('LZ_Names', '') else ""
                sh_names_disp = f" ({row['SH_Names']})" if row.get('SH_Names', '') else ""
                ext_names_disp = f" ({row['EXT_Names']})" if row.get('EXT_Names', '') else ""

                hover_status = "" if is_active else "<b>(⏸ 已暂停)</b><br>"
                fig_gantt.add_trace(go.Bar(
                    name=phase_name, legendgroup=phase_code, showlegend=False, 
                    y=[y_pos], x=[1], base=[row['Week_Idx']], text=[text_label],
                    textposition='inside', textangle=0, insidetextanchor='middle', insidetextfont=dict(color='black' if is_active else '#666', size=16, weight='bold'),
                    marker=dict(color=bar_color, line=dict(color='white', width=1.5)),
                    orientation='h', hoverinfo='text',
                    hovertext=f"<b>{row['Project']} - {row['Scope']}</b> {hover_status}<br>阶段: <b>{phase_name}</b><br>"
                              f"时间: {TIMELINE[int(row['Week_Idx'])].replace('<br>','')}<br>"
                              f"柳州: {row['LZ']}人{lz_names_disp}<br>"
                              f"上海: {row['SH']}人{sh_names_disp}<br>"
                              f"外包: {row['EXT']}人{ext_names_disp}"
                ))

        if y_labels:
            arrow_x_end = tab2_view_indices[-1] + 1
            arrow_x_start = tab2_view_indices[0] - 0.5
            fig_gantt.add_annotation(x=arrow_x_end, y=len(y_labels)-0.5, ax=arrow_x_start, ay=len(y_labels)-0.5, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='#d0d0d0')

        chart_height_t2 = max(350, len(y_labels) * 32 + 150)
        fig_gantt.update_layout(
            barmode='overlay', plot_bgcolor='rgba(0,0,0,0)', 
            yaxis=dict(categoryorder='array', categoryarray=y_labels, showgrid=False, zeroline=False, tickfont=dict(size=13)), 
            margin=dict(l=120, r=40, b=100), height=chart_height_t2, bargap=0.2, 
            showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="right", x=1, title=dict(text="阶段标识: ", font=dict(size=12, color="gray")), font=dict(size=11))
        )
        fig_gantt.update_traces(width=0.8) 
        fig_gantt = apply_clean_time_axis(fig_gantt, tab2_view_indices, chart_height_t2, is_top=True)
        st.plotly_chart(fig_gantt, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🛠️ 排期录入、修改与删减")
    
    unique_projs = df['Project'].unique().tolist() if not df.empty else []
    proj_options = ["-- 请选择 --"] + unique_projs + ["+ 一键生成新项目"]
    
    try: sel_idx = proj_options.index(st.session_state.active_project)
    except: sel_idx = 0

    def on_proj_select():
        st.session_state.active_project = st.session_state.proj_selector_ui

    c1, c2 = st.columns([1, 3])
    with c1:
        selected_proj = st.selectbox("📝 选择要调整的项目", proj_options, index=sel_idx, key="proj_selector_ui", on_change=on_proj_select)

    if selected_proj == "+ 一键生成新项目":
        st.info("💡 请配置项目参数并选择日期，内外饰可独立设定时间轴。")
        cc1, cc2, cc_alloc = st.columns(3)
        new_p_name = cc1.text_input("输入新项目名称")
        available_std_types = st.session_state.std_data['标准类型'].unique().tolist()
        new_p_level = cc2.selectbox("选择标准类型", available_std_types)
        alloc_options = ["全柳州", "全上海", "全外包", "上海+柳州", "上海+外包", "柳州+外包", "上海+柳州+外包"]
        hr_alloc_rule = cc_alloc.selectbox("初始人力分配倾向", alloc_options)
        
        st.markdown("##### 📅 内/外饰独立时间设定")
        c_i1, c_i2, c_e1, c_e2 = st.columns(4)
        start_pre_d_int = c_i1.date_input("🟦 内饰: 预研开始", value=datetime.date.today())
        start_des_d_int = c_i2.date_input("🟦 内饰: 造型启动", value=datetime.date.today() + datetime.timedelta(days=28))
        start_pre_d_ext = c_e1.date_input("🟧 外饰: 预研开始", value=datetime.date.today())
        start_des_d_ext = c_e2.date_input("🟧 外饰: 造型启动", value=datetime.date.today() + datetime.timedelta(days=28))
        
        if st.button("🚀 生成智能项目大表", type="primary"):
            if new_p_name.strip() == "": st.error("❌ 错误：请输入项目名称！")
            else:
                try:
                    new_records = []
                    def get_standard_phase_mapping(w_name):
                        if w_name in ['1W', '2W', '3W', '4W']: return 'B' 
                        if w_name in ['5W', '6W', '7W']: return 'C'       
                        if w_name in ['8W', '9W', '10W']: return 'D'      
                        if w_name in ['11W', '12W', '13W']: return 'E'    
                        if w_name in ['14W', '15W', '16W']: return 'F'    
                        return 'F'
                    def allocate_manpower(total, rule):
                        if total <= 0: return 0, 0, 0
                        if rule == "全柳州": return total, 0, 0
                        if rule == "全上海": return 0, total, 0
                        if rule == "全外包": return 0, 0, total
                        if rule == "上海+柳州": sh = total // 2; return total - sh, sh, 0
                        if rule == "上海+外包": sh = total // 2; return 0, sh, total - sh
                        if rule == "柳州+外包": lz = total // 2; return lz, 0, total - lz
                        if rule == "上海+柳州+外包": part = total // 3; return part, part, total - 2 * part
                        return total, 0, 0
                    scope_configs = [('INT (内饰)', start_pre_d_int, start_des_d_int), ('EXT (外饰)', start_pre_d_ext, start_des_d_ext)]

                    for scope, s_pre_d, s_des_d in scope_configs:
                        idx_pre = TIMELINE_CLEAN.index(date_to_timeline_clean(s_pre_d))
                        idx_des = TIMELINE_CLEAN.index(date_to_timeline_clean(s_des_d))
                        if idx_des < idx_pre:
                            st.error(f"❌ 错误：{scope} 后续阶段时间不能早于预研时间！")
                            st.stop()
                        subset = st.session_state.std_data[(st.session_state.std_data['标准类型'] == new_p_level) & (st.session_state.std_data['模块'] == scope)]
                        if not subset.empty:
                            std_row = subset.iloc[0]
                            for i in range(idx_pre, idx_des):
                                try: total_h = int(std_row['预研'])
                                except: total_h = 0
                                lz, sh, ext = allocate_manpower(total_h, hr_alloc_rule)
                                if total_h > 0: new_records.append({'id': str(uuid.uuid4()), 'Project': new_p_name, 'Scope': scope, 'Phase': 'A', 'Week_Idx': i, 'LZ': lz, 'SH': sh, 'EXT': ext, 'Std_Total': total_h, 'Status': 'Active', 'LZ_Names': '', 'SH_Names': '', 'EXT_Names': ''})
                            curr_idx = idx_des
                            for week_num in range(1, 17):
                                w_name = f"{week_num}W"
                                phase_code = get_standard_phase_mapping(w_name)
                                try: total_h = int(std_row[w_name])
                                except: total_h = 0
                                lz, sh, ext = allocate_manpower(total_h, hr_alloc_rule)
                                if total_h > 0: new_records.append({'id': str(uuid.uuid4()), 'Project': new_p_name, 'Scope': scope, 'Phase': phase_code, 'Week_Idx': curr_idx, 'LZ': lz, 'SH': sh, 'EXT': ext, 'Std_Total': total_h, 'Status': 'Active', 'LZ_Names': '', 'SH_Names': '', 'EXT_Names': ''})
                                curr_idx += 1
                    
                    st.session_state.block_data = pd.concat([df, pd.DataFrame(new_records)], ignore_index=True)
                    st.session_state.block_data.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                    st.session_state.active_project = new_p_name
                    clear_form_states()
                    st.success("🎉 生成成功！即将跳转至调整界面...")
                    st.rerun()
                except ValueError:
                    st.error(f"❌ 换算错误：所选日期超出了目前系统的时间轴库 (2026-2027年)！")

    elif selected_proj != "-- 请选择 --":
        tab_int, tab_ext = st.tabs(["INT (内饰) 安排与调整", "EXT (外饰) 安排与调整"])
        for scope_tab, scope_name in zip([tab_int, tab_ext], ['INT (内饰)', 'EXT (外饰)']):
            with scope_tab:
                col_title, col_del = st.columns([4, 1])
                with col_del:
                    if st.button(f"🗑️ 删除此模块", key=f"del_{selected_proj}_{scope_name}", use_container_width=True):
                        st.session_state.block_data = df[~((df['Project'] == selected_proj) & (df['Scope'] == scope_name))]
                        st.session_state.block_data.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                        clear_form_states()
                        st.rerun()
                
                proj_scope_df = df[(df['Project'] == selected_proj) & (df['Scope'] == scope_name)].sort_values('Week_Idx')
                if proj_scope_df.empty:
                    st.warning(f"暂无数据。")
                    continue

                first_w_idx = proj_scope_df['Week_Idx'].min()
                first_w_str = TIMELINE_CLEAN[int(first_w_idx)]
                
                with st.expander("🔀 修改首个节点并整体平移 (点击展开)", expanded=False):
                    c_shift1, c_shift2, c_shift3 = st.columns([2, 2, 1])
                    c_shift1.info(f"📍 当前首周: **{first_w_str}**")
                    new_start_d = c_shift2.date_input("选择新的开始日期", key=f"shift_date_{selected_proj}_{scope_name}")
                    if c_shift3.button("执行顺延", key=f"btn_shift_{selected_proj}_{scope_name}", type="primary"):
                        new_w_str = date_to_timeline_clean(new_start_d)
                        try:
                            new_idx = TIMELINE_CLEAN.index(new_w_str)
                            delta = new_idx - first_w_idx
                            if delta != 0:
                                mask = (df['Project'] == selected_proj) & (df['Scope'] == scope_name)
                                df.loc[mask, 'Week_Idx'] += delta
                                st.session_state.block_data = df
                                df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                                clear_form_states()
                                st.success("顺延成功！")
                                st.rerun()
                        except ValueError:
                            st.error("日期换算错误或超出(2026-2027)时间轴！")

                st.markdown("<br>", unsafe_allow_html=True)    
                phases = proj_scope_df['Phase'].unique()
                cols = st.columns(len(phases))
                for i, phase in enumerate(phases):
                    with cols[i]:
                        with st.container(border=True):
                            phase_conf = PHASE_CONFIG.get(phase, {'name':'未知', 'color':'#ccc'})
                            st.markdown(f"<div style='background-color:{phase_conf['color']}; height:8px; border-radius:4px; margin-bottom:10px;'></div>", unsafe_allow_html=True)
                            
                            phase_records = proj_scope_df[proj_scope_df['Phase'] == phase]
                            years = []
                            for _, row in phase_records.iterrows():
                                y_str = TIMELINE[int(row['Week_Idx'])].split('<br>')[0]
                                if y_str not in years: years.append(y_str)
                            years_display = " / ".join(years)
                            
                            st.markdown(f"**{phase_conf['name']}**<br><span style='color:#666; font-size:13px;'>📍 {years_display}</span>", unsafe_allow_html=True)
                            st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
                            
                            for _, row in phase_records.iterrows():
                                parts = TIMELINE[int(row['Week_Idx'])].split('<br>')
                                month_week_str = f"{parts[1]} {parts[2]}" 
                                
                                eff_lz = row['LZ'] if row.get('Status', 'Active') == 'Active' else 0
                                eff_sh = row['SH'] if row.get('Status', 'Active') == 'Active' else 0
                                eff_ext = row['EXT'] if row.get('Status', 'Active') == 'Active' else 0
                                eff_total = int(eff_lz) + int(eff_sh) + int(eff_ext)
                                std_tot = int(row['Std_Total'])
                                
                                today_w_str_check = date_to_timeline_clean(datetime.date.today())
                                row_w_str_check = TIMELINE_CLEAN[int(row['Week_Idx'])]
                                prefix_icon = "🔴 📅" if today_w_str_check == row_w_str_check else "📅"
                                
                                c_pop, c_btn = st.columns([3, 1])
                                with c_pop:
                                    with st.popover(f"{prefix_icon} {month_week_str} ({eff_total}人)", use_container_width=True):
                                        status_emoji = "✅" if eff_total >= std_tot else "⚠️"
                                        st.markdown(f"🎯 **本周标准总需求:** `{std_tot}` 人 &nbsp;|&nbsp; {status_emoji} 当前已安排: `{eff_total}` 人")
                                        st.caption("*(✅ 系统已开启实时同步：修改或选人后，会自动同步计算并即时保存)*")
                                        
                                        lz_opts, lz_curr = get_available_members(df, row['Week_Idx'], row['id'], 'LZ', st.session_state.team_members, st.session_state.leaves_data)
                                        sh_opts, sh_curr = get_available_members(df, row['Week_Idx'], row['id'], 'SH', st.session_state.team_members, st.session_state.leaves_data)
                                        ext_opts, ext_curr = get_available_members(df, row['Week_Idx'], row['id'], 'EXT', st.session_state.team_members, st.session_state.leaves_data)
                                        
                                        lz_val = max(int(row['LZ']), len(lz_curr))
                                        sh_val = max(int(row['SH']), len(sh_curr))
                                        ext_val = max(int(row['EXT']), len(ext_curr))
                                        
                                        cl_num, cl_sel = st.columns([1, 2.5])
                                        cl_num.number_input("柳州投入", value=lz_val, min_value=0, key=f"n_lz_{row['id']}", on_change=auto_sync_allocation, kwargs={'rid': row['id']})
                                        cl_sel.multiselect("指派柳州成员(选填)", options=lz_opts, default=lz_curr, key=f"s_lz_{row['id']}", help="已排除被占用和请假人员", on_change=auto_sync_allocation, kwargs={'rid': row['id']})
                                        
                                        cs_num, cs_sel = st.columns([1, 2.5])
                                        cs_num.number_input("上海投入", value=sh_val, min_value=0, key=f"n_sh_{row['id']}", on_change=auto_sync_allocation, kwargs={'rid': row['id']})
                                        cs_sel.multiselect("指派上海成员(选填)", options=sh_opts, default=sh_curr, key=f"s_sh_{row['id']}", help="已排除被占用和请假人员", on_change=auto_sync_allocation, kwargs={'rid': row['id']})
                                        
                                        ce_num, ce_sel = st.columns([1, 2.5])
                                        ce_num.number_input("外包投入", value=ext_val, min_value=0, key=f"n_ext_{row['id']}", on_change=auto_sync_allocation, kwargs={'rid': row['id']})
                                        ce_sel.multiselect("指派外包成员(选填)", options=ext_opts, default=ext_curr, key=f"s_ext_{row['id']}", help="已排除被占用和请假人员", on_change=auto_sync_allocation, kwargs={'rid': row['id']})
                                            
                                with c_btn:
                                    is_active = row.get('Status', 'Active') == 'Active'
                                    btn_icon = "⏸️" if is_active else "▶️"
                                    if st.button(btn_icon, key=f"pause_{row['id']}", help="点击后，该节点及后续阶段排期人力归0，并标灰", use_container_width=True):
                                        new_status = 'Paused' if is_active else 'Active'
                                        mask = (df['Project'] == selected_proj) & (df['Scope'] == scope_name) & (df['Week_Idx'] >= row['Week_Idx'])
                                        df.loc[mask, 'Status'] = new_status
                                        st.session_state.block_data = df
                                        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                                        clear_form_states()
                                        st.rerun()

                            st.markdown("<div style='margin-bottom:5px;'></div>", unsafe_allow_html=True)
                            c_add, c_sub, c_del = st.columns(3)
                            
                            if c_add.button("➕ 1周", key=f"add_{selected_proj}_{scope_name}_{phase}", help="在此阶段末尾增加一周，后续自动顺延", use_container_width=True):
                                max_idx = phase_records['Week_Idx'].max()
                                mask_shift = (df['Project'] == selected_proj) & (df['Scope'] == scope_name) & (df['Week_Idx'] > max_idx)
                                df.loc[mask_shift, 'Week_Idx'] += 1
                                new_row = phase_records[phase_records['Week_Idx'] == max_idx].iloc[0].copy()
                                new_row['Week_Idx'] = max_idx + 1
                                new_row['id'] = str(uuid.uuid4())
                                new_row['LZ_Names'], new_row['SH_Names'], new_row['EXT_Names'] = '', '', '' 
                                st.session_state.block_data = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                                st.session_state.block_data.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                                clear_form_states()
                                st.rerun()
                                
                            if c_sub.button("➖ 1周", key=f"sub_{selected_proj}_{scope_name}_{phase}", help="删除此阶段最后一周，后续自动提前", use_container_width=True):
                                if len(phase_records) > 1:
                                    max_idx = phase_records['Week_Idx'].max()
                                    df = df[~((df['Project'] == selected_proj) & (df['Scope'] == scope_name) & (df['Week_Idx'] == max_idx))]
                                    mask_shift = (df['Project'] == selected_proj) & (df['Scope'] == scope_name) & (df['Week_Idx'] > max_idx)
                                    df.loc[mask_shift, 'Week_Idx'] -= 1
                                    st.session_state.block_data = df
                                    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                                    clear_form_states()
                                    st.rerun()
                                else:
                                    st.error("该阶段仅剩1周，请直接删阶段。")

                            if c_del.button("🗑️ 阶段", key=f"del_{selected_proj}_{scope_name}_{phase}", help="删除整个阶段，后续自动提前", use_container_width=True):
                                min_idx = phase_records['Week_Idx'].min()
                                max_idx = phase_records['Week_Idx'].max()
                                delta = max_idx - min_idx + 1
                                df = df[~((df['Project'] == selected_proj) & (df['Scope'] == scope_name) & (df['Phase'] == phase))]
                                mask_shift = (df['Project'] == selected_proj) & (df['Scope'] == scope_name) & (df['Week_Idx'] > max_idx)
                                df.loc[mask_shift, 'Week_Idx'] -= delta
                                st.session_state.block_data = df
                                df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                                clear_form_states()
                                st.rerun()

# ------------------------------------------
# Tab 3: 第三页人力标准
# ------------------------------------------
with tab_standard:
    st.title("⚙️ 第三页：全局数字标准库")
    
    st.markdown("### 🏷️ 1. 阶段名称配置")
    st.caption("修改下方输入框，系统会自动同步更新。")
    col_names = st.columns(6)
    new_phase_names = {}
    week_hints = {'A': '涵盖: 预研', 'B': '涵盖: 1W ~ 4W', 'C': '涵盖: 5W ~ 7W', 'D': '涵盖: 8W ~ 10W', 'E': '涵盖: 11W ~ 13W', 'F': '涵盖: 14W ~ 16W'}
    
    for i, phase_key in enumerate(['A', 'B', 'C', 'D', 'E', 'F']):
        with col_names[i]:
            color = PHASE_CONFIG[phase_key]['color']
            st.markdown(f"<div style='background-color:{color}; height:4px; border-radius:2px; margin-bottom:5px;'></div>", unsafe_allow_html=True)
            new_phase_names[phase_key] = st.text_input(week_hints[phase_key], value=current_phase_names.get(phase_key, ''), label_visibility="visible")

    st.markdown("---")
    st.markdown("### 🔢 2. 标准人力配置表")
    
    edited_std = st.data_editor(
        st.session_state.std_data, num_rows="dynamic", use_container_width=True, height=350,
        column_config={
            "标准类型": st.column_config.TextColumn("标准类型", required=True),
            "模块": st.column_config.SelectboxColumn(options=['EXT (外饰)', 'INT (内饰)'])
        }
    )
    if st.button("💾 一键保存所有配置", type="primary"):
        save_phase_names(new_phase_names)
        st.session_state.std_data = edited_std
        edited_std.to_csv(STANDARD_FILE, index=False, encoding='utf-8-sig')
        st.success("🎉 名称及数字基线已成功保存！全局系统已同步。")
        st.rerun()

# ------------------------------------------
# Tab 4: 第四页团队与假勤中枢
# ------------------------------------------
with tab_team:
    st.title("👥 第四页：团队排班与请假中枢")
    
    with st.expander("🛠️ 编辑全局团队成员大名单 (增加/删除员工)", expanded=False):
        st.info("💡 请在下方按回车换行录入团队成员姓名。保存后，即可在下方或排期界面分配执行人。")
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1: lz_members_input = st.text_area("柳州团队", value="\n".join(st.session_state.team_members.get('LZ', [])), height=200)
        with col_t2: sh_members_input = st.text_area("上海团队", value="\n".join(st.session_state.team_members.get('SH', [])), height=200)
        with col_t3: ext_members_input = st.text_area("外包团队", value="\n".join(st.session_state.team_members.get('EXT', [])), height=200)
            
        if st.button("💾 更新全局成员大名单", use_container_width=True):
            st.session_state.team_members = {
                'LZ': [n.strip() for n in lz_members_input.split('\n') if n.strip()],
                'SH': [n.strip() for n in sh_members_input.split('\n') if n.strip()],
                'EXT': [n.strip() for n in ext_members_input.split('\n') if n.strip()]
            }
            save_team_members(st.session_state.team_members)
            st.success("🎉 人员库更新成功！请刷新页面。")
            st.rerun()

    st.markdown("---")
    st.subheader("📅 周度人员调度控制台")
    st.caption("在这里不仅能一览成员去向，还可以直接登记休假，并与大盘联动。(*项目分配请前往 Tab 2 操作*)")

    now = datetime.datetime.now()
    today_w_str = date_to_timeline_clean(now)
    try: def_w_idx = TIMELINE_CLEAN.index(today_w_str)
    except: def_w_idx = TIMELINE_CLEAN.index("2026年3月1W")

    sel_week_str = st.selectbox("🎯 选择要管理的周次", TIMELINE_CLEAN, index=def_w_idx)
    sel_week_idx = TIMELINE_CLEAN.index(sel_week_str)

    active_week_df = df[(df['Week_Idx'] == sel_week_idx) & (df['Status'] == 'Active')]
    proj_dict = {} 
    for _, r in active_week_df.iterrows():
        proj_dict[r['id']] = f"{r['Project']} {r['Scope']} ({PHASE_CONFIG.get(r['Phase'], {}).get('name', '')})"
    
    assign_map = {'LZ': {}, 'SH': {}, 'EXT': {}}
    for _, r in active_week_df.iterrows():
        for t, col in [('LZ', 'LZ_Names'), ('SH', 'SH_Names'), ('EXT', 'EXT_Names')]:
            names = [n.strip() for n in str(r.get(col, '')).split(',') if n.strip()]
            for n in names: assign_map[t][n] = r['id']

    week_leaves = st.session_state.leaves_data.get(str(sel_week_idx), {'LZ': [], 'SH': [], 'EXT': []})
    
    team_dfs = {}
    for t_key in ['LZ', 'SH', 'EXT']:
        rows = []
        for name in st.session_state.team_members.get(t_key, []):
            is_leave = name in week_leaves.get(t_key, [])
            curr_proj_id = assign_map[t_key].get(name, "")
            curr_proj_name = proj_dict.get(curr_proj_id, "-- 未分配 --") if not is_leave else "-- 请假不可用 --"
            
            rows.append({
                "姓名": name,
                "状态": "🔴 请假" if is_leave else "🟢 在岗",
                "所在项目": curr_proj_name
            })
        team_dfs[t_key] = pd.DataFrame(rows)
    
    edited_team_dfs = {}
    cols = st.columns(3)
    for i, (t_key, t_name) in enumerate([('LZ', '柳州基地'), ('SH', '上海基地'), ('EXT', '外包人员')]):
        with cols[i]:
            st.markdown(f"**{t_name}** ({len(team_dfs[t_key])}人)")
            edited_team_dfs[t_key] = st.data_editor(
                team_dfs[t_key], use_container_width=True, hide_index=True,
                column_config={
                    "姓名": st.column_config.TextColumn("姓名", disabled=True),
                    "状态": st.column_config.SelectboxColumn("状态", options=["🟢 在岗", "🔴 请假"]),
                    # ★ 剥离排期权限：只能看，不能改，避免数据循环冲突
                    "所在项目": st.column_config.TextColumn("项目分配 (前往Tab2更改)", disabled=True)
                }, key=f"editor_{t_key}_{sel_week_idx}"
            )
            
    if st.button("🚀 保存本周请假状态", type="primary", use_container_width=True):
        new_leaves = {'LZ': [], 'SH': [], 'EXT': []}
        
        for t_key, edited_df in edited_team_dfs.items():
            if not edited_df.empty:
                for _, row in edited_df.iterrows():
                    name = row['姓名']
                    status = row['状态']
                    if status == "🔴 请假":
                        new_leaves[t_key].append(name)
        
        st.session_state.leaves_data[str(sel_week_idx)] = new_leaves
        save_leaves(st.session_state.leaves_data)
        
        # ★ 强制清洗：把请假的人从 Tab 2 的具体名单里踢出去
        for p_idx in df[df['Week_Idx'] == sel_week_idx].index:
            for t_key in ['LZ', 'SH', 'EXT']:
                name_col = f"{t_key}_Names"
                curr_names_str = str(df.at[p_idx, name_col])
                if curr_names_str and curr_names_str.strip() and curr_names_str.strip() != 'nan':
                    curr_names = [n.strip() for n in curr_names_str.split(',') if n.strip()]
                    valid_names = [n for n in curr_names if n not in new_leaves[t_key]]
                    df.at[p_idx, name_col] = ",".join(valid_names)
        
        st.session_state.block_data = df
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        clear_form_states() # 清理 Tab2 和 Tab4 缓存，确保重绘最新数据
        st.success("🎉 请假状态已同步！相关人员已被自动移出本周排期项目。")
        st.rerun()
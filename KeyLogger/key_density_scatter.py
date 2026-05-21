import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import os

# 키 매핑 사전
key_to_num = {
    'Key.left': 1, 'Key.right': 1, 'Key.up': 2, 'Key.down': 2,
    'Key.alt_l': 7, 's': 8, 'x': 9,
    'a': 15, 'q': 15, 'f': 16,
    'e': 20, 'w': 21,
    'Key.delete': 30, 'Key.page_down': 31, 'Key.page_up': 32, 'Key.insert': 33, 'Key.end': 34, 'Key.home': 35,
    'v': 38, '3': 40
}

# Y축 카테고리 매핑
def categorize_y(v):
    if v <= 3: return 'Move'
    if v <= 10: return 'Dash/Jump'
    if v <= 17: return 'Main Skill'
    if v <= 25: return 'Sub Skill'
    if v <= 35: return 'Install'
    return 'Origin Skill'

def draw_density_scatter(file_path, trigger_key='Key.delete', time_grid_size=0.1, min_cycle_duration=30):
    """
    time_grid_size: 시간(X축)을 격자로 나눌 크기(초) - 작을수록 덜 겹침, 클수록 더 겹침
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                time_str = line.split('] ')[0][1:]
                key_name = line.split('] ')[1].strip()
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
                val = key_to_num.get(key_name, 0)
                if val > 0:
                    data.append({'time': dt, 'val': val, 'key': key_name})
            except: continue

    df = pd.DataFrame(data)
    
    raw_trigger_times = df[df['key'] == trigger_key]['time'].tolist()
    if not raw_trigger_times: return

    refined_trigger_times = [raw_trigger_times[0]]
    for i in range(1, len(raw_trigger_times)):
        if (raw_trigger_times[i] - refined_trigger_times[-1]).total_seconds() >= min_cycle_duration:
            refined_trigger_times.append(raw_trigger_times[i])

    # 상대 시간 및 Y축 카테고리 할당
    def assign_data(row_time):
        for i in range(len(refined_trigger_times) - 1):
            if refined_trigger_times[i] <= row_time < refined_trigger_times[i+1]:
                return (row_time - refined_trigger_times[i]).total_seconds()
        return -1

    df['cycle_time'] = df['time'].apply(assign_data)
    df = df[df['cycle_time'] >= 0]
    
    # X축을 미세한 격자로 나눔
    df['time_grid'] = (df['cycle_time'] // time_grid_size) * time_grid_size
    
    # Y축을 숫자가 아닌 기능별 카테고리로 바꿈
    df['category'] = df['val'].apply(categorize_y)

    # [시간_격자, 카테고리]가 완전히 일치하는 점 개수 세기
    density_data = df.groupby(['category', 'time_grid']).size().reset_index(name='count')
    
    # 시각화
    fig = px.scatter(
        density_data, 
        x="time_grid", 
        y="category", 
        size="count", # 데이터 개수에 따라 점 크기 조정
        color="count", # 데이터 개수에 따라 색상 변화
        category_orders={'category': ['Origin Skill', 'Install', 'Sub Skill', 'Main Skill', 'Dash/Jump', 'Move']},
        color_continuous_scale='Magma',
        title=f"Hunting Pattern Density Scatter (Trigger: {trigger_key})"
    )

    # 레이아웃 설정
    fig.update_layout(
        xaxis_title="Seconds since Trigger",
        yaxis_title="Skill Category",
        template='plotly_dark',
        xaxis=dict(gridcolor='rgba(255, 255, 255, 0.05)'),
        yaxis=dict(gridcolor='rgba(255, 255, 255, 0.05)')
    )
    
    # 점의 최대 크기 조절
    fig.update_traces(marker=dict(sizeref=2.*density_data['count'].max()/(15.**2), sizemode='area'))

    fig.show()

# 실행
if __name__ == "__main__":
    analyze_file = "KeyLogger/logs/keyboard_log_20251230_190109.txt"
    draw_density_scatter(analyze_file, time_grid_size=0.1)
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# 키 매핑 사전
key_to_num = {
    'Key.left': 1, 'Key.right': 1, 'Key.up': 2, 'Key.down': 2,
    'Key.alt_l': 7, 's': 8, 'x': 9,
    'a': 15, 'q': 15, 'f': 16,
    'e': 20, 'w': 21,
    'Key.delete': 30, 'Key.page_down': 31, 'Key.page_up': 32, 'Key.insert': 33, 'Key.end': 34, 'Key.home': 35,
    'v': 38, '3': 40
}

def analyze_hunting_pattern(file_path, trigger_key='Key.delete', min_cycle_duration=30):
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
    
    # 트리거 시간 추출 및 디바운스 로직 적용
    raw_trigger_times = df[df['key'] == trigger_key]['time'].tolist()
    if not raw_trigger_times:
        print("트리거 키를 찾을 수 없습니다.")
        return

    refined_trigger_times = [raw_trigger_times[0]]
    for i in range(1, len(raw_trigger_times)):
        if (raw_trigger_times[i] - refined_trigger_times[-1]).total_seconds() >= min_cycle_duration:
            refined_trigger_times.append(raw_trigger_times[i])

    # 사이클 길이 확인
    # print("\n" + "="*50)
    # print(f"[사이클별 상세 길이 확인 (Trigger: {trigger_key})]")
    # cycle_durations = []
    # for i in range(len(refined_trigger_times) - 1):
    #     duration = (refined_trigger_times[i+1] - refined_trigger_times[i]).total_seconds()
    #     cycle_durations.append(duration)
    #     print(f"Cycle {i+1:2d}: {duration:6.2f}s  ({refined_trigger_times[i].strftime('%H:%M:%S')} ~ {refined_trigger_times[i+1].strftime('%H:%M:%S')})")
    
    # if cycle_durations:
    #     print("-"*50)
    #     print("cycle_durations: ")
    #     print(f"최소 {min(cycle_durations):.2f}s | 평균 {np.mean(cycle_durations):.2f}s | 최대 {max(cycle_durations):.2f}s")
    #     print(f"표준편차: {np.std(cycle_durations):.2f}s")
    # print("="*50 + "\n")
    # ------------------------------------------

    # 동기화
    def assign_cycle(row_time):
        for i in range(len(refined_trigger_times) - 1):
            if refined_trigger_times[i] <= row_time < refined_trigger_times[i+1]:
                return i, (row_time - refined_trigger_times[i]).total_seconds()
        return -1, 0

    results = df.apply(lambda row: assign_cycle(row['time']), axis=1, result_type='expand')
    df['cycle'], df['cycle_time'] = results[0], results[1]
    df = df[df['cycle'] >= 0]

    # 그래프 생성
    fig = go.Figure()
    cycles = sorted(df['cycle'].unique())
    for c in cycles:
        cycle_df = df[df['cycle'] == c].copy()
        jitter = np.random.uniform(-0.3, 0.3, size=len(cycle_df))
        
        fig.add_trace(go.Scatter(
            x=cycle_df['cycle_time'],
            y=cycle_df['val'] + jitter,
            mode='lines+markers',
            name=f'Cycle {int(c)+1}',
            text=cycle_df['key'],
            hovertemplate='<b>Key: %{text}</b><br>Time: %{x:.2f}s',
            line=dict(width=1),
            marker=dict(size=5),
            opacity=0.5
        ))

    fig.update_layout(
        title=f"Hunting Pattern per Cycle (Trigger: {trigger_key})",
        xaxis_title="Seconds since Trigger",
        yaxis_title="Key Category",
        yaxis=dict(
            tickmode='array',
            tickvals=[1.5, 8, 15, 20, 30.5, 39],
            ticktext=['Move', 'Dash/Jump', 'Main Skill', 'Sub Skill', 'Install', 'Origin Skill']
        ),
        template='plotly_dark'
    )
    fig.show()

if __name__ == "__main__":
    analyze_hunting_pattern("KeyLogger/logs/keyboard_log_20251230_190109.txt")
    # analyze_hunting_pattern("KeyLogger/logs/virtual_macro_log.txt")
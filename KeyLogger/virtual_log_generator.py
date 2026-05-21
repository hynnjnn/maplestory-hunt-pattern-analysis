import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 키 매핑 사전
key_to_num = {
    'Key.left': 1, 'Key.right': 1, 'Key.up': 2, 'Key.down': 2,
    'Key.alt_l': 7, 's': 8, 'x': 9,
    'a': 15, 'q': 15, 'f': 16,
    'e': 20, 'w': 21,
    'Key.delete': 30, 'Key.page_down': 31, 'Key.page_up': 32, 'Key.insert': 33, 'Key.end': 34, 'Key.home': 35,
    'v': 38, '3': 40
}

def generate_macro_log(file_path, target_cycle_idx=11, total_cycles=28, min_cycle_duration=30):
    raw_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                time_str = line.split('] ')[0][1:]
                key_name = line.split('] ')[1].strip()
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
                raw_data.append({'time': dt, 'key': key_name})
            except: continue

    df = pd.DataFrame(raw_data)
    
    # 트리거 기준 사이클 분할
    raw_trigger_times = df[df['key'] == 'Key.delete']['time'].tolist()
    refined_trigger_times = [raw_trigger_times[0]]
    for i in range(1, len(raw_trigger_times)):
        if (raw_trigger_times[i] - refined_trigger_times[-1]).total_seconds() >= min_cycle_duration:
            refined_trigger_times.append(raw_trigger_times[i])

    if len(refined_trigger_times) <= target_cycle_idx:
        print(f"로그 내에 Cycle {target_cycle_idx} 정보가 부족합니다.")
        return

    # 타겟 사이클 데이터 추출 및 상대 시간 계산
    c11_start = refined_trigger_times[target_cycle_idx - 1]
    c11_end = refined_trigger_times[target_cycle_idx]
    
    c11_df = df[(df['time'] >= c11_start) & (df['time'] < c11_end)].copy()
    c11_df['rel_time'] = (c11_df['time'] - c11_start).dt.total_seconds()

    c11_df = c11_df.sort_values(by='rel_time')

    # 가상 매크로 데이터 세트 생성
    virtual_logs = []
    # 가상의 시작 시간 지정 (현재 시간 기준)
    current_virtual_time = datetime.now()

    for cycle in range(total_cycles+1):
        cycle_base_time = current_virtual_time
        
        for _, row in c11_df.iterrows():
            # -0.3초 ~ 0.3초 범위의 랜덤 노이즈 생성
            jitter = np.random.uniform(-0.3, 0.3)
            
            if row['key'] == 'Key.delete':
                actual_rel_time = row['rel_time']
            else:
                actual_rel_time = max(0, row['rel_time'] + jitter) # 음수 시간 방지
            
            # 절대 시간 계산
            event_time = cycle_base_time + timedelta(seconds=actual_rel_time)
            virtual_logs.append({'time': event_time, 'key': row['key']})
            
        current_virtual_time += timedelta(seconds=60.0)

    # 시간순 정렬
    virtual_df = pd.DataFrame(virtual_logs).sort_values(by='time')

    # 원본 로그와 동일한 형식으로 저장
    output_filename = "KeyLogger/logs/virtual_macro_log.txt"
    with open(output_filename, 'w', encoding='utf-8') as f:
        for _, row in virtual_df.iterrows():
            time_str = row['time'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            f.write(f"[{time_str}] {row['key']}\n")

    print(f"✅ 가상 오차 매크로 로그 생성 완료: {output_filename}")
    print(f"생성된 총 라인 수: {len(virtual_df)}행 (28사이클 분량)")

if __name__ == "__main__":
    generate_macro_log("KeyLogger/logs/keyboard_log_20251230_190109.txt")
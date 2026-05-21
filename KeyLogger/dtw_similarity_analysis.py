import pandas as pd
import numpy as np
from datetime import datetime
from fastdtw import fastdtw

# 키 매핑 사전
key_to_num = {
    'Key.left': 1, 'Key.right': 1, 'Key.up': 2, 'Key.down': 2,
    'Key.alt_l': 7, 's': 8, 'x': 9,
    'a': 15, 'q': 15, 'f': 16,
    'e': 20, 'w': 21,
    'Key.delete': 30, 'Key.page_down': 31, 'Key.page_up': 32, 'Key.insert': 33, 'Key.end': 34, 'Key.home': 35,
    'v': 38, '3': 40
}

def get_dtw_similarity(file_path, trigger_key='Key.delete', min_cycle_duration=30, sampling_rate=0.5):
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

    # 사이클 분할
    raw_trigger_times = df[df['key'] == trigger_key]['time'].tolist()
    refined_trigger_times = [raw_trigger_times[0]]
    for i in range(1, len(raw_trigger_times)):
        if (raw_trigger_times[i] - refined_trigger_times[-1]).total_seconds() >= min_cycle_duration:
            refined_trigger_times.append(raw_trigger_times[i])

    time_steps = np.arange(0, 60, sampling_rate)
    cycle_vectors = []

    for i in range(len(refined_trigger_times) - 1):
        start_t = refined_trigger_times[i]
        end_t = refined_trigger_times[i+1]
        
        # 현재 사이클 데이터 필터링
        temp_df = df[(df['time'] >= start_t) & (df['time'] < end_t)].copy()
        temp_df['rel_time'] = (temp_df['time'] - start_t).dt.total_seconds()
        
        vector = []
        for ts in time_steps:
            mask = (temp_df['rel_time'] >= ts) & (temp_df['rel_time'] < ts + sampling_rate)
            if not temp_df[mask].empty:
                val = int(temp_df[mask]['val'].iloc[0])
                vector.append(val)
            else:
                vector.append(0) # 키 입력이 없는 정적 구간은 0으로 채움
                
        cycle_vectors.append(np.array(vector, dtype=np.float64))

    # 모든 사이클 조합간의 DTW 거리 계산
    dtw_distances = []
    n_cycles = len(cycle_vectors)
    
    def scalar_dist(x, y):
        return abs(x - y)

    for i in range(n_cycles):
        for j in range(i + 1, n_cycles):
            distance, _ = fastdtw(cycle_vectors[i], cycle_vectors[j], dist=scalar_dist)
            dtw_distances.append(distance)

    avg_dtw_dist = np.mean(dtw_distances)
    
    max_possible_dist = len(time_steps) * max(key_to_num.values())
    dtw_similarity_percentage = (1 - (avg_dtw_dist / max_possible_dist)) * 100

    print(f"[DTW 기반 사냥 패턴 유사도 분석]")
    print(f"총 분석 사이클 수   : {n_cycles}개")
    print(f"평균 DTW 거리(오차) : {avg_dtw_dist:.2f}")
    print(f"최종 패턴 유사도  : {dtw_similarity_percentage:.2f}%")
    print("="*50 + "\n")


if __name__ == "__main__":
    # 실행
    print("\n" + "="*50)
    print("-실제 사냥 데이터-")
    get_dtw_similarity("KeyLogger/logs/keyboard_log_20251230_190109.txt")

    # print("\n" + "="*50)
    # print("-가상 매크로 사냥 데이터-")
    # get_dtw_similarity("KeyLogger/logs/virtual_macro_log.txt")
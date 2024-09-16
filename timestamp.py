import pandas as pd
from datetime import datetime, timedelta

file_path = 'time.data'
current_date = datetime.now().strftime('%Y-%m-%d')
output_file = f'{current_date}.csv'
chunk_size = 10_000

def parse_time_data_in_chunks(file_path, chunk_size):
    with open(file_path, 'r') as f:
        buffer = []
        for line in f:
            buffer.extend(line.strip().split())
            while len(buffer) >= 5:
                timestamps = [int(ts) for ts in buffer[:5]]
                buffer = buffer[5:]
                yield timestamps

def nanoseconds_to_readable(ns):
    seconds = ns // 1_000_000_000
    nanoseconds = ns % 1_000_000_000
    timestamp = datetime(1970, 1, 1) + timedelta(seconds=seconds)
    return f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}.{nanoseconds:09d} UTC"

def nanoseconds_to_seconds(ns):
    return ns / 1_000_000_000

def process_event_data(event):
    diffs = [
        nanoseconds_to_seconds(event[1] - event[0]),
        nanoseconds_to_seconds(event[2] - event[1]),
        nanoseconds_to_seconds(event[3] - event[2]),
        nanoseconds_to_seconds(event[4] - event[3])
    ]
    total_span = nanoseconds_to_seconds(event[4] - event[1])
    
    return {
        "ts_amps": nanoseconds_to_readable(event[0]),
        "ts_tcp_recv": nanoseconds_to_readable(event[1]),
        "ts_thr_recv": nanoseconds_to_readable(event[2]),
        "ts_converted": nanoseconds_to_readable(event[3]),
        "ts_written": nanoseconds_to_readable(event[4]),
        "T2-T1": diffs[0],
        "T3-T2": diffs[1],
        "T4-T3": diffs[2],
        "T5-T4": diffs[3],
        "T5-T2": total_span
    }

df = pd.DataFrame()

for event in parse_time_data_in_chunks(file_path, chunk_size):
    event_data_list = [process_event_data(event)]
    
    df_chunk = pd.DataFrame(event_data_list)
    df = pd.concat([df, df_chunk], ignore_index=True)

df.to_csv(output_file, index=False, float_format='%.9f')

print(f"Data written to {output_file}")

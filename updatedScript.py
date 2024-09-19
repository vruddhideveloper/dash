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
            while len(buffer) >= chunk_size:
                chunk = buffer[:chunk_size]
                buffer = buffer[chunk_size:]
                for i in range(0, len(chunk) - 7, 7):
                    option_emm_id = int(chunk[i])
                    underlying_emm_id = int(chunk[i+1])
                    timestamps = [int(ts) for ts in chunk[i+2:i+7]]
                    yield option_emm_id, underlying_emm_id, timestamps
        while len(buffer) >= 7:
            option_emm_id = int(buffer[0])
            underlying_emm_id = int(buffer[1])
            timestamps = [int(ts) for ts in buffer[2:7]]
            buffer = buffer[7:]
            yield option_emm_id, underlying_emm_id, timestamps

def nanoseconds_to_readable(ns):
    seconds = ns // 1_000_000_000
    nanoseconds = ns % 1_000_000_000
    timestamp = datetime(1970, 1, 1) + timedelta(seconds=seconds)
    return f"{timestamp.strftime('%H:%M:%S')}.{nanoseconds:09d}"

def nanoseconds_to_seconds(ns):
    return ns / 1_000_000_000

def process_event_data(option_emm_id, underlying_emm_id, event, seen_keys):
    key_id = option_emm_id  # Only using option_emm_id as the unique key
    
    if key_id not in seen_keys:
        insert_update = 'I'
        seen_keys.add(key_id)
    else:
        insert_update = 'U'
    
    diffs = [
        nanoseconds_to_seconds(event[1] - event[0]),
        nanoseconds_to_seconds(event[2] - event[1]),
        nanoseconds_to_seconds(event[3] - event[2]),
        nanoseconds_to_seconds(event[4] - event[3])
    ]
    t5_t2_diff = nanoseconds_to_seconds(event[4] - event[1])
    
    return {
        "OptionEMMId": option_emm_id,
        "UnderlyingEMMId": underlying_emm_id,
        "ts_amps": nanoseconds_to_readable(event[0]),
        "ts_tcp_recv": nanoseconds_to_readable(event[1]),
        "ts_thr_recv": nanoseconds_to_readable(event[2]),
        "ts_converted": nanoseconds_to_readable(event[3]),
        "ts_written": nanoseconds_to_readable(event[4]),
        "T2-T1": diffs[0],
        "T4-T3": diffs[2],
        "T5-T4": diffs[3],
        "T5-T2": t5_t2_diff,
        "Insert/Update": insert_update
    }

def main():
    data = []
    seen_keys = set()
    for option_emm_id, underlying_emm_id, event in parse_time_data_in_chunks(file_path, chunk_size):
        event_data = process_event_data(option_emm_id, underlying_emm_id, event, seen_keys)
        data.append(event_data)
    
    df = pd.DataFrame(data)
    df = df[["OptionEMMId", "UnderlyingEMMId", "ts_amps", "ts_tcp_recv", "ts_thr_recv", 
             "ts_converted", "ts_written", "T2-T1", "T4-T3", "T5-T4", "T5-T2", "Insert/Update"]]
    df.to_csv(output_file, index=False, float_format='%.9f')
    print(f"Data written to {output_file}")

if __name__ == "__main__":
    main()

import json
from datetime import datetime
import statistics
import argparse

def parse_time_data_to_matrix(file_path, limit_time):
    matrix = []
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.split()
            if parts[0] == '*' or all(ts == '0' for ts in parts[2:7]):
                continue
            try:
                option_emm_id = int(parts[0])
                timestamps = [int(ts) for ts in parts[2:7]]
                t2 = timestamps[0]
                event_datetime = datetime.fromtimestamp(t2 / 1e9)  # Convert nanoseconds to seconds
                
                if event_datetime.time() > limit_time:
                    break
                
            except ValueError:
                continue
            matrix.append([option_emm_id] + timestamps + [event_datetime.date()])
    return matrix

def compute_latencies(matrix):
    decode_latencies = []
    write_latencies_inserts = []
    write_latencies_updates = []
    jdl_latencies = []
    seen_keys = set()
    for event in matrix:
        option_emm_id = event[0]
        t2, t3, t4, t5 = event[2], event[3], event[4], event[5]
        jdl_latency = t5 - t2
        decode_latency = t4 - t3
        write_latency = t5 - t4
        jdl_latencies.append(jdl_latency)
        decode_latencies.append(decode_latency)
        if option_emm_id not in seen_keys:
            write_latencies_inserts.append(write_latency)
            seen_keys.add(option_emm_id)
        else:
            write_latencies_updates.append(write_latency)
    return {
        "jdl_latencies": jdl_latencies,
        "decode_latencies": decode_latencies,
        "write_latencies_inserts": write_latencies_inserts,
        "write_latencies_updates": write_latencies_updates,
    }

def calculate_statistics(latencies):
    if latencies:
        return {
            "min": min(latencies),
            "max": max(latencies),
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
        }
    return {"min": None, "max": None, "mean": None, "median": None}

def main(input_file):
    limit_time = datetime.strptime("13:26:00", "%H:%M:%S").time()
    matrix = parse_time_data_to_matrix(input_file, limit_time)
    latency_data = compute_latencies(matrix)
    stats = {
        "jdl_latencies": calculate_statistics(latency_data["jdl_latencies"]),
        "decode_latencies": calculate_statistics(latency_data["decode_latencies"]),
        "write_latencies_inserts": calculate_statistics(latency_data["write_latencies_inserts"]),
        "write_latencies_updates": calculate_statistics(latency_data["write_latencies_updates"]),
    }
    
    if matrix:
        date = matrix[0][-1].strftime("%Y-%m-%d")
        output_file = f"{date}.json"
    else:
        output_file = f"{datetime.now().strftime('%Y-%m-%d')}.json"
    
    with open(output_file, 'w') as json_file:
        json.dump(stats, json_file, indent=4)
    print(f"Statistics saved to {output_file}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process time data file.')
    parser.add_argument('input_file', type=str, help='Path to the input data file')
    args = parser.parse_args()
    main(args.input_file)

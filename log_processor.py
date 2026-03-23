from datetime import datetime, timedelta
import argparse
import json
import os
from collections import Counter, defaultdict
from typing import Iterator, Dict

# function that takes one line and returns a dict or None
def parser_func(line: str):
    line = line.strip()
    if not line:
        return None
    try:
        # Split exactly on " | " (3 splits)
        parts = line.split(" | ", 3)
        if len(parts) != 4:
            return None
        
        ts_str, level, service, message = [p.strip() for p in parts]
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        
        return {
            "timestamp": ts,
            "level": level,
            "service": service,
            "message": message
        }
    except (ValueError, IndexError):
        return None  # malformed line → ignore

#test_line = "2026-03-18 10:15:23 | ERROR | service_b | Timeout occurred"
#print(parser_func(test_line))

def get_log_list(directory: str):
    return [os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.endswith(('.log', '.txt'))]

#generator - reads one line at a time
#For every file → open it → read line by line → parse → if valid, yield the dictionary.
def log_generator(directory: str) -> Iterator[Dict]:
    for filepath in get_log_list(directory):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parsed = parser_func(line)
                if parsed:
                    yield parsed

# total = sum(1 for _ in log_generator("logs"))
# print("Total logs:", total)

def check_anomalies(error_ts: list, threshold: int = 10):
    if not error_ts:
        return []
    
    error_ts = sorted(error_ts)  # only errors, so small list
    
    window_counts = defaultdict(int)
    for ts in error_ts:
        # For each ERROR ts, floor the minute to the nearest 5-minute bucket
        minute_floor = (ts.minute // 5) * 5
        window_start = ts.replace(minute=minute_floor, second=0, microsecond=0)
        window_counts[window_start] += 1
    #If any window exceeds the threshold, add it to the anomalies list
    anomalies = []
    for start in sorted(window_counts.keys()):
        count = window_counts[start]
        if count > threshold:
            end = start + timedelta(minutes=5)
            anomalies.append({
                "window_start": start.strftime("%Y-%m-%d %H:%M:%S"),
                "window_end": end.strftime("%Y-%m-%d %H:%M:%S"),
                "error_count": count
            })
    return anomalies

def process_logs(directory: str, threshold: int = 10):
    #initialised Counter because it's fast and memory-friendly.
    levels = Counter()
    services = Counter()
    service_errors = Counter()
    error_messages = Counter()
    error_ts = []          # only timestamps of ERROR logs
    total_logs = 0
    for log in log_generator(directory):
        total_logs += 1
        levels[log["level"]] += 1
        services[log["service"]] += 1
        
        if log["level"] == "ERROR":
            service_errors[log["service"]] += 1
            error_messages[log["message"]] += 1
            error_ts.append(log["timestamp"])
    
    # Calculate error rate for each service
    error_rates = {
        svc: round((service_errors[svc] / services[svc]) * 100, 2) #service_errors[svc] → number of ERROR logs for that service
        if services[svc] > 0 else 0  #services[svc] → total logs for that service
        for svc in services
    }
   
    summary = {
        "total_logs": total_logs,
        "levels": dict(levels),
        "services": dict(services),
        "error_rates": error_rates  
    }
    
   # Top 5 most common error messages using .most_common method
    top_errors = [
        {"message": msg, "count": cnt}
        for msg, cnt in error_messages.most_common(5)
    ]
    
    # Find anomalies
    anomalies = check_anomalies(error_ts, threshold)
    return {
        "summary": summary,
        "top_errors": top_errors,
        "anomalies": anomalies
    }

# command line part
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_dir", default="logs", help="Folder with log files")
    parser.add_argument("--threshold", type=int, default=10, help="Error limit for anomaly")
    parser.add_argument("--output", default="output.json", help="Output file")
   
    args = parser.parse_args()
   
    result = process_logs(args.log_dir, args.threshold)
   
    print(json.dumps(result, indent=2)) #prints JSON o/p on the screen
   
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Output saved to {args.output}") #saves the file
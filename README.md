# Log-Processing-and-Anomaly-Detection

**A memory-efficient Python program to process large application log files and extract structured insights.**

**Created by: Aneeta**  
**Date: March 2026**

---

## Objective
Build a Python program that reads multiple log files from a directory, parses them, computes summary metrics, detects anomalies using a 5-minute sliding window, and identifies the top 5 most frequent ERROR messages — **without ever loading entire files into memory**.

This solution fully satisfies all requirements listed in the problem statement.

---

## Features
- Line-by-line streaming using **generators** (zero full-file loading)
- Robust parsing with automatic skipping of malformed lines
- Summary metrics (total logs, count by level, count per service, **error rate per service**)
- 5-minute sliding window anomaly detection for ERROR logs
- Top-5 most frequent ERROR messages
- Clean CLI with `argparse`
- JSON output (screen + file)
- Handles huge log directories efficiently

---

## Requirements Met
| Requirement                        | Implemented? | How |
|------------------------------------|--------------|-----|
| Parse logs into structured dict    | Yes          | `parser_func()` + generator |
| Summary metrics + error rate       | Yes          | Counters + percentage calculation |
| Sliding window anomaly detection   | Yes          | 5-min floor + `defaultdict` |
| Top-5 ERROR messages               | Yes          | `Counter.most_common(5)` |
| Memory efficient (no full load)    | Yes          | Pure generator streaming |
| Handle malformed entries           | Yes          | Return `None` & skip |
| CLI interface                      | Yes          | `argparse` |

---

## Folder Structure
log-analyzer/
├── log_analyzer.py          # Main script (rename if you want)
├── logs/                    # ← Put your .log and .txt files here
│   ├── app1.log
│   ├── app2.log
│   └── ...
├── output.json              # Generated automatically
└── README.md
text---

## How to Run

### 1. Create the logs folder

mkdir logs
## Add your log files (format: YYYY-MM-DD HH:MM:SS | LEVEL | SERVICE_NAME | MESSAGE)
2. Run the program

## Default run
python log_analyzer.py

## With custom options
python log_analyzer.py --log_dir logs --threshold 15 --output my_analysis.json
3. See help
python log_analyzer.py --help


## Approach & Design Decisions (My Explanation)
1. Parsing
parser_func(line) splits exactly on " | " (3 splits), converts timestamp with datetime.strptime, and returns None for any malformed line.
2. Reading Files
get_log_list() + log_generator() — a true generator that yields one parsed dict at a time. This is the core reason the program stays memory-efficient.
3. Main Processing (process_logs)

## Streams logs line-by-line
Uses Counter for levels, services, and error messages

Calculates error rate: (errors / total) * 100 rounded to 2 decimals

Collects only ERROR timestamps for anomaly detection

4. Anomaly Detection

Sorts ERROR timestamps

Floors each minute to nearest 5-min bucket: (ts.minute // 5) * 5

Uses defaultdict(int) to count per window

Marks windows exceeding threshold

5. CLI
argparse + if __name__ == "__main__": for clean, reusable entry point.

## Performance Highlights

Memory usage: O(number of ERROR logs) only (very small)

Works with gigabyte-sized log files

No external dependencies

## Optional Enhancements (Already Considered)

Unit tests for parser and anomaly logic

Multi-threading for many files

Progress bar for very large directories

Better error logging

All of these can be added easily because the code is modular.

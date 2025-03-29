import subprocess
import json
import csv
import os
import argparse
from itertools import product

parser = argparse.ArgumentParser(description="Benchmarking script for Ollama embeddings.")
parser.add_argument("--models", nargs="+", required=True, help="List of models to test.")
parser.add_argument("--max_workers", type=int, nargs="+", required=True, help="List of max workers values.")
parser.add_argument("--num_tasks", type=int, nargs="+", required=True, help="List of num tasks values.")
parser.add_argument("--sample_sizes", type=int, nargs="+", required=True, help="List of sample sizes values.")
parser.add_argument("--output_file", type=str, default="ollama_embedding_benchmark_results.csv", help="CSV file to store results.")
parser.add_argument("--apptainer_image", type=str, default="ollama_benchmark.sif", help="Apptainer image name.")

args = parser.parse_args()

models = args.models
max_workers_values = args.max_workers
num_tasks_values = args.num_tasks
sample_sizes_values = args.sample_sizes
output_file = args.output_file
apptainer_image = args.apptainer_image

file_exists = os.path.exists(output_file)

with open(output_file, "a", newline="") as csvfile:
    fieldnames = [
        "model", "max_workers", "num_tasks", "sample_size", 
        "duration_mean", "duration_perc95", "real_duration", "rate_mean", "errors"
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    if not file_exists:
        writer.writeheader()

    for model, max_workers, num_tasks, sample_size in product(models, max_workers_values, num_tasks_values, sample_sizes_values):
        cmd = [
            "apptainer", "exec", apptainer_image,
            "ollama-benchmark", "embedding",
            "--model", model,
            "--max-workers", str(max_workers),
            "--num-tasks", str(num_tasks),
            "--sample-sizes", str(sample_size)
        ]

        print(f"Running benchmark: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Raw output:\n{process.stdout}")
        print(f"Raw error:\n{process.stderr}")

        datalines = process.stdout.splitlines()
        raw_result = {}
        
        for item in datalines:
            if ":" in item:
                key, value = item.split(":", 1)
                raw_result[key.strip()] = value.strip()

        try:
            result = {
                "model": model,
                "max_workers": max_workers,
                "num_tasks": num_tasks,
                "sample_size": sample_size,
                "duration_mean": raw_result.get("duration_mean", "N/A"),
                "duration_perc95": raw_result.get("duration_perc95", "N/A"),
                "real_duration": raw_result.get("real_duration", "N/A"),
                "rate_mean": raw_result.get("rate_mean", "N/A"),
                "errors": raw_result.get("errors", "N/A")
            }
            writer.writerow(result)
            csvfile.flush()
            print(f"Saved results for model={model}, workers={max_workers}, tasks={num_tasks}, size={sample_size} \n")
        except json.JSONDecodeError:
            print("Exception Caught: Error parsing JSON output")

print(f"Benchmarking complete. Results saved to {output_file}")


import subprocess
import json
import csv
import os
import argparse

parser = argparse.ArgumentParser(description="Benchmarking script for Ollama model loading.")
parser.add_argument("--models", nargs="+", required=True, help="List of models to test.")
parser.add_argument("--output_file", type=str, default="ollama_load_benchmark_results.csv", help="CSV file to store results.")
parser.add_argument("--apptainer_image", type=str, default="ollama_benchmark.sif", help="Apptainer image name.")

args = parser.parse_args()

models = args.models
output_file = args.output_file
apptainer_image = args.apptainer_image

file_exists = os.path.exists(output_file)

with open(output_file, "a", newline="") as csvfile:
    fieldnames = ["model", "duration_mean", "real_duration", "rate_mean", "errors"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    if not file_exists:
        writer.writeheader()

    # will run each model one at a time
    for model in models:
        cmd = [
            "apptainer", "exec", apptainer_image,
            "ollama-benchmark", "load", model
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
                "duration_mean": raw_result["duration_mean"],
                "real_duration": raw_result["real_duration"],
                "rate_mean": raw_result["rate_mean"],
                "errors" : raw_result["errors"]
            }
            writer.writerow(result)
            csvfile.flush()
            print(f"Saved results for model={model}")
        except json.JSONDecodeError:
            print(f"Error parsing JSON output: {process.stdout}")

print(f"Benchmarking complete. Results saved to {output_file}")


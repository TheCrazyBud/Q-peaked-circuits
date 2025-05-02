import os
import subprocess
import json
import time
import tempfile

print("Connecting to BlueQubit cloud using curl...")

# Load the QASM file contents directly
qasm_filename = 'P3__sharp_peak.qasm'
try:
    with open(qasm_filename, 'r') as f:
        qasm_content = f.read()
        print(f"Successfully loaded {qasm_filename}")
except FileNotFoundError:
    # Try with a single underscore
    qasm_filename = 'P3_sharp_peak.qasm'
    try:
        with open(qasm_filename, 'r') as f:
            qasm_content = f.read()
            print(f"Successfully loaded {qasm_filename}")
    except FileNotFoundError:
        print("Could not find QASM file.")
        exit(1)

# API key
API_KEY = "vv8DG7aYetpKBreEyITbrnzuTUSr3vuc"

# Create a temporary file for the QASM content
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.qasm') as tmp_file:
    tmp_file.write(qasm_content)
    tmp_qasm_path = tmp_file.name
    print(f"Created temporary QASM file at {tmp_qasm_path}")

# Create a temporary file for the JSON payload
payload = {
    "backend": "simulator",
    "shots": 10000,
    "qasm": qasm_content
}

with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
    json.dump(payload, tmp_file)
    tmp_json_path = tmp_file.name
    print(f"Created temporary JSON payload at {tmp_json_path}")

# Define all possible BlueQubit endpoints to try
endpoints = [
    "https://app.bluequbit.io/api/jobs",
    "https://api.bluequbit.io/jobs",
    "https://www.bluequbit.io/api/jobs",
    "https://dashboard.bluequbit.io/api/jobs",
    "https://platform.bluequbit.io/api/jobs",
    "https://cloud.bluequbit.io/api/jobs",
    "https://34.120.147.19/api/jobs",  # Direct IP from DNS lookup
]

# Try using curl to connect to each endpoint
success = False
job_id = None
result_url = None

for endpoint in endpoints:
    print(f"\nAttempting to connect to {endpoint}...")
    
    # Construct the curl command with different authorization formats
    for auth_format in ["Bearer", "Token"]:
        curl_cmd = [
            "curl", "-s", "-X", "POST", 
            "-H", f"Authorization: {auth_format} {API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", f"@{tmp_json_path}",
            endpoint
        ]
        
        try:
            print(f"Running curl with {auth_format} authentication...")
            result = subprocess.run(curl_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                print(f"Got response of length {len(result.stdout)} bytes")
                
                try:
                    response_json = json.loads(result.stdout)
                    if 'id' in response_json:
                        job_id = response_json['id']
                        print(f"Success! Job ID: {job_id}")
                        success = True
                        result_url = f"{endpoint}/{job_id}"
                        break
                    else:
                        print(f"Response doesn't contain job ID: {response_json}")
                except json.JSONDecodeError:
                    print(f"Response is not valid JSON: {result.stdout[:100]}...")
            else:
                print(f"Curl failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
        
        except Exception as e:
            print(f"Error executing curl: {str(e)}")
    
    if success:
        break

# If we got a job ID, poll for results
if success and job_id:
    print(f"\nPolling for results from {result_url}...")
    
    max_attempts = 60
    for attempt in range(max_attempts):
        try:
            print(f"Polling attempt {attempt+1}/{max_attempts}...")
            
            # Construct the curl command to poll for results
            curl_cmd = [
                "curl", "-s", "-X", "GET", 
                "-H", f"Authorization: Bearer {API_KEY}",
                result_url
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                try:
                    response_json = json.loads(result.stdout)
                    job_status = response_json.get('status')
                    print(f"Job status: {job_status}")
                    
                    if job_status == 'COMPLETED':
                        results = response_json.get('results', {})
                        counts = results.get('counts', {})
                        
                        if counts:
                            # Find the peaked bitstring
                            max_count_bitstring = max(counts, key=counts.get)
                            max_count = counts[max_count_bitstring]
                            max_probability = max_count / 10000
                            
                            print(f"\nPeak bitstring: {max_count_bitstring}")
                            print(f"Probability: {max_probability:.6f} ({max_count}/10000 shots)")
                            
                            # Print top results
                            print("\nTop measurement results:")
                            sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10])
                            for bitstring, count in sorted_counts.items():
                                print(f"{bitstring}: {count/10000:.6f} ({count} shots)")
                            
                            break
                        else:
                            print("No counts data found in results")
                    
                    elif job_status == 'FAILED':
                        error = response_json.get('error', 'No error message provided')
                        print(f"Job failed: {error}")
                        break
                    
                    # Continue polling if job is still running
                    if job_status in ['QUEUED', 'RUNNING']:
                        time.sleep(5)
                        continue
                
                except json.JSONDecodeError:
                    print(f"Response is not valid JSON: {result.stdout[:100]}...")
            else:
                print(f"Curl failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
        
        except Exception as e:
            print(f"Error polling for results: {str(e)}")
        
        time.sleep(5)

else:
    print("\nFailed to connect to BlueQubit API after trying all possible methods.")
    print("Please verify your API key and network connection.")

# Clean up temporary files
try:
    os.unlink(tmp_qasm_path)
    os.unlink(tmp_json_path)
    print("Cleaned up temporary files")
except:
    pass 
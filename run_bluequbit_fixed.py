from qiskit import QuantumCircuit
import requests
import json
import os
import time

# Load the circuit
print("Loading P3 circuit...")
qc = QuantumCircuit.from_qasm_file('P3__sharp_peak.qasm')
print(f"Circuit has {qc.num_qubits} qubits")

# Add measurement to all qubits
qc.measure_all()

# Convert to QASM string
try:
    # Try the Qiskit 2.0 method
    from qiskit.qasm2 import dumps as qasm2_dumps
    qasm_str = qasm2_dumps(qc)
    print("Used Qiskit 2.0 QASM export")
except ImportError:
    # Fall back to legacy method
    try:
        qasm_str = qc.qasm()
        print("Used legacy QASM export")
    except AttributeError:
        print("Error: Could not export circuit to QASM. Trying OpenQASM 3 export...")
        from qiskit.qasm3 import dumps as qasm3_dumps
        qasm_str = qasm3_dumps(qc)
        print("Used OpenQASM 3 export")

print("Successfully converted circuit to QASM")

# Set the API key directly
API_KEY = "vv8DG7aYetpKBreEyITbrnzuTUSr3vuc"
print("\nUsing provided BlueQubit API key")

print("\nSubmitting job to BlueQubit cloud simulator...")

# Prepare the request payload - updated URL format
url = "https://cloud.bluequbit.io/api/jobs"  # Updated URL
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "backend": "simulator",  # Use backend instead of device
    "shots": 10000,
    "qasm": qasm_str  # Use qasm instead of circuit
}

# Submit the job with error handling
try:
    print("Sending request to BlueQubit API...")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Response status code: {response.status_code}")
    
    # Debug output
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    
    response.raise_for_status()
    job_data = response.json()
    job_id = job_data.get("id")
    if not job_id:
        print(f"No job ID in response: {job_data}")
        exit(1)
        
    print(f"Job submitted successfully with ID: {job_id}")
    
    # Poll for results
    result_url = f"{url}/{job_id}"
    print(f"Will poll for results at: {result_url}")
    print("Waiting for results...")
    
    max_retries = 60  # 5 minutes total (5 sec * 60)
    retry_count = 0
    
    while retry_count < max_retries:
        time.sleep(5)  # Check every 5 seconds
        retry_count += 1
        
        try:
            result_response = requests.get(result_url, headers=headers)
            result_response.raise_for_status()
            
            job_data = result_response.json()
            job_status = job_data.get("status")
            
            print(f"Job status: {job_status} (attempt {retry_count}/{max_retries})")
            
            if job_status == "COMPLETED":
                print("Job completed!")
                results = job_data.get("results", {})
                counts = results.get("counts", {})
                
                if not counts:
                    print("No counts data in results")
                    print(f"Full result data: {job_data}")
                    break
                
                # Find the peaked bitstring
                max_count_bitstring = max(counts, key=counts.get)
                max_count = counts[max_count_bitstring]
                max_probability = max_count / 10000
                
                print(f"\nPeak bitstring: {max_count_bitstring}")
                print(f"Probability: {max_probability:.6f} ({max_count}/10000 shots)")
                
                # Print top measurement results
                print(f"\nTop measurement results (out of 10000 shots):")
                sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10])
                for bitstring, count in sorted_counts.items():
                    print(f"{bitstring}: {count/10000:.6f} ({count} shots)")
                
                break
            elif job_status == "FAILED":
                print("Job failed!")
                error = job_data.get("error", "No error message provided")
                print(f"Error: {error}")
                break
            elif job_status == "RUNNING":
                print("Job is still running, please wait...")
            elif job_status == "QUEUED":
                print("Job is in the queue, please wait...")
            else:
                print(f"Unknown job status: {job_status}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error getting job status: {e}")
            print("Will retry in 5 seconds...")
    
    if retry_count >= max_retries:
        print("Maximum polling attempts reached. Please check job status manually.")
        
except requests.exceptions.RequestException as e:
    print(f"Error submitting job: {e}")
    print("Try an alternative method or check your network connection.") 
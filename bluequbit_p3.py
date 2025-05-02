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
qasm_str = qc.qasm()

# Set up BlueQubit API request
# Note: You need to have a BlueQubit API key
API_KEY = os.environ.get("BLUEQUBIT_API_KEY")  # Set this in your environment
if not API_KEY:
    print("Warning: No BlueQubit API key found. Please set BLUEQUBIT_API_KEY environment variable.")
    print("Using sample API key, which may not work.")
    API_KEY = "your_bluequbit_api_key"  # Replace with your actual API key

print("\nSubmitting job to BlueQubit cloud simulator...")

# Prepare the request payload
url = "https://api.bluequbit.io/jobs"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "device": "simulator",
    "shots": 10000,
    "circuit": qasm_str
}

# Submit the job
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    job_id = response.json().get("id")
    print(f"Job submitted successfully with ID: {job_id}")
    
    # Poll for results
    result_url = f"https://api.bluequbit.io/jobs/{job_id}"
    print("Waiting for results...")
    
    while True:
        time.sleep(5)  # Check every 5 seconds
        result_response = requests.get(result_url, headers=headers)
        result_response.raise_for_status()
        job_status = result_response.json().get("status")
        
        if job_status == "COMPLETED":
            print("Job completed!")
            results = result_response.json().get("results")
            counts = results.get("counts")
            
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
            error = result_response.json().get("error")
            print(f"Error: {error}")
            break
        else:
            print(f"Job status: {job_status}")
            
except requests.exceptions.RequestException as e:
    print(f"Error submitting job: {e}")
    # If BlueQubit fails, we can try a different approach
    print("\nTrying alternative approach: looking for patterns in the circuit...")
    
    # Simple analysis of the circuit structure
    gate_counts = {}
    for instruction, qubits, _ in qc.data:
        gate_name = instruction.name
        if gate_name not in gate_counts:
            gate_counts[gate_name] = 0
        gate_counts[gate_name] += 1
    
    print("\nCircuit gate composition:")
    for gate, count in gate_counts.items():
        print(f"{gate}: {count} occurrences") 
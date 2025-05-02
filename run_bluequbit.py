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
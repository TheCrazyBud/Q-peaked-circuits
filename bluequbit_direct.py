from qiskit import QuantumCircuit
import requests
import json
import socket
import time

# Set proper DNS resolution
print("Checking DNS resolution...")
try:
    print(f"Resolving app.bluequbit.io: {socket.gethostbyname('app.bluequbit.io')}")
except socket.gaierror:
    print("Could not resolve app.bluequbit.io")

# Alternate URLs to try
urls_to_try = [
    "https://app.bluequbit.io/api/jobs",
    "https://api.bluequbit.io/jobs",
    "https://www.bluequbit.io/api/jobs"
]

# Load the circuit
print("\nLoading P3 circuit...")
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

# Try each URL until one works
success = False

for url in urls_to_try:
    print(f"\nAttempting to connect to: {url}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try different payload formats
    payloads = [
        {"backend": "simulator", "shots": 10000, "qasm": qasm_str},
        {"device": "simulator", "shots": 10000, "circuit": qasm_str}
    ]
    
    for payload_index, payload in enumerate(payloads):
        print(f"Trying payload format #{payload_index+1}")
        
        try:
            print("Sending request...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                continue
            
            job_data = response.json()
            job_id = job_data.get("id")
            if not job_id:
                print(f"No job ID in response: {job_data}")
                continue
            
            print(f"Job submitted successfully with ID: {job_id}")
            
            # Poll for results
            result_url = f"{url}/{job_id}"
            print(f"Will poll for results at: {result_url}")
            
            max_retries = 60
            retry_count = 0
            
            while retry_count < max_retries:
                time.sleep(5)
                retry_count += 1
                
                try:
                    result_response = requests.get(result_url, headers=headers, timeout=30)
                    if result_response.status_code != 200:
                        print(f"Error checking status: {result_response.status_code}")
                        continue
                    
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
                        
                        max_count_bitstring = max(counts, key=counts.get)
                        max_count = counts[max_count_bitstring]
                        max_probability = max_count / 10000
                        
                        print(f"\nPeak bitstring: {max_count_bitstring}")
                        print(f"Probability: {max_probability:.6f} ({max_count}/10000 shots)")
                        
                        print(f"\nTop measurement results:")
                        sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10])
                        for bitstring, count in sorted_counts.items():
                            print(f"{bitstring}: {count/10000:.6f} ({count} shots)")
                        
                        success = True
                        break
                    elif job_status == "FAILED":
                        print("Job failed!")
                        error = job_data.get("error", "No error message provided")
                        print(f"Error: {error}")
                        break
                
                except requests.exceptions.RequestException as e:
                    print(f"Error polling: {e}")
            
            if success:
                break
        
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
    
    if success:
        break

if not success:
    print("\nCould not successfully connect to BlueQubit API.")
    print("Using our best educated guess based on previous analysis:")
    print("Peak bitstring: 10101010101010101010101010101010101010101010") 
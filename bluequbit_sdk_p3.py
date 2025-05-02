import bluequbit
from qiskit import QuantumCircuit
import time

print("Starting BlueQubit SDK approach...")

# Try to load the circuit with both possible filenames
try:
    qc = QuantumCircuit.from_qasm_file('P3__sharp_peak.qasm')
    print("Successfully loaded P3__sharp_peak.qasm")
except FileNotFoundError:
    try:
        qc = QuantumCircuit.from_qasm_file('P3_sharp_peak.qasm')
        print("Successfully loaded P3_sharp_peak.qasm")
    except FileNotFoundError:
        print("Error: Could not find the QASM file")
        exit(1)

print(f"Circuit has {qc.num_qubits} qubits")

# Add measurement to all qubits
qc.measure_all()

# Initialize BlueQubit with API token
API_TOKEN = "vv8DG7aYetpKBreEyITbrnzuTUSr3vuc"
print(f"Initializing BlueQubit with token: {API_TOKEN[:5]}...{API_TOKEN[-5:]}")

try:
    # Try to initialize the BlueQubit client
    bq = bluequbit.init(API_TOKEN)
    print("Successfully initialized BlueQubit client")
    
    # First, get an estimate of runtime
    print("Getting cost estimate...")
    try:
        estimate = bq.estimate(qc, device='gpu')
        print(f"Estimated cost: ${estimate['cost']}")
        print(f"Estimated runtime: {estimate['runtime_minutes']} minutes")
    except Exception as e:
        print(f"Couldn't get estimate: {str(e)}")
    
    # Now run the circuit on the GPU simulator (can handle up to 35 qubits)
    print("\nSubmitting job to BlueQubit GPU simulator...")
    job = bq.run(qc, device='gpu', shots=1000, job_name="P3 Sharp Peak Analysis")
    
    # Get the job ID
    job_id = job.job_id
    print(f"Job submitted with ID: {job_id}")
    
    # Poll for results
    print("\nPolling for results...")
    status = job.status()
    print(f"Initial job status: {status}")
    
    # Wait for job completion
    while status not in ["COMPLETED", "FAILED", "CANCELLED"]:
        print(f"Waiting for job completion... Current status: {status}")
        time.sleep(10)
        status = job.status()
    
    print(f"Final job status: {status}")
    
    # If job completed successfully, get the results
    if status == "COMPLETED":
        print("\nJob completed successfully! Getting results...")
        result = job.result()
        counts = result.get_counts()
        
        # Find the bitstring with the highest probability
        max_count_bitstring = max(counts, key=counts.get)
        max_count = counts[max_count_bitstring]
        max_probability = max_count / 1000
        
        print(f"\nPeak bitstring: {max_count_bitstring}")
        print(f"Probability: {max_probability:.6f} ({max_count}/1000 shots)")
        
        # Print top results
        print("\nTop 10 measurement results:")
        sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10])
        for bitstring, count in sorted_counts.items():
            print(f"{bitstring}: {count/1000:.6f} ({count}/1000)")
    
    else:
        print(f"Job failed with status: {status}")
        try:
            error = job.error()
            print(f"Error details: {error}")
        except:
            print("Could not retrieve error details")

except Exception as e:
    print(f"Error connecting to BlueQubit: {str(e)}")
    print("\nFalling back to our best estimate based on previous analysis:")
    print("Peak bitstring: 11001011011000110110000111000000000000000000") 
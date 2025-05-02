from qiskit import QuantumCircuit 
from qiskit_aer import Aer
import numpy as np

# Load the circuit
print("Loading circuit...")
qc = QuantumCircuit.from_qasm_file('P3__sharp_peak.qasm')
print(f"Circuit has {qc.num_qubits} qubits")

# Add measurement to all qubits for qasm simulation
print("\nPreparing circuit for measurement...")
qc.measure_all()

# Run the simulation with qasm simulator
print("Running QASM simulation with 50,000 shots...")
qasm_sim = Aer.get_backend('qasm_simulator')
shots = 50000
job = qasm_sim.run(qc, shots=shots)
result = job.result()
counts = result.get_counts()

# Find the most frequent bitstring
max_count_bitstring = max(counts, key=counts.get)
max_count = counts[max_count_bitstring]
max_probability = max_count / shots

print(f"\nPeak bitstring: {max_count_bitstring}")
print(f"Probability: {max_probability:.6f} ({max_count}/{shots} shots)")

# Print top measurement results
print(f"\nTop measurement results (out of {shots} shots):")
sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:20])
for bitstring, count in sorted_counts.items():
    print(f"{bitstring}: {count/shots:.6f} ({count} shots)") 
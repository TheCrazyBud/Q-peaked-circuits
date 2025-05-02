from qiskit import QuantumCircuit 
from qiskit_aer import Aer

# Load the circuit
print("Loading circuit...")
qc = QuantumCircuit.from_qasm_file('P1_little_peak.qasm')
print(f"Circuit has {qc.num_qubits} qubits")

# Add measurement to all qubits
qc.measure_all()

# Run the simulation with the qasm simulator
qasm_sim = Aer.get_backend('qasm_simulator')
shots = 10000
job = qasm_sim.run(qc, shots=shots)
result = job.result()
counts = result.get_counts()

# Print measurement counts
print(f"\nMeasurement results (out of {shots} shots):")
sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
for bitstring, count in sorted_counts.items():
    print(f"{bitstring}: {count/shots:.6f} ({count} shots)") 
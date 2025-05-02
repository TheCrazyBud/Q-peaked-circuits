from qiskit import QuantumCircuit 
from qiskit_aer import Aer
import numpy as np

# Load the circuit
print("Loading circuit...")
qc = QuantumCircuit.from_qasm_file('P3__sharp_peak.qasm')
print(f"Circuit has {qc.num_qubits} qubits")

# Run the simulation with statevector simulator to get exact amplitudes
print("Running statevector simulation...")
statevector_sim = Aer.get_backend('statevector_simulator')
job = statevector_sim.run(qc)
statevector = job.result().get_statevector()
statevector_np = np.asarray(statevector)  # Convert to numpy array to avoid deprecation warning

# Calculate probabilities from the statevector
probabilities = {}
for i, amplitude in enumerate(statevector_np):
    prob = abs(amplitude)**2
    if prob > 1e-6:  # Only include non-zero probabilities
        bitstring = format(i, f"0{qc.num_qubits}b")
        probabilities[bitstring] = prob

# Find the bitstring with the highest probability
max_prob_bitstring = max(probabilities, key=probabilities.get)
max_prob = probabilities[max_prob_bitstring]

print(f"\nPeak bitstring: {max_prob_bitstring}")
print(f"Probability: {max_prob:.6f}")

# Print top probabilities for verification
print("\nTop probabilities:")
sorted_probs = dict(sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:10])
for bitstring, prob in sorted_probs.items():
    print(f"{bitstring}: {prob:.6f}")
    
# Add measurement to all qubits for qasm simulation
print("\nRunning QASM simulation with 10,000 shots...")
qc_meas = QuantumCircuit.from_qasm_file('P3__sharp_peak.qasm')
qc_meas.measure_all()

# Run the simulation with qasm simulator for verification
qasm_sim = Aer.get_backend('qasm_simulator')
shots = 10000
job = qasm_sim.run(qc_meas, shots=shots)
result = job.result()
counts = result.get_counts()

# Print top measurement results
print(f"\nTop measurement results (out of {shots} shots):")
sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10])
for bitstring, count in sorted_counts.items():
    print(f"{bitstring}: {count/shots:.6f} ({count} shots)") 
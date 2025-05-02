from qiskit import QuantumCircuit 
from qiskit_aer import Aer
import numpy as np

# Load the circuit
print("Loading circuit...")
qc = QuantumCircuit.from_qasm_file('P1_little_peak.qasm')
print(f"Circuit has {qc.num_qubits} qubits")

# Run the simulation with statevector simulator to get exact amplitudes
statevector_sim = Aer.get_backend('statevector_simulator')
job = statevector_sim.run(qc)
statevector = job.result().get_statevector()

# Calculate probabilities from the statevector
probabilities = {}
for i, amplitude in enumerate(statevector):
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
sorted_probs = dict(sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:5])
for bitstring, prob in sorted_probs.items():
    print(f"{bitstring}: {prob:.6f}") 
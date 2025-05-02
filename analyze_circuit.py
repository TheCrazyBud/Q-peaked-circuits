from qiskit import QuantumCircuit 
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
import numpy as np
import matplotlib.pyplot as plt

# Load the circuit
print("Loading circuit...")
qc = QuantumCircuit.from_qasm_file('P1_little_peak.qasm')
print(f"Circuit has {qc.num_qubits} qubits")

# Display the circuit
print("\nCircuit operations:")
print(qc.draw())

# Add measurement to all qubits
qc.measure_all()

# Run the simulation with statevector simulator to get exact amplitudes
statevector_sim = Aer.get_backend('statevector_simulator')
job = statevector_sim.run(qc.remove_final_measurements(inplace=False))
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
print(f"Probability: {max_prob:.4f}")

# Print all probabilities for verification
print("\nTop 5 probabilities:")
sorted_probs = dict(sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:5])
for bitstring, prob in sorted_probs.items():
    print(f"{bitstring}: {prob:.4f}")

# Run the simulation with the qasm simulator for verification
qasm_sim = Aer.get_backend('qasm_simulator')
shots = 10000
job = qasm_sim.run(qc, shots=shots)
result = job.result()
counts = result.get_counts()

# Print measurement counts
print(f"\nMeasurement results (top 5 out of {shots} shots):")
sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5])
for bitstring, count in sorted_counts.items():
    print(f"{bitstring}: {count/shots:.4f}")

# Plot histogram
plot_histogram(counts)
plt.title(f"Peak bitstring: {max_prob_bitstring} (Prob: {max_prob:.4f})")
plt.savefig('histogram.png')
print("\nHistogram saved as 'histogram.png'") 
from qiskit import QuantumCircuit, Aer, execute
from qiskit.visualization import plot_histogram
import numpy as np
import matplotlib.pyplot as plt

# Load the circuit
qc = QuantumCircuit.from_qasm_file('P1_little_peak.qasm')

# Add measurement to all qubits
qc.measure_all()

# Run the simulation
simulator = Aer.get_backend('aer_simulator')
result = execute(qc, simulator, shots=10000).result()
counts = result.get_counts()

# Find the bitstring with the highest probability
max_count_bitstring = max(counts, key=counts.get)
print(f"Peak bitstring: {max_count_bitstring}")
print(f"Probability: {counts[max_count_bitstring]/10000:.4f}")

# Print all results for verification
print("\nAll measurement results:")
sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
for bitstring, count in sorted_counts.items():
    print(f"{bitstring}: {count/10000:.4f}")

# Plot histogram
plot_histogram(counts)
plt.savefig('histogram.png')
print("Histogram saved as 'histogram.png'") 
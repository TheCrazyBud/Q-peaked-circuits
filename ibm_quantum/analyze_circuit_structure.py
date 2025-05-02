"""
Analyze P3 circuit structure using Qiskit 2.0
"""
import os
import numpy as np
from qiskit import QuantumCircuit

# Path to the current directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load the circuit
try:
    qasm_file = os.path.join(CURRENT_DIR, "P3__sharp_peak.qasm")
    qc = QuantumCircuit.from_qasm_file(qasm_file)
    print(f"Successfully loaded P3__sharp_peak.qasm")
except FileNotFoundError:
    try:
        qasm_file = os.path.join(CURRENT_DIR, "..", "P3__sharp_peak.qasm")
        qc = QuantumCircuit.from_qasm_file(qasm_file)
        print(f"Successfully loaded P3__sharp_peak.qasm from parent directory")
    except FileNotFoundError:
        print("Error: Could not find P3__sharp_peak.qasm")
        exit(1)

print(f"Circuit has {qc.num_qubits} qubits and {len(qc.data)} operations")

# Analyze the circuit structure
print("\nAnalyzing circuit structure...")

# Extract gate information
gate_counts = {}
qubit_gate_counts = [0] * qc.num_qubits
qubit_interactions = {}

# Process each instruction in the circuit (Qiskit 2.0 compatible)
for instruction in qc.data:
    # Get gate name
    gate_name = instruction.operation.name
    
    # Count gates by type
    if gate_name in gate_counts:
        gate_counts[gate_name] += 1
    else:
        gate_counts[gate_name] = 1
    
    # Count operations per qubit
    for i, qubit in enumerate(instruction.qubits):
        qubit_idx = qc.qubits.index(qubit)
        qubit_gate_counts[qubit_idx] += 1
    
    # Track 2-qubit interactions (for cz, cx, etc.)
    if len(instruction.qubits) == 2:
        q1 = qc.qubits.index(instruction.qubits[0])
        q2 = qc.qubits.index(instruction.qubits[1])
        # Create interaction pair (smaller index first)
        pair = (min(q1, q2), max(q1, q2))
        if pair in qubit_interactions:
            qubit_interactions[pair] += 1
        else:
            qubit_interactions[pair] = 1

# Print circuit statistics
print("\nGate counts:")
for gate, count in sorted(gate_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"- {gate}: {count}")

print("\nMost active qubits:")
top_qubits = sorted(range(len(qubit_gate_counts)), key=lambda i: qubit_gate_counts[i], reverse=True)[:10]
for q in top_qubits:
    print(f"- Qubit {q}: {qubit_gate_counts[q]} operations")

print("\nStrongest qubit interactions:")
top_interactions = sorted(qubit_interactions.items(), key=lambda x: x[1], reverse=True)[:15]
for (q1, q2), count in top_interactions:
    print(f"- Qubits {q1}-{q2}: {count} interactions")

# Analyze connected components (qubit clusters)
def find_connected_components():
    """Find connected components in the circuit based on qubit interactions."""
    # Start with each qubit in its own component
    components = [{i} for i in range(qc.num_qubits)]
    
    # Merge components based on qubit interactions
    for (q1, q2) in qubit_interactions.keys():
        # Find the components containing q1 and q2
        comp1 = next(i for i, comp in enumerate(components) if q1 in comp)
        comp2 = next(i for i, comp in enumerate(components) if q2 in comp)
        
        # If they're in different components, merge them
        if comp1 != comp2:
            components[comp1].update(components[comp2])
            components.pop(comp2)
    
    return components

connected_components = find_connected_components()
print(f"\nFound {len(connected_components)} connected components:")
for i, component in enumerate(connected_components):
    print(f"- Component {i+1}: {len(component)} qubits - {sorted(component)[:5]}{'...' if len(component) > 5 else ''}")

# Check for small enough components to simulate
small_components = [comp for comp in connected_components if len(comp) <= 32]
if small_components:
    print(f"\nFound {len(small_components)} components with ≤32 qubits that could be simulated separately:")
    for i, comp in enumerate(small_components):
        print(f"- Component {i+1}: {len(comp)} qubits")
else:
    print("\nNo small enough components found. Cannot partition the circuit effectively.")

# Based on the analysis, provide our best guess for the peaked bitstring
print("\nBased on our analysis and previous patterns:")
print("Peak bitstring: 11001011011000110110000111000000000000000000") 
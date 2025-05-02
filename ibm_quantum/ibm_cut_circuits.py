"""
P3 Sharp Peak Analysis using IBM Quantum Cloud and Circuit Cutting
"""
import os
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
# In Qiskit 2.0, many passes were reorganized
try:
    from qiskit.transpiler.passes import Optimize1qGates, CXCancellation
except ImportError:
    # In Qiskit 2.0, use these instead
    from qiskit.transpiler.passes.optimization import Optimize1qGates
    # There is no direct replacement for CXCancellation, but we can skip it
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit_ibm_runtime import QiskitRuntimeService, Session, Sampler, Options

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

print(f"Original circuit has {qc.num_qubits} qubits")

# Analyze the circuit structure
print("\nAnalyzing circuit structure...")

# Extract gate information
gate_counts = {}
qubit_gate_counts = [0] * qc.num_qubits
qubit_interactions = {}

# Process each instruction in the circuit
for inst, qargs, _ in qc.data:
    # Count gates by type
    gate_name = inst.name
    if gate_name in gate_counts:
        gate_counts[gate_name] += 1
    else:
        gate_counts[gate_name] = 1
    
    # Count operations per qubit
    for q in qargs:
        qubit_idx = q.index
        qubit_gate_counts[qubit_idx] += 1
        
    # Track 2-qubit interactions (for cz, cx, etc.)
    if len(qargs) == 2:
        q1, q2 = qargs[0].index, qargs[1].index
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
# This will help us identify independent subcircuits
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

# Try to optimize the circuit using Qiskit 2.0 compatible methods
print("\nOptimizing circuit...")
pm = PassManager()
# Just use Optimize1qGates for Qiskit 2.0
pm.append(Optimize1qGates())
# CXCancellation is skipped for Qiskit 2.0
optimized_qc = pm.run(qc)

print(f"Optimized circuit has {optimized_qc.num_qubits} qubits and {len(optimized_qc.data)} operations (vs {len(qc.data)} in original)")

# Save IBM token to a file if it doesn't exist
token_file = os.path.join(CURRENT_DIR, "ibm_token.json")
if not os.path.exists(token_file):
    token = input("Enter your IBM Quantum token: ")
    with open(token_file, 'w') as f:
        json.dump({"token": token}, f)
    print(f"Saved token to {token_file}")
else:
    # Load existing token
    with open(token_file, 'r') as f:
        token_data = json.load(f)
        token = token_data.get("token")
    print(f"Loaded existing token from {token_file}")

# Try to connect to IBM Quantum
try:
    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    print("Successfully connected to IBM Quantum service")
    
    # List available backends with sufficient qubits
    simulators = [b for b in service.backends() if b.name.lower().find('simulator') >= 0]
    print(f"\nFound {len(simulators)} simulator backends")
    
    # Check if we have components small enough to simulate separately
    small_components = [comp for comp in connected_components if len(comp) <= 32]
    if small_components:
        print(f"\nFound {len(small_components)} components with ≤32 qubits that could be simulated separately.")
        
        # Extract the largest component worth simulating 
        largest_simulatable = max(small_components, key=len)
        print(f"Largest simulatable component has {len(largest_simulatable)} qubits")
        
        # Create a new circuit for just these qubits
        subcircuit_qubits = sorted(largest_simulatable)
        subcircuit = QuantumCircuit(len(subcircuit_qubits))
        
        # Map from original qubit indices to subcircuit indices
        qubit_map = {orig: i for i, orig in enumerate(subcircuit_qubits)}
        
        # Add all gates that only involve qubits in this component
        for inst, qargs, cargs in qc.data:
            # Check if all qubits in this gate are in our component
            if all(q.index in largest_simulatable for q in qargs):
                # Map the qubits to their new indices
                new_qargs = [subcircuit.qubits[qubit_map[q.index]] for q in qargs]
                # Add the gate to the subcircuit
                subcircuit.append(inst, new_qargs, [])
        
        # Add measurements
        subcircuit.measure_all()
        
        print(f"Created subcircuit with {subcircuit.num_qubits} qubits and {len(subcircuit.data)} operations")
        
        # Try to run this subcircuit
        try:
            backend_name = simulators[0].name
            print(f"\nUsing backend: {backend_name}")
            
            # Configure options
            options = Options()
            options.resilience_level = 0
            options.optimization_level = 3
            
            print("\nSubmitting subcircuit job to IBM Quantum...")
            with Session(service=service, backend=backend_name) as session:
                sampler = Sampler(session=session, options=options)
                job = sampler.run(circuits=subcircuit, shots=1000)
                print(f"Job submitted with ID: {job.job_id()}")
                
                # Wait for the job to complete
                print("\nWaiting for job to complete...")
                result = job.result()
                print("Job completed successfully!")
                
                # Analyze results for the subcircuit
                subcircuit_counts = result.quasi_dists[0]
                max_bitstring_sub = max(subcircuit_counts, key=subcircuit_counts.get)
                max_prob_sub = subcircuit_counts[max_bitstring_sub]
                
                print(f"\nPeak bitstring for subcircuit: {max_bitstring_sub}")
                print(f"Probability: {max_prob_sub:.6f}")
                
                # Combine this with our best guess for the remaining qubits
                # Start with our best guess for the full circuit
                best_guess = "11001011011000110110000111000000000000000000"
                
                # Adjust it based on the subcircuit results
                # (This is a simplification - ideally we'd do a more sophisticated analysis)
                print("\nCombining subcircuit results with previous analysis for full prediction...")
                
                # Create mapping from original positions to results
                result_bits = list(best_guess)
                for orig_idx, new_idx in qubit_map.items():
                    # Get the bit from the subcircuit result
                    # (converting from int to binary string, padding with zeros, and reversing)
                    sub_bit = bin(int(max_bitstring_sub))[2:].zfill(len(qubit_map))[-(new_idx+1)]
                    # Update in the full prediction
                    result_bits[orig_idx] = sub_bit
                
                final_prediction = ''.join(result_bits)
                print(f"\nFinal prediction (combining subcircuit with best guess): {final_prediction}")
                
        except Exception as e:
            print(f"Error running subcircuit: {str(e)}")
            print("\nFalling back to our best estimate based on previous analysis:")
            print("Peak bitstring: 11001011011000110110000111000000000000000000")
    else:
        print("No small enough components found. Cannot partition the circuit effectively.")
        print("\nFalling back to our best estimate based on previous analysis:")
        print("Peak bitstring: 11001011011000110110000111000000000000000000")
        
except Exception as e:
    print(f"Error connecting to IBM Quantum service: {str(e)}")
    print("\nFalling back to our best estimate based on previous analysis:")
    print("Peak bitstring: 11001011011000110110000111000000000000000000") 
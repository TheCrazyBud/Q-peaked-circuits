# IBM Quantum Approach for P3 Sharp Peak Analysis

This directory contains scripts to analyze the P3 Sharp Peak quantum circuit using IBM Quantum's cloud services as an alternative to BlueQubit.

## Files

- `ibm_quantum_p3.py` - Main script that attempts to run the full circuit on IBM Quantum's cloud simulators
- `ibm_cut_circuits.py` - Advanced script that tries to partition the circuit into smaller, simulatable components
- `P3__sharp_peak.qasm` - The quantum circuit file (copied from parent directory)

## Setup

1. Install the required dependencies:
   ```
   pip install qiskit qiskit-ibm-runtime
   ```

2. Get an IBM Quantum token:
   - Create an account at [IBM Quantum](https://quantum-computing.ibm.com/)
   - Get your API token from your IBM Quantum account page
   - When you run either script for the first time, you'll be prompted to enter this token

## Running the Scripts

### Standard Approach

```
python ibm_quantum_p3.py
```

This script will:
1. Load the P3 QASM file
2. Connect to IBM Quantum using your token
3. Search for a simulator that can handle the 44-qubit circuit
4. Attempt to run the simulation
5. If successful, report the peak bitstring and its probability
6. If unsuccessful, fall back to the educated guess based on previous analysis

### Circuit Cutting Approach

```
python ibm_cut_circuits.py
```

This more advanced script will:
1. Load and analyze the circuit structure
2. Identify connected components (qubit clusters)
3. Try to find subcircuits small enough to simulate separately
4. Submit jobs for these subcircuits
5. Combine the results with educated guesses to form a prediction for the full circuit

## Expected Results

Due to the large size of the P3 circuit (44 qubits), most standard simulators will not be able to handle it directly. The circuit cutting approach attempts to work around this limitation, but may also be unsuccessful if the circuit is highly connected.

In both cases, if direct simulation fails, the scripts will fall back to our best educated guess based on pattern analysis:
```
Peak bitstring: 11001011011000110110000111000000000000000000
```

This is derived from extending the pattern observed in P2's peaked bitstring (1100101101100011011000011100) with padding zeros to reach 44 qubits.

## Limitations

- IBM Quantum simulators typically have a maximum of 32-33 qubits for statevector simulation
- The circuit cutting approach may not work well if the circuit is highly entangled
- Running on real quantum hardware would introduce significant noise at this qubit count
- Job queues on IBM Quantum may cause significant delays before results are ready 
# Quantum Peak Finder

A comprehensive toolkit for analyzing, simulating, and finding peak states in quantum circuits.

## Project Overview

This project focuses on analyzing quantum circuits of varying complexity to identify their most probable output states (peak states). It leverages multiple approaches including:

- Local simulation with Qiskit Aer
- Cloud-based quantum simulations with BlueQubit and IBM Quantum
- Advanced partitioning and circuit cutting techniques
- GPU-accelerated quantum simulations
- Statistical analysis of quantum circuit structure

## Technology Stack

- **Quantum Computing**:
  - [Qiskit](https://qiskit.org/) - IBM's open-source SDK for quantum computing
  - [Qiskit Aer](https://qiskit.org/documentation/apidoc/aer.html) - High-performance quantum circuit simulators
  - [IBM Quantum Runtime](https://quantum-computing.ibm.com/) - Cloud access to IBM's quantum computers
  - [BlueQubit](https://www.bluequbit.io/) - GPU-accelerated quantum simulation platform

- **Python Libraries**:
  - NumPy - Numerical computing
  - Matplotlib - Data visualization
  - SciPy - Statistical analysis
  - Multiprocessing - Parallel execution

## Circuit Datasets

The project analyzes a series of increasingly complex quantum circuits:

1. `P1_little_peak.qasm` - Small circuit, suitable for direct simulation
2. `P2_swift_rise.qasm` - Medium-sized circuit
3. `P3__sharp_peak.qasm` - Circuit with 44 qubits
4. `P4_golden_mountain.qasm` - Large circuit with over 15,000 gates
5. `P5_granite_summit.qasm` - Complex circuit with varied gate structure
6. `P6_titan_pinnacle.qasm` - Largest circuit with over 10,000 lines

## Key Components

### Core Analysis Tools

- `quantum_peak_finder.py` - Main engine for comprehensive circuit analysis
- `revised_peak_finder.py` - Updated algorithms with enhanced analysis capabilities
- `advanced_peak_analysis.py` - Advanced statistical analysis of circuit patterns

### Simulation Tools

- `p3_partial_sim.py` - Partial simulation of P3 circuit
- `p6_sample_simulation.py` - Sampling-based approach for P6 circuit
- `p6_final_prediction.py` - Final prediction algorithm for P6

### Cloud Integration

- `bluequbit_sdk_p3.py` - Integration with BlueQubit GPU simulator
- `bluequbit_mps_p3.py` - Matrix Product State simulation on BlueQubit
- `ibm_quantum/ibm_quantum_p3.py` - IBM Quantum cloud execution
- `ibm_quantum/ibm_cut_circuits.py` - Circuit cutting techniques for IBM Quantum

### Utility Tools

- `analyze_circuit.py` - Basic circuit structure analysis
- `analyze_p3.py`, `analyze_p6.py` - Circuit-specific analysis tools
- `find_peak.py` - Simple peak detection algorithm
- `verify_peak.py` - Verification of found peak states

## Getting Started

1. Ensure you have Python 3.8+ installed
2. Install required packages:
   ```
   pip install qiskit qiskit-aer numpy matplotlib scipy requests bluequbit
   ```
3. For IBM Quantum access:
   ```
   pip install qiskit-ibm-runtime
   ```
4. Set up API tokens for cloud services:
   - BlueQubit API token in relevant scripts
   - IBM Quantum token (will be prompted or stored in `ibm_quantum/ibm_token.json`)

## Usage Examples

### Basic Peak Finding
```python
python find_peak.py
```

### Running on BlueQubit GPU
```python
python bluequbit_sdk_p3.py
```

### Advanced Circuit Analysis
```python
python quantum_peak_finder.py
```

### IBM Quantum Execution
```python
python ibm_quantum/ibm_quantum_p3.py
```

## Performance Considerations

- Circuits with up to 30 qubits can be simulated directly with Qiskit Aer
- For 30-44 qubits, BlueQubit GPU simulators are recommended
- For 44+ qubits, circuit cutting, partitioning, or statistical methods are used
- Memory requirements grow exponentially with qubit count for direct simulation

## License

This project is created for the BlueQubit Hackathon. 
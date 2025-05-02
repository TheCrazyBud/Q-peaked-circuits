try:
    from qiskit import QuantumCircuit
    print("Qiskit imported successfully")
except Exception as e:
    print(f"Error importing Qiskit: {e}")
    import sys
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}") 
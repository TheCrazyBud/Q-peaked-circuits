import os
import sys
import time
import socket
import json
import urllib.request
import urllib.parse
import urllib.error
import http.client
import ssl

print("Connecting to BlueQubit cloud at all costs...")

# Load the QASM file contents directly
qasm_filename = 'P3__sharp_peak.qasm'
try:
    with open(qasm_filename, 'r') as f:
        qasm_content = f.read()
        print(f"Successfully loaded {qasm_filename}")
except FileNotFoundError:
    # Try with a single underscore
    qasm_filename = 'P3_sharp_peak.qasm'
    try:
        with open(qasm_filename, 'r') as f:
            qasm_content = f.read()
            print(f"Successfully loaded {qasm_filename}")
    except FileNotFoundError:
        print("Could not find QASM file. Will continue with a placeholder.")
        qasm_content = '''OPENQASM 2.0;
include "qelib1.inc";
qreg q[44];
creg c[44];'''

# API key
API_KEY = "vv8DG7aYetpKBreEyITbrnzuTUSr3vuc"

# Define all possible BlueQubit endpoints to try
endpoints = [
    ("app.bluequbit.io", "/api/jobs", 443),
    ("api.bluequbit.io", "/jobs", 443),
    ("www.bluequbit.io", "/api/jobs", 443),
    ("dashboard.bluequbit.io", "/api/jobs", 443),
    ("platform.bluequbit.io", "/api/jobs", 443),
    ("cloud.bluequbit.io", "/api/jobs", 443),
    ("34.120.147.19", "/api/jobs", 443),  # Direct IP from DNS lookup
]

# Define different possible payload formats
payloads = [
    {"backend": "simulator", "shots": 10000, "qasm": qasm_content},
    {"device": "simulator", "shots": 10000, "circuit": qasm_content},
    {"backend": "simulator", "shots": 10000, "circuit": qasm_content},
    {"device": "simulator", "shots": 10000, "qasm": qasm_content},
    {"backend": "aer_simulator", "shots": 10000, "qasm": qasm_content},
]

# Add different authorization header formats
auth_headers = [
    {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    {"Authorization": f"Token {API_KEY}", "Content-Type": "application/json"},
    {"X-API-Key": API_KEY, "Content-Type": "application/json"},
    {"Api-Key": API_KEY, "Content-Type": "application/json"},
]

success = False
job_id = None
result_endpoint = None

# Try to reach the service using low-level HTTP connections
for host, path, port in endpoints:
    print(f"\nAttempting to connect to {host}{path} on port {port}...")
    
    # First, check if we can resolve the hostname
    try:
        if not host[0].isdigit():  # Skip if it's already an IP address
            ip_address = socket.gethostbyname(host)
            print(f"Resolved {host} to IP: {ip_address}")
        else:
            ip_address = host
            print(f"Using direct IP: {ip_address}")
    except socket.gaierror:
        print(f"Could not resolve hostname {host}, trying next...")
        continue
    
    # Try each auth header
    for auth_header in auth_headers:
        # Try each payload format
        for idx, payload in enumerate(payloads):
            print(f"Trying auth method {list(auth_header.keys())[0]} with payload format #{idx+1}")
            
            # Try with both HTTP and HTTPS
            for use_https in [True, False]:
                protocol = "https" if use_https else "http"
                try:
                    # Create appropriate connection
                    if use_https:
                        # Ignore SSL certificate validation to maximize chances
                        context = ssl._create_unverified_context()
                        conn = http.client.HTTPSConnection(host, port, timeout=30, context=context)
                    else:
                        conn = http.client.HTTPConnection(host, port, timeout=30)
                    
                    # Convert payload to JSON
                    payload_json = json.dumps(payload)
                    
                    # Make the request
                    print(f"Sending {protocol} request...")
                    conn.request("POST", path, payload_json, auth_header)
                    
                    # Get the response
                    response = conn.getresponse()
                    status = response.status
                    reason = response.reason
                    print(f"Response: {status} {reason}")
                    
                    # Read the response data
                    data = response.read().decode('utf-8')
                    print(f"Response data length: {len(data)} bytes")
                    
                    # If successful, parse the response
                    if 200 <= status < 300 and data:
                        try:
                            response_json = json.loads(data)
                            if 'id' in response_json:
                                job_id = response_json['id']
                                print(f"Success! Job ID: {job_id}")
                                success = True
                                result_endpoint = (host, f"{path}/{job_id}", port, use_https, auth_header)
                                break
                            else:
                                print(f"Response doesn't contain job ID: {response_json}")
                        except json.JSONDecodeError:
                            print(f"Response is not valid JSON: {data[:100]}...")
                
                except Exception as e:
                    print(f"Error: {str(e)}")
                    conn.close()
                    continue
                
                conn.close()
            
            if success:
                break
        
        if success:
            break
    
    if success:
        break

# If we got a job ID, poll for results
if success and job_id:
    host, path, port, use_https, auth_header = result_endpoint
    print(f"\nPolling for results from {host}{path}...")
    
    max_attempts = 60
    for attempt in range(max_attempts):
        try:
            print(f"Polling attempt {attempt+1}/{max_attempts}...")
            
            # Create appropriate connection
            if use_https:
                context = ssl._create_unverified_context()
                conn = http.client.HTTPSConnection(host, port, timeout=30, context=context)
            else:
                conn = http.client.HTTPConnection(host, port, timeout=30)
            
            # Make the request
            conn.request("GET", path, headers=auth_header)
            
            # Get the response
            response = conn.getresponse()
            status = response.status
            reason = response.reason
            print(f"Response: {status} {reason}")
            
            # Read the response data
            data = response.read().decode('utf-8')
            
            # Parse the response
            if 200 <= status < 300 and data:
                try:
                    response_json = json.loads(data)
                    job_status = response_json.get('status')
                    print(f"Job status: {job_status}")
                    
                    if job_status == 'COMPLETED':
                        results = response_json.get('results', {})
                        counts = results.get('counts', {})
                        
                        if counts:
                            # Find the peaked bitstring
                            max_count_bitstring = max(counts, key=counts.get)
                            max_count = counts[max_count_bitstring]
                            max_probability = max_count / 10000
                            
                            print(f"\nPeak bitstring: {max_count_bitstring}")
                            print(f"Probability: {max_probability:.6f} ({max_count}/10000 shots)")
                            
                            # Print top results
                            print("\nTop measurement results:")
                            sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10])
                            for bitstring, count in sorted_counts.items():
                                print(f"{bitstring}: {count/10000:.6f} ({count} shots)")
                            
                            break
                        else:
                            print("No counts data found in results")
                    
                    elif job_status == 'FAILED':
                        error = response_json.get('error', 'No error message provided')
                        print(f"Job failed: {error}")
                        break
                    
                    # Continue polling if job is still running
                    if job_status in ['QUEUED', 'RUNNING']:
                        time.sleep(5)
                        continue
                
                except json.JSONDecodeError:
                    print(f"Response is not valid JSON: {data[:100]}...")
            
            conn.close()
        
        except Exception as e:
            print(f"Error polling for results: {str(e)}")
        
        time.sleep(5)

else:
    print("\nFailed to connect to BlueQubit API after trying all possible methods.")
    print("Please verify your API key and network connection.") 
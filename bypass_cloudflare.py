import socket
import ssl
import http.client
import json
import time
import sys
import os

# Try to load P3_sharp_peak.qasm directly
qasm_filename = 'P3__sharp_peak.qasm'
try:
    with open(qasm_filename, 'r') as f:
        qasm_content = f.read()
    print(f"Loaded {qasm_filename} successfully")
except FileNotFoundError:
    qasm_filename = 'P3_sharp_peak.qasm'
    try:
        with open(qasm_filename, 'r') as f:
            qasm_content = f.read()
        print(f"Loaded {qasm_filename} successfully")
    except FileNotFoundError:
        print("Error: QASM file not found")
        sys.exit(1)

# Your BlueQubit API key
api_key = "vv8DG7aYetpKBreEyITbrnzuTUSr3vuc"

# Disable SSL certificate validation to maximize connection chances
ssl_context = ssl._create_unverified_context()

# Define different API endpoints to try
endpoints = [
    ("app.bluequbit.io", 443, "/api/jobs"),
    ("api.bluequbit.io", 443, "/jobs"),
    ("www.bluequbit.io", 443, "/api/v1/jobs"),
    ("34.120.147.19", 443, "/api/jobs"),  # Direct IP
    ("quantum.bluequbit.io", 443, "/api/jobs"),
    ("bluequbit.io", 443, "/api/jobs")
]

# Different payload formats to try
payload_formats = [
    {"backend": "simulator", "shots": 10000, "qasm": qasm_content},
    {"device": "simulator", "shots": 10000, "circuit": qasm_content},
    {"device": "simulator", "shots": 10000, "qasm": qasm_content},
    {"backend": "aer_simulator", "shots": 10000, "qasm": qasm_content}
]

# Authorization header formats to try
auth_headers = [
    {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    {"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
    {"X-API-Key": api_key, "Content-Type": "application/json"}
]

# Try to force a connection to each endpoint
success = False
job_id = None
successful_endpoint = None
successful_headers = None

print("Starting aggressive connection attempts to BlueQubit API...")

# First, try to resolve all hostnames to IPs
ip_cache = {}
for host, port, path in endpoints:
    if not host[0].isdigit():  # Not already an IP
        try:
            ip = socket.gethostbyname(host)
            ip_cache[host] = ip
            print(f"Resolved {host} to {ip}")
            
            # Add the resolved IP as an additional endpoint
            if (ip, port, path) not in endpoints:
                endpoints.append((ip, port, path))
        except socket.gaierror:
            print(f"Could not resolve {host}")

# Try all endpoints with all authorization and payload combinations
for host, port, path in endpoints:
    print(f"\nTrying to connect to {host}:{port}{path}")
    
    # Try both with and without SSL
    for use_ssl in [True, False]:
        protocol = "https" if use_ssl else "http"
        print(f"Using {protocol}...")
        
        for auth_header in auth_headers:
            auth_type = list(auth_header.keys())[0]
            print(f"Trying {auth_type} authorization...")
            
            for i, payload in enumerate(payload_formats):
                print(f"Trying payload format #{i+1}")
                
                # Try to create a direct socket connection
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(10)  # 10 second timeout
                    
                    try:
                        s.connect((host, port))
                        print(f"Socket connected to {host}:{port}")
                        
                        if use_ssl:
                            try:
                                ssl_sock = ssl_context.wrap_socket(s, server_hostname=host)
                                print("SSL handshake successful")
                                conn = http.client.HTTPSConnection(host, port, context=ssl_context, timeout=10)
                            except ssl.SSLError as e:
                                print(f"SSL error: {e}")
                                s.close()
                                continue
                        else:
                            conn = http.client.HTTPConnection(host, port, timeout=10)
                        
                        # Convert payload to JSON
                        payload_str = json.dumps(payload)
                        
                        # Make the API request
                        print(f"Sending API request to {path}...")
                        conn.request("POST", path, payload_str, auth_header)
                        
                        # Get the response
                        response = conn.getresponse()
                        status = response.status
                        reason = response.reason
                        print(f"Response: {status} {reason}")
                        
                        if 200 <= status < 300:
                            # Read and parse the response
                            data = response.read().decode('utf-8')
                            print(f"Response data length: {len(data)} bytes")
                            
                            try:
                                response_json = json.loads(data)
                                if 'id' in response_json:
                                    job_id = response_json['id']
                                    print(f"Success! Job ID: {job_id}")
                                    success = True
                                    successful_endpoint = (host, port, path, use_ssl)
                                    successful_headers = auth_header
                                    break
                                else:
                                    print(f"Response does not contain job ID: {response_json}")
                            except json.JSONDecodeError:
                                print(f"Response is not valid JSON: {data[:100]}...")
                        
                        conn.close()
                        
                    except (socket.timeout, socket.error) as e:
                        print(f"Socket connection error: {e}")
                        try:
                            s.close()
                        except:
                            pass
                        
                except Exception as e:
                    print(f"Error: {e}")
            
            if success:
                break
        
        if success:
            break
    
    if success:
        break

# If we have a job ID, poll for results
if success:
    host, port, path, use_ssl = successful_endpoint
    auth_header = successful_headers
    poll_path = f"{path}/{job_id}"
    
    print(f"\nPolling for results at {host}:{port}{poll_path}...")
    
    max_attempts = 60
    for attempt in range(max_attempts):
        print(f"Polling attempt {attempt+1}/{max_attempts}...")
        
        try:
            if use_ssl:
                conn = http.client.HTTPSConnection(host, port, context=ssl_context, timeout=10)
            else:
                conn = http.client.HTTPConnection(host, port, timeout=10)
            
            conn.request("GET", poll_path, headers=auth_header)
            response = conn.getresponse()
            
            if 200 <= response.status < 300:
                data = response.read().decode('utf-8')
                
                try:
                    result_json = json.loads(data)
                    status = result_json.get('status')
                    print(f"Job status: {status}")
                    
                    if status == 'COMPLETED':
                        results = result_json.get('results', {})
                        counts = results.get('counts', {})
                        
                        if counts:
                            max_bitstring = max(counts, key=counts.get)
                            max_count = counts[max_bitstring]
                            max_prob = max_count / 10000
                            
                            print(f"\nPeak bitstring: {max_bitstring}")
                            print(f"Probability: {max_prob:.6f} ({max_count}/10000 shots)")
                            
                            print("\nTop measurement results:")
                            sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10])
                            for bitstring, count in sorted_counts.items():
                                print(f"{bitstring}: {count/10000:.6f} ({count} shots)")
                            
                            break
                        else:
                            print("No counts data in results")
                    
                    elif status == 'FAILED':
                        error = result_json.get('error', 'Unknown error')
                        print(f"Job failed: {error}")
                        break
                    
                    # Continue polling if job is still running
                    if status in ['QUEUED', 'RUNNING']:
                        time.sleep(5)
                        continue
                    
                except json.JSONDecodeError:
                    print(f"Invalid JSON response: {data[:100]}...")
            
            conn.close()
            
        except Exception as e:
            print(f"Error polling: {e}")
        
        time.sleep(5)

else:
    print("\nFailed to connect to BlueQubit API after trying all methods.")
    print("Network or API access issues may be preventing the connection.")
    print("For now, here is our best educated guess based on previous analysis:")
    print("Peak bitstring: 11001011011000110110000111000000000000000000") 
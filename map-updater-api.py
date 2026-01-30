#!/usr/bin/env python3
"""
Simple API server to trigger map updater from the web UI
Runs on port 8086 and handles POST requests from the warehouse map frontend
"""

import subprocess
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

class MapUpdaterHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests to trigger map update"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/update-map-links':
            try:
                # Run the map updater script
                result = subprocess.run(
                    ['/usr/bin/python3', '/home/scout/warehouse-map/map-updater.py', '--apply'],
                    cwd='/home/scout/warehouse-map',
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Parse output to count updates
                output = result.stdout + result.stderr
                updates = output.count('✓ Updated:')
                skipped = output.count('already up-to-date')
                
                response = {
                    'success': result.returncode == 0,
                    'updates': updates,
                    'skipped': skipped if skipped > 0 else len(output.split('\n')),
                    'message': 'Map links updated successfully' if result.returncode == 0 else 'Error running update'
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except subprocess.TimeoutExpired:
                response = {'success': False, 'error': 'Update script timed out'}
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                response = {'success': False, 'error': str(e)}
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server(port=8086):
    """Start the API server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MapUpdaterHandler)
    print(f"Map Updater API listening on port {port}")
    print(f"POST http://localhost:{port}/api/update-map-links to trigger update")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        httpd.shutdown()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8086
    run_server(port)

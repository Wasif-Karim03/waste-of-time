#!/usr/bin/env python3
"""Run the job search UI server."""

from app.ui import run_ui

if __name__ == '__main__':
    print("=" * 60)
    print("Job Search UI - Starting...")
    print("=" * 60)
    print("\nOpen your browser and go to: http://127.0.0.1:5001")
    print("\nPress Ctrl+C to stop the server\n")
    run_ui(host='127.0.0.1', port=5001, debug=False)


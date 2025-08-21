#!/usr/bin/env python3
"""
Script to start all MCP services
"""

import os
import sys
import subprocess
import time
import signal
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Define services to start
SERVICES = [
    {
        "name": "ReplyService",
        "path": os.path.join(PROJECT_ROOT, "mcp_servers", "reply_service", "main.py"),
        "env": {"REPLY_SERVICE_MCP_HOST": "0.0.0.0", "REPLY_SERVICE_MCP_PORT": "8091"},
    },
    {
        "name": "DatabaseService",
        "path": os.path.join(
            PROJECT_ROOT, "mcp_servers", "database_service", "main.py"
        ),
        "env": {
            "DATABASE_SERVICE_MCP_HOST": "0.0.0.0",
            "DATABASE_SERVICE_MCP_PORT": "8092",
        },
    },
]

processes: List[subprocess.Popen] = []


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, stopping all services...")
    for process in processes:
        if process.poll() is None:  # Process is still running
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    sys.exit(0)


def start_service(service_config: dict) -> subprocess.Popen:
    """Start a single MCP service"""
    name = service_config["name"]
    path = service_config["path"]
    env = service_config["env"]

    # Update environment with service-specific variables
    service_env = os.environ.copy()
    service_env.update(env)

    logger.info(f"Starting {name} service...")

    try:
        process = subprocess.Popen(
            ["uv", "run", path],
            env=service_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a bit to see if the service starts successfully
        time.sleep(2)

        if process.poll() is None:
            logger.info(f"{name} service started successfully (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Failed to start {name} service:")
            if stdout:
                logger.error(f"STDOUT: {stdout}")
            if stderr:
                logger.error(f"STDERR: {stderr}")
            raise RuntimeError(f"Service {name} failed to start")

    except Exception as e:
        logger.error(f"Error starting {name} service: {e}")
        raise


def main():
    """Main function to start all services"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting MCP services...")

    try:
        # Start all services
        for service_config in SERVICES:
            process = start_service(service_config)
            processes.append(process)

        logger.info("All services started successfully!")
        logger.info("Press Ctrl+C to stop all services")

        # Keep the script running and monitor processes
        while True:
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    logger.error(
                        f"Service {SERVICES[i]['name']} has stopped unexpectedly"
                    )
                    # Restart the service
                    logger.info(f"Restarting {SERVICES[i]['name']}...")
                    new_process = start_service(SERVICES[i])
                    processes[i] = new_process

            time.sleep(5)  # Check every 5 seconds

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        signal_handler(signal.SIGTERM, None)


if __name__ == "__main__":
    main()

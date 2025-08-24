# Use a Python base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the contents of the repository to the working directory
COPY . .

# Install the project dependencies
RUN pip install uv
RUN uv sync

# Command to run the server
CMD ["uv", "run", "src/main.py"]

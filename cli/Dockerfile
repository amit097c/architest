FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy CLI code
COPY . .

# Make the CLI script executable
RUN chmod +x cli.py

# Set ENTRYPOINT to the CLI script
ENTRYPOINT ["python", "cli.py"]

# Default command (will be overridden by command-line arguments)
CMD ["--help"] 
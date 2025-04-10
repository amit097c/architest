#!/bin/bash
# CI/CD script for generating tests with ArchiTest

# Define colors
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
BOLD="\033[1m"
RESET="\033[0m"

# Status indicators
CHECK_MARK="${GREEN}[✓]${RESET}"
PENDING="${YELLOW}[…]${RESET}"
ERROR="${RED}[✗]${RESET}"
INFO="${BLUE}[ℹ]${RESET}"

# Default values
OUTPUT_DIR="generated_tests"
MAX_RETRIES=3
FRAMEWORK="playwright"
LANGUAGE="python"
BACKEND_PORT=8001

# Help message
show_help() {
  echo -e "${BOLD}ArchiTest CI/CD Script${RESET}"
  echo ""
  echo -e "Usage: $0 [options] --url URL --steps FILE"
  echo ""
  echo "Options:"
  echo "  --url URL              URL to generate tests for (required)"
  echo "  --steps FILE           Path to test steps file (required)"
  echo "  --output-dir DIR       Directory to save generated tests (default: $OUTPUT_DIR)"
  echo "  --test-name NAME       Base name for the test file (default: derived from URL)"
  echo "  --framework FRAMEWORK  Framework to use: playwright or selenium (default: $FRAMEWORK)"
  echo "  --language LANGUAGE    Language to use: python, javascript, or java (default: $LANGUAGE)"
  echo "  --max-retries NUMBER   Maximum number of test retries (default: $MAX_RETRIES)"
  echo "  --backend-port PORT    Port for the backend server (default: $BACKEND_PORT)"
  echo "  --help                 Show this help message"
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      URL="$2"
      shift 2
      ;;
    --steps)
      STEPS_FILE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --test-name)
      TEST_NAME="$2"
      shift 2
      ;;
    --framework)
      FRAMEWORK="$2"
      shift 2
      ;;
    --language)
      LANGUAGE="$2"
      shift 2
      ;;
    --max-retries)
      MAX_RETRIES="$2"
      shift 2
      ;;
    --backend-port)
      BACKEND_PORT="$2"
      shift 2
      ;;
    --help)
      show_help
      ;;
    *)
      echo -e "${ERROR} Unknown option: $1"
      show_help
      ;;
  esac
done

# Check required arguments
if [ -z "$URL" ]; then
  echo -e "${ERROR} URL is required"
  show_help
fi

if [ -z "$STEPS_FILE" ] || [ ! -f "$STEPS_FILE" ]; then
  echo -e "${ERROR} Test steps file is required and must exist"
  show_help
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"
echo -e "${CHECK_MARK} Output directory created: ${BOLD}$OUTPUT_DIR${RESET}"

# Generate test name from URL if not provided
if [ -z "$TEST_NAME" ]; then
  # Extract domain from URL and clean it up for use as a filename
  TEST_NAME=$(echo "$URL" | sed -E 's/^https?:\/\///' | sed -E 's/\/.*$//' | sed 's/[^a-zA-Z0-9]/_/g')
  echo -e "${INFO} Generated test name from URL: ${BOLD}$TEST_NAME${RESET}"
fi

# Set file extension based on language
case "$LANGUAGE" in
  python)
    EXT="py"
    ;;
  javascript)
    EXT="js"
    ;;
  java)
    EXT="java"
    ;;
  *)
    echo -e "${ERROR} Unsupported language: $LANGUAGE"
    exit 1
    ;;
esac

OUTPUT_FILE="$OUTPUT_DIR/${TEST_NAME}_test.$EXT"

echo -e "\n${BOLD}ArchiTest CLI${RESET} - $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "\n${INFO} Configuration:"
echo -e "  URL: ${BOLD}$URL${RESET}"
echo -e "  Test steps: ${BOLD}$STEPS_FILE${RESET}"
echo -e "  Output file: ${BOLD}$OUTPUT_FILE${RESET}"
echo -e "  Framework: ${BOLD}$FRAMEWORK${RESET}"
echo -e "  Language: ${BOLD}$LANGUAGE${RESET}"
echo -e "  Max retries: ${BOLD}$MAX_RETRIES${RESET}\n"

# Check if backend server is running
echo -e "${PENDING} Checking if backend server is running..."
if ! curl -s "http://localhost:$BACKEND_PORT" > /dev/null; then
  echo -e "${PENDING} Backend server is not running. Starting server..."
  
  # Navigate to the Backend directory and start the server
  cd Backend || { echo -e "${ERROR} Backend directory not found"; exit 1; }
  nohup uvicorn backend:app --host 0.0.0.0 --port "$BACKEND_PORT" > backend_server.log 2>&1 &
  BACKEND_PID=$!
  echo -e "${CHECK_MARK} Backend server started with PID ${BOLD}$BACKEND_PID${RESET}"
  
  # Go back to the original directory
  cd ..
  
  # Wait for the server to start
  echo -e "${PENDING} Waiting for backend server to start..."
  sleep 5
  echo -e "${CHECK_MARK} Backend server is ready"
else
  echo -e "${CHECK_MARK} Backend server is already running"
fi

# Run CLI to generate tests
echo -e "\n${PENDING} Generating tests..."
if python cli.py --url "$URL" --test-steps "$STEPS_FILE" --framework "$FRAMEWORK" --language "$LANGUAGE" --max-retries "$MAX_RETRIES" --output "$OUTPUT_FILE"; then
  # Check if the test was generated successfully
  if [ -f "$OUTPUT_FILE" ]; then
    echo -e "${CHECK_MARK} Test generated successfully: ${BOLD}$OUTPUT_FILE${RESET}"
    echo -e "${CHECK_MARK} All tasks completed successfully ${GREEN}🎉${RESET}\n"
    exit 0
  else
    echo -e "${ERROR} Generated file not found: $OUTPUT_FILE"
    exit 1
  fi
else
  echo -e "${ERROR} Test generation failed"
  exit 1
fi 
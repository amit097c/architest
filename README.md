# Setting up the `ArchiTest` Project

## Option 1: Using Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed on your system
- Git to clone the repository

### Getting Started with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd architest
   ```

2. **Set up environment configuration**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file to add your API keys and configuration values.

3. **Start in development mode**
   ```bash
   docker-compose up
   ```
   This starts all services with hot reloading enabled.

4. **Start in production mode**
   ```bash
   # Using production configuration
   docker-compose -f docker-compose.prod.yml up -d
   ```
   This starts optimized production containers without development volumes.

5. **Access the application**
   - Development mode: http://localhost:5173
   - Production mode: http://localhost:3000
   - Backend API: http://localhost:8001
   - LLM Service: http://localhost:8000

6. **Using the CLI with Docker**
   ```bash
   docker-compose run --rm cli --url https://example.com --test-steps "Test step 1, Test step 2" --output output.py
   ```

7. **Rebuilding containers after changes to Dockerfiles**
   ```bash
   docker-compose build
   ```

8. **Stopping the application**
   ```bash
   docker-compose down
   ```

## Option 2: Local Setup (Without Docker)

1. **Follow the below commands to create and activate a new envinorment for this project**
   - First go to the folder where the project is located:
   ```bash
     cd path\to\your\project\wherever\it\is\located\architest
     ```
   - And then run the following commands to create and activate the environment
     ```bash
     conda create -n myenv
     conda activate myenv
     ```
2. **Install all the requirements**
   - Navigate to the architest project folder and run the below command to install all the required modules for the project
     ```bash
     pip install -r requirements.txt
     ```
3. **Setting up the frontend**
   - Navigate to the frontend folder from the architest project folder
     ```bash
     cd frontend
     ```
   - And run the below commands
     ```bash
      npm install
      ```
4. **For Java with Selenium execution**  
   - Create a folder `llm/agent/utils/java_utils` and copy the below installed drivers inside `java_utils`  
   - And install ChromeDriver and Chrome:  
     [https://googlechromelabs.github.io/chrome-for-testing/](https://googlechromelabs.github.io/chrome-for-testing/)  
   - And Selenium:  
     [https://www.selenium.dev/downloads/](https://www.selenium.dev/downloads/)

5. **For JavaScript with Playwright execution**  
   - Create a folder `llm/agent/utils/javascript_utils`  
   - And run the below commands inside the `javascript_utils` folder:
     ```bash
     npm init -y
     npm install -D @playwright/test
     npx playwright install
     ```


# Running the `ArchiTest` Project

## Option 1: Using Docker

1. **Start all services**
   ```bash
   docker-compose up
   ```

2. **Or start specific services**
   ```bash
   docker-compose up frontend backend
   ```

3. **Run in background**
   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

5. **Stop all services**
   ```bash
   docker-compose down
   ```

## Option 2: Local Setup

1. **Run the Backend Server**
   - Navigate to the Backend folder from the architest project folder
     ```bash
     uvicorn backend:app --reload --port 8001
     ```

2. **Run the Frontend**
   - Navigate to the Frontend folder from the architest project folder
     ```bash
     npm run dev
     ```

# Using the CLI for CI/CD

## Option 1: Using Docker

```bash
docker-compose run --rm cli --url https://example.com \
             --test-steps "1. Navigate to the login page. 2. Enter username and password. 3. Click login button." \
             --framework playwright \
             --language python \
             --max-retries 3 \
             --output generated_tests/example_test.py
```

## Option 2: Local Setup

1. **Make the CLI script executable** (Unix/Linux)
   ```bash
   chmod +x cli.py
   ```

2. **Basic Usage**
   ```bash
   python cli.py --url https://example.com
   ```

3. **Advanced Options**
   ```bash
   python cli.py --url https://example.com \
                 --test-steps "1. Navigate to the login page. 2. Enter username and password. 3. Click login button." \
                 --framework playwright \
                 --language python \
                 --max-retries 3 \
                 --output generated_tests/example_test.py
   ```

4. **Using a File for Test Steps**
   You can save your test steps in a text file and pass the file path:
   ```bash
   python cli.py --url https://example.com --test-steps test_steps.txt
   ```

5. **CLI Arguments**
   
   | Argument | Description | Default | Required |
   |----------|-------------|---------|----------|
   | `--url` | The URL to generate tests for | - | Yes |
   | `--test-steps` | Test steps description or path to file containing test steps | Empty string | No |
   | `--framework` | Testing framework to use (`playwright` or `selenium`) | `playwright` | No |
   | `--language` | Programming language for tests (`python`, `javascript`, or `java`) | `python` | No |
   | `--max-retries` | Maximum number of test retries | 3 | No |
   | `--output` | Output file to save generated tests | None (prints to console) | No |

6. **Using the Shell Script**
   
   The included shell script provides additional functionality, like automatic server startup:
   
   ```bash
   ./ci_generate_tests.sh --url https://example.com --steps test_steps.txt
   ```
   
   For more options:
   ```bash
   ./ci_generate_tests.sh --help
   ```

# Docker Deployment Guide

## Container Sizes and Optimization

- Frontend: ~75MB (Nginx + static assets)
- Backend: ~1.5GB (Python + Playwright)
- LLM Service: ~2.5GB (Python + ML libraries + Playwright)

The large sizes for Backend and LLM services are primarily due to the Playwright browser installation, which is required for web automation.

## Environment Variables

All required environment variables are documented in `.env.example`. For production deployment, ensure you:

1. Set `ENV=production` for optimized containers
2. Add your actual API keys for OpenAI/Azure and LangSmith
3. Adjust ports if needed

## Production Considerations

1. **Data Persistence**: The LLM service uses ChromaDB which stores data in a volume. This data is persisted between container restarts.

2. **Security**: The production containers run as non-root users for better security.

3. **Health Checks**: The containers include health checks to monitor their status.

4. **Resource Requirements**: Ensure your host has sufficient resources:
   - At least 4GB RAM
   - 10GB+ free disk space
   - 2+ CPU cores recommended

## Troubleshooting Docker Setup

1. **Container fails to start**: Check logs with `docker-compose logs <service-name>`

2. **Connection issues between services**: Ensure the environment variables are correctly set

3. **Volume mounting issues**: Check that paths in docker-compose.yml are correct

4. **Permission problems**: The containers run as non-root users in production

5. **Performance issues**: The LLM service is resource-intensive; consider adjusting resource limits
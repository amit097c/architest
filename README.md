# Setting up the `ArchiTest` Project

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

ArchiTest provides a command-line interface that can be used in CI/CD pipelines to generate tests without using the frontend.

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

7. **Example CI/CD Integration (GitHub Actions)**
   
   ```yaml
   name: Generate Website Tests
   
   on:
     schedule:
       - cron: '0 0 * * *'  # Daily at midnight
     workflow_dispatch:  # Manual trigger
   
   jobs:
     generate-tests:
       runs-on: ubuntu-latest
       
       steps:
       - name: Checkout repository
         uses: actions/checkout@v2
         
       - name: Set up Python
         uses: actions/setup-python@v2
         with:
           python-version: '3.10'
           
       - name: Install dependencies
         run: |
           pip install -r requirements.txt
           
       - name: Start backend server
         run: |
           cd Backend
           nohup uvicorn backend:app --host 0.0.0.0 --port 8001 &
           sleep 5  # Wait for server to start
           
       - name: Generate tests
         run: |
           python cli.py --url ${{ secrets.TEST_URL }} --test-steps test_scenarios/login.txt --output generated_tests/login_test.py
           
       - name: Archive generated tests
         uses: actions/upload-artifact@v2
         with:
           name: generated-tests
           path: generated_tests/
   ```
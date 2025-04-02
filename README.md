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

1. **Run the LLM Server**
   - Navigate to the LLM folder from the architest project folder
     ```bash
      uvicorn server:app --reload
      ```

2. **Run the Backend Server**
   - Navigate to the Backend folder from the architest project folder
     ```bash
     uvicorn backend:app --reload --port 8001
     ```

3. **Run the Frontend**
   - Navigate to the Frontend folder from the architest project folder
     ```bash
     npm run dev
     ```
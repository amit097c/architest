import ast
from typing import Optional

class PlaywrightTestStep:
    def __init__(self, func_str: str, description: str):
        self.func_str = func_str
        self.name = self.extract_function_name(func_str)  # Extract function name from the string
        self.description = description

    def extract_function_name(self, code_string: str):
        try:
            tree = ast.parse(code_string)  # Parse the code string into an AST
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name
        except SyntaxError as e:
            print(f"Syntax error in code string: {e}")
        return None

    def render_test_call(self):
        return (
            f"    page = {self.name}(page)  # {self.description}\n"
            f"    page.wait_for_load_state('load')\n"
            f"    html = page.content()\n"
            f"    with open('latest_page.html', 'w', encoding='utf-8') as f:\n"
            f"        f.write(html)\n"
        )

    def render_function(self):
        """Return the function code as a string."""
        return self.func_str  # Return the function code (as provided in the string)
    

class ScriptBuilder:
    def __init__(self, base_url: str = None):
        self.steps: list[PlaywrightTestStep] = []
        self.base_url = base_url
        
    def set_url(self, new_url: str):
        self.base_url = new_url

    def add_step(self, step: PlaywrightTestStep):
        self.steps.append(step)

    def replace_last_step(self, step: PlaywrightTestStep):
        if not self.steps:
            raise IndexError("No steps to replace.")
        self.steps[-1] = step

    def render_script(self) -> str:
        if not self.base_url:
            raise ValueError("Base URL must be set before rendering the script.")
        
        imports = "from playwright.sync_api import Page, expect\n\n\n"
        test_fn = "def test_main(page: Page):\n"
        test_fn += f"    page.goto(\"{self.base_url}\")  # Navigate to the initial URL\n\n"

        for step in self.steps:
            test_fn += step.render_test_call() + "\n"

        step_fns = "\n\n\n".join(step.render_function() for step in self.steps)
        return imports + test_fn + "\n" + step_fns
    
    def reset(self):
        self.steps = []
        self.base_url = None

class JavaScriptTestStep:
    def __init__(self, func_str, description):
        self.func_str = func_str
        self.description = description
        self.name = self.extract_function_name()

    def extract_function_name(self):
        import re
        match = re.search(r'async function (\w+)', self.func_str)
        return match.group(1) if match else None

    def render_test_call(self):
        return f"    await {self.name}(page); // {self.description}"

    def render_function(self):
        return self.func_str

class ScriptBuilderJS:
    def __init__(self, base_url: str = None):
        self.steps = []
        self.base_url = base_url

    def set_url(self, url):
        self.base_url = url

    def add_step(self, step):
        self.steps.append(step)

    def replace_last_step(self, step):
        if not self.steps:
            raise IndexError("No steps to replace.")
        self.steps[-1] = step

    def render_script(self):
        imports = "const { test, expect } = require('@playwright/test');\n\n"
        
        # Add a configuration for consistent execution
        imports += "// Configuration for better stability\n"
        imports += "const config = {\n"
        imports += "  timeout: 30000,\n"
        imports += "  retries: 1,\n"
        imports += "  reporter: 'list'\n"
        imports += "};\n\n"
        
        setup = f"test('Generated Test', async ({{ page }}) => {{\n    // Navigate to the initial URL\n    await page.goto('{self.base_url}');\n"

        for step in self.steps:
            setup += step.render_test_call() + "\n"

        setup += "});\n\n"

        functions = "\n\n".join(step.render_function() for step in self.steps)
        return imports + setup + functions
    
    def reset(self):
        self.steps = []
        self.base_url = None
    
class JavaTestStep:
    def __init__(self, func_str, description):
        self.func_str = func_str
        self.description = description
        self.name = self.extract_function_name()
        # Extract step number from the description if available
        self.step_number = self.extract_step_number()

    def extract_step_number(self):
        """Extract step number from description or fallback to a default."""
        import re
        # Try to extract from the description first
        if self.description:
            match = re.search(r'Step (\d+):', self.description)
            if match:
                return int(match.group(1))
        
        # If not found in description, try to extract from function name
        if self.name:
            match = re.search(r'step(\d+)_', self.name)
            if match:
                return int(match.group(1))
        
        # Default to 1 if no step number found
        return 1

    def extract_function_name(self):
        import re
        
        # Try to find the method name using standard regex pattern
        match = re.search(r'public\s+(?:static\s+)?void\s+(\w+)\s*\(', self.func_str)
        
        if match:
            return match.group(1)
        
        # If no match is found, check if this is a fixed/refined script that may have different formatting
        # Look for any method name pattern with WebDriver parameter
        alt_match = re.search(r'(?:public|private)\s+(?:static\s+)?void\s+(\w+)\s*\(\s*WebDriver', self.func_str)
        if alt_match:
            return alt_match.group(1)
        
        # Last resort: try to extract a name from the first line (useful for errors)
        first_line = self.func_str.split('\n')[0] if '\n' in self.func_str else self.func_str
        basic_match = re.search(r'step\d+_\w+', first_line)
        if basic_match:
            return basic_match.group(0)
            
        # If no name found and we have a description, create a name from it
        if self.description:
            # Extract step number and create a camelCase name from description
            step_num = self.extract_step_number()
            # Create a name from description text (removing "Step X: " prefix if present)
            desc_text = re.sub(r'^Step \d+:\s*', '', self.description)
            # Replace non-alphanumeric chars with spaces, title case it, remove spaces
            name_base = ''.join(word.capitalize() for word in re.sub(r'[^a-zA-Z0-9\s]', ' ', desc_text).split())
            # Ensure first letter is lowercase for camelCase
            if name_base:
                name_base = name_base[0].lower() + name_base[1:]
                return f"step{step_num}_{name_base}"
        
        # Final fallback
        print(f"WARNING: Could not extract function name from Java code: {self.func_str[:100]}...")
        return f"step{self.extract_step_number()}_unknown"
        
    def render_test_call(self):
        # Only render if we have a valid name (not None or empty)
        if not self.name:
            print("WARNING: Cannot render test call without function name. Check Java code.")
            return f"// ERROR: Missing function name for step: {self.description}"
        return f"{self.name}(driver); // {self.description}"

    def render_function(self):
        return self.func_str

class ScriptBuilderJava:
    def __init__(self, base_url=None):
        self.steps = []
        self.base_url = base_url

    def set_url(self, url):
        self.base_url = url

    def add_step(self, step):
        self.steps.append(step)

    def replace_last_step(self, step):
        if not self.steps:
            raise IndexError("No steps to replace.")
        self.steps[-1] = step

    def render_script(self):
        # Java imports
        imports = (
            "import org.openqa.selenium.By;\n"
            "import org.openqa.selenium.WebDriver;\n"
            "import org.openqa.selenium.WebElement;\n"
            "import org.openqa.selenium.chrome.ChromeDriver;\n"
            "import org.openqa.selenium.chrome.ChromeOptions;\n"
            "import org.openqa.selenium.support.ui.ExpectedConditions;\n"
            "import org.openqa.selenium.support.ui.WebDriverWait;\n"
            "import java.time.Duration;\n"
            "import org.openqa.selenium.interactions.Actions;\n"
            "import org.openqa.selenium.JavascriptExecutor;\n"
            "import java.util.concurrent.TimeUnit;\n\n"
        )

        # Class and main method
        header = (
            "public class GeneratedTest {\n"
            "  public static void main(String[] args) {\n"
            "    // Configure Chrome options for better stability\n"
            "    ChromeOptions options = new ChromeOptions();\n"
            "    options.addArguments(\"--headless=new\", \"--no-sandbox\", \"--disable-dev-shm-usage\");\n"
            "    options.addArguments(\"--window-size=1920,1080\");\n"
            "    options.setPageLoadTimeout(Duration.ofSeconds(60));\n\n"
            "    WebDriver driver = new ChromeDriver(options);\n"
            "    // Set implicit wait for better element detection\n"
            "    driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));\n"
            f"    // Navigate to the initial URL\n"
            f"    driver.get(\"{self.base_url}\");\n\n"
        )
 

        for step in self.steps:
            header += f"    {step.render_test_call()}\n"

        header += "    driver.quit();\n"
        header += "  }\n\n"
        
        # Add helper methods
        helper_methods = (
            "  /**\n"
            "   * Helper method to pause execution for the specified milliseconds\n"
            "   * @param millis time to sleep in milliseconds\n"
            "   */\n"
            "  private static void sleep(long millis) {\n"
            "    try {\n"
            "      Thread.sleep(millis);\n"
            "    } catch (InterruptedException e) {\n"
            "      e.printStackTrace();\n"
            "    }\n"
            "  }\n\n"
        )

        # Include all methods inside the class (and mark them as static)
        methods = "\n\n".join(
            self._make_static(step.render_function()) for step in self.steps
        )

        return imports + header + helper_methods + methods + "\n}"

    def _make_static(self, method_str: str) -> str:
        """
        Ensures that the step method is marked as static.
        If it already has 'public void', replace it with 'public static void'.
        """
        return method_str.replace("public void", "public static void", 1)
    
    def reset(self):
        self.steps = []
        self.base_url = None


# script_builder = ScriptBuilder()
# script_builder_js = ScriptBuilderJS()
# script_builder_java = ScriptBuilderJava()

# Global script builder instance
_script_builder = None

def get_script_builder():
    """Get the global script builder instance."""
    global _script_builder
    if _script_builder is None:
        raise RuntimeError("Script builder not initialized. Call set_script_builder first.")
    return _script_builder

def set_script_builder(builder):
    """Set the global script builder instance."""
    global _script_builder
    if not builder:
        raise ValueError("Cannot set None as script builder")
    _script_builder = builder

__all__ = [
    'PlaywrightTestStep',
    'JavaTestStep', 
    'JavaScriptTestStep',
    'ScriptBuilder',
    'ScriptBuilderJS',
    'ScriptBuilderJava',
    'get_script_builder',
    'set_script_builder'
]
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
        setup = f"test('Generated Test', async ({{ page }}) => {{\n    await page.goto('{self.base_url}');\n"

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

    def extract_function_name(self):
        import re
        match = re.search(r'public void (\w+)', self.func_str)
        return match.group(1) if match else None

    def render_test_call(self):
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
            "import org.openqa.selenium.support.ui.ExpectedConditions;\n"
            "import org.openqa.selenium.support.ui.WebDriverWait;\n"
            "import java.time.Duration;\n\n"
        )

        # Class and main method
        header = (
            "public class GeneratedTest {\n"
            "  public static void main(String[] args) {\n"
            "    WebDriver driver = new ChromeDriver();\n"
            f"    driver.get(\"{self.base_url}\");\n"
        )

        for step in self.steps:
            header += f"    {step.render_test_call()}\n"

        header += "    driver.quit();\n"
        header += "  }\n\n"

        # Include all methods inside the class (and mark them as static)
        methods = "\n\n".join(
            self._make_static(step.render_function()) for step in self.steps
        )

        return imports + header + methods + "\n}"

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
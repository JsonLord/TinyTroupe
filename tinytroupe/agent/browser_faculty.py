from tinytroupe.agent.mental_faculty import TinyMentalFaculty
from tinytroupe.tools import browser
import textwrap

class BrowserFaculty(TinyMentalFaculty):
    """
    A mental faculty that allows an agent to interact with a web browser.
    """

    def __init__(self):
        super().__init__("Browser Navigation")

    def process_action(self, agent, action: dict) -> bool:
        """
        Processes a browser-related action.
        """
        action_type = action.get("type")
        content = action.get("content")
        target = action.get("target")

        if action_type == "NAVIGATE":
            browser.navigate(target)
            agent.see(f"Navigated to {target}")
            return True
        elif action_type == "CLICK":
            browser.click(target)
            agent.see(f"Clicked on element with selector: {target}")
            return True
        elif action_type == "TYPE":
            browser.type_text(target, content)
            agent.see(f"Typed '{content}' into element with selector: {target}")
            return True
        elif action_type == "SCREENSHOT":
            screenshot_path = browser.screenshot()
            agent.see(f"Took a screenshot and saved it to {screenshot_path}. I will now analyze the screenshot.")
            # In a real implementation, you would then process the image.
            # For now, we'll just acknowledge that a screenshot was taken.
            return True
        return False

    def actions_definitions_prompt(self) -> str:
        """
        Returns the prompt for defining browser-related actions.
        """
        prompt = """
          - NAVIGATE: Navigate to a specific URL. The `target` should be the URL.
          - CLICK: Click on an element on the page. The `target` should be a CSS selector for the element.
          - TYPE: Type text into an element on the page. The `target` should be a CSS selector for the element, and `content` should be the text to type.
          - SCREENSHOT: Take a screenshot of the current page. The `content` will be a placeholder for vision, reminding you to analyze the image.
        """
        return textwrap.dedent(prompt)

    def actions_constraints_prompt(self) -> str:
        """
        Returns the prompt for defining constraints on browser-related actions.
        """
        prompt = """
        - When asked to perform a task on a website, first NAVIGATE to the URL.
        - Use CLICK and TYPE to interact with elements on the page to accomplish the task.
        - Use SCREENSHOT to get a visual representation of the page to help you decide on the next action.
        """
        return textwrap.dedent(prompt)

from tinytroupe.agent.mental_faculty import TinyMentalFaculty
from tinytroupe.tools.browser import Browser
from tinytroupe.openai_utils import analyze_image
import textwrap
import json

class BrowserFaculty(TinyMentalFaculty):
    """
    A mental faculty that allows an agent to interact with a web browser.
    """

    def __init__(self):
        super().__init__("Browser Navigation")
        self.browser = Browser()

    def process_action(self, agent, action: dict) -> bool:
        """
        Processes a browser-related action.
        """
        action_type = action.get("type")
        content = action.get("content")
        target = action.get("target")

        try:
            tool, operation = action_type.split(":/", 1)
        except ValueError:
            return False

        if tool not in ["Browser", "See", "Click", "Write", "Submit", "Wait", "Scroll", "Hover", "Keyboard_Key", "ScanPage"]:
            return False

        if operation == "NAVIGATE":
            result = self.browser.navigate(target)
            agent.see(result)
            return True
        elif operation == "Screenshot":
            image_url = self.browser.screenshot()

            # Retrieve the last thought from the agent's memory
            last_thought = ""
            recent_memories = agent.episodic_memory.retrieve_recent()
            for memory in reversed(recent_memories):
                if memory.get('content', {}).get('action', {}).get('type') == 'SEQUENTIAL_THINKING':
                    last_thought = memory['content']['action']['content']
                    break

            prompt = f"""
            Analyze the following screenshot of a website.

            **Agent's Last Thought:**
            {last_thought}

            **Instructions:**
            1.  **Overall Description:** Provide a clear and concise description of the website's purpose and content.
            2.  **Layout Analysis:** Describe the layout of the page, including the location of major elements like headers, navigation bars, main content areas, and footers.
            3.  **Navigation Tips:** Identify and suggest potential navigation options, such as links, buttons, or menus, that the agent could use to proceed with its task.
            4.  **Feedback:** Based on the agent's last thought, provide feedback and suggestions for the next action to take.
            """
            analysis = analyze_image(image_url, textwrap.dedent(prompt))
            agent.see(f"Screenshot analysis: {analysis}")
            return True
        elif operation == "Click":
            result = self.browser.click(target)
            agent.see(f"Click result: {result}")
            return True
        elif operation == "fill":
            result = self.browser.fill(target, content)
            agent.see(f"Fill result: {result}")
            return True
        elif operation == "submit_form":
            result = self.browser.submit_form(target, content)
            agent.see(f"Submit form result: {result}")
            return True
        elif operation == "wait_for_element":
            result = self.browser.wait_for_element(target)
            agent.see(f"Wait for element result: {result}")
            return True
        elif operation == "scroll_page":
            result = self.browser.scroll_page(target)
            agent.see(f"Scroll page result: {result}")
            return True
        elif operation == "hover_element":
            result = self.browser.hover_element(target)
            agent.see(f"Hover element result: {result}")
            return True
        elif operation == "press_key":
            result = self.browser.press_key(content, target)
            agent.see(f"Press key result: {result}")
            return True
        elif operation == "get_page_info":
            result = self.browser.get_page_info()
            agent.see(f"Get page info result: {result}")
            return True
        return False

    def actions_definitions_prompt(self) -> str:
        """
        Returns the prompt for defining browser-related actions.
        """
        prompt = """
          - Browser:/NAVIGATE: Navigate to a specific URL. The `target` should be the URL. This must be the first step.
          - See:/Screenshot: Take a screenshot of the current page and get a detailed analysis of its content and layout.
          - Click:/Click: Click on an element on the page. The `target` should be a CSS selector for the element.
          - Write:/fill: Type text into an element on the page. The `target` should be a CSS selector for the element, and `content` should be the text to type.
          - Submit:/submit_form: Submit a form. The `target` should be a CSS selector for the form, and `content` should be a JSON string of the form data.
          - Wait:/wait_for_element: Wait for an element to appear on the page. The `target` should be a CSS selector for the element.
          - Scroll:/scroll_page: Scroll the page up or down. The `target` should be 'up' or 'down'.
          - Hover:/hover_element: Hover over an element on the page. The `target` should be a CSS selector for the element.
          - Keyboard_Key:/press_key: Press a key on the keyboard. The `content` should be the key to press (e.g., 'Enter', 'Escape'), and `target` can be an optional CSS selector.
          - ScanPage:/get_page_info: Get information about the current page, such as the title and URL.
        """
        return textwrap.dedent(prompt)

    def actions_constraints_prompt(self) -> str:
        """
        Returns the prompt for defining constraints on browser-related actions.
        """
        prompt = """
        - You must always NAVIGATE to a URL before performing any other browser action.
        - Use See:/Screenshot to get a visual representation and analysis of the page to help you decide on the next action.
        - Use Click:/Click, Write:/fill, and Submit:/submit_form to interact with elements on the page to accomplish the task.
        - Use ScanPage:/get_page_info to understand the context of the current page.
        """
        return textwrap.dedent(prompt)

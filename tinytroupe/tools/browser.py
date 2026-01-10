import subprocess
import json
import shlex

_GRADIO_API_URL = "https://diamond-in-browser-use-mcp.hf.space/gradio_api/call"

class Browser:
    def __init__(self):
        self.current_url = None

    def _gradio_api_call(self, api_name: str, data: list) -> str:
        """
        Makes a two-step API call to the Gradio backend.
        """
        post_url = f"{_GRADIO_API_URL}/{api_name}"

        headers = {"Content-Type": "application/json"}
        post_data = json.dumps({"data": data})

        post_command = f"curl -s -X POST {post_url} -H '{headers['Content-Type']}' -d {shlex.quote(post_data)}"

        try:
            post_result = subprocess.run(post_command, shell=True, capture_output=True, text=True, check=True)
            event_id = json.loads(post_result.stdout).get("event_id")
            if not event_id:
                return f"Error: Could not get event ID from response: {post_result.stdout}"
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            return f"Error during POST request: {e}"

        get_url = f"{post_url}/{event_id}"
        get_command = f"curl -s -N {get_url}"

        try:
            get_result = subprocess.run(get_command, shell=True, capture_output=True, text=True, check=True)
            lines = get_result.stdout.strip().split('\n')
            for line in reversed(lines):
                if line.startswith("data:"):
                    try:
                        response_data = json.loads(line[len("data:"):])
                        if response_data.get("msg") == "process_completed":
                            return response_data.get("output", {}).get("data", [None])[0]
                    except json.JSONDecodeError:
                        continue
            return "Error: Could not parse final result from SSE stream."
        except subprocess.CalledProcessError as e:
            return f"Error during GET request: {e}"

    def navigate(self, url: str):
        """Navigates to the given URL by setting the current URL."""
        self.current_url = url
        print(f"Navigating to {url}...")
        return f"Navigated to {url}"

    def click(self, selector: str):
        """Clicks on the element with the given CSS selector."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("click", [self.current_url, selector, True])

    def fill(self, selector: str, text: str):
        """Fills the given text into the element with the given CSS selector."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("fill", [self.current_url, selector, text, True])

    def submit_form(self, selector: str, form_data: str = "{}"):
        """Submits the form with the given CSS selector."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("submit_form", [self.current_url, form_data, selector, True])

    def wait_for_element(self, selector: str, timeout: int = 10):
        """Waits for the element with the given CSS selector to appear."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("wait_for_element", [self.current_url, selector, timeout, True])

    def scroll_page(self, direction: str):
        """Scrolls the page in the given direction."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("scroll_page", [self.current_url, direction, 100, True])

    def hover_element(self, selector: str):
        """Hovers over the element with the given CSS selector."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("hover_element", [self.current_url, selector, True])

    def press_key(self, key: str, selector: str):
        """Presses the given key on a target element."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("press_key", [self.current_url, key, selector, True])

    def get_page_info(self):
        """Gets information about the current page."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("get_page_info", [self.current_url, True])

    def screenshot(self, full_page: bool = True):
        """Takes a screenshot of the current page and returns the path to the image."""
        if not self.current_url:
            return "Error: URL not set. Please navigate to a URL first."
        return self._gradio_api_call("screenshot", [self.current_url, full_page, True])

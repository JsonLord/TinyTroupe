from tinytroupe.agent.mental_faculty import TinyToolUse
from gradio_client import Client
import json
from tinytroupe.validation.computer_use_validator import ComputerUseValidator


class ComputerUseTool(TinyToolUse):
    def __init__(self, client: Client = None, website_url: str = None):
        super().__init__(tools=[self])
        self._validator = None
        self._is_retrying = False
        self.name = "computer_use"
        self.description = "A tool to interact with a Gradio API, allowing for calling specific API endpoints with parameters."
        self.actions_list = [
            {"action": "navigate", "description": "Navigate to a URL."},
            {"action": "see", "description": "Wait for an element to be visible on the page."},
            {"action": "click", "description": "Simulate a mouse click on an element."},
            {"action": "fill", "description": "Enter text into an input field."},
            {"action": "submit", "description": "Submit a form."},
            {"action": "wait", "description": "Pause execution for a specified duration."},
            {"action": "scroll", "description": "Scroll the view to a specific element or position."},
            {"action": "hover", "description": "Simulate hovering the mouse pointer over an element."},
            {"action": "press_key", "description": "Simulate pressing a sequence of keys, often used for typing or sending special key combinations. The keys should be provided as a list in the 'keys' parameter."}
        ]
        self.action_mapping = {
            "navigate": "/get_page_info",
            "see": "/get-page-info",
            "click": "/click",
            "fill": "/fill",
            "submit": "/submit_form",
            "wait": "/wait_for_element",
            "scroll": "/scroll_page",
            "hover": "/hover_element",
            "press_key": "/press_key"
        }
        self.actions_requiring_url = [
            "navigate", "see", "click", "fill", "submit", "wait", "scroll", "hover", "press_key"
        ]
        self.website_url = website_url
        if client:
            self.client = client
        else:
            self.client = Client("diamond-in/Browser-Use-mcp")

    def _get_validator(self):
        if self._validator is None:
            self._validator = ComputerUseValidator(self)
        return self._validator

    def process_action(self, agent, action: dict) -> bool:
        if action['type'] == self.name:
            try:
                return self._execute_action(agent, action)
            except Exception as e:
                agent.think(f"Error using computer_use tool: {e}")
                return False
        return False

    def _execute_action(self, agent, action: dict) -> bool:
        content = json.loads(action['content'])
        action_name = content.get('action_name')

        if not action_name:
            agent.think("Error: 'action_name' is a required parameter for the computer_use tool.")
            return False

        api_name = self.action_mapping.get(action_name)

        if not api_name:
            agent.think(f"Error: Unknown action '{action_name}'.")
            return False

        params = {k: v for k, v in content.items() if k != 'action_name'}
        params['use_persistent'] = True

        if 'url' not in params:
            params['url'] = self.website_url

        if action_name == 'press_key':
            keys = params.get('keys', [])
            results = []
            for key in keys:
                key_params = params.copy()
                key_params['key'] = key
                if 'keys' in key_params:
                    del key_params['keys']
                result = self.client.predict(api_name=api_name, **key_params)
                results.append(result)
            final_result = ", ".join(results)
        else:
            final_result = self.client.predict(api_name=api_name, **params)

        if not final_result:
            agent.think(f"Error: No data retrieved for action '{action_name}'. The API call may have failed silently.")
            return False

        if action_name == 'navigate':
            if isinstance(final_result, dict):
                page_info = final_result.get('page_info', 'No page info available.')
                agent.think(f"Successfully performed action 'navigate'. Current page info: {page_info}")
            else:
                agent.think(f"Successfully performed action 'navigate', but no page info was returned.")
        else:
            agent.think(f"Successfully performed action '{action_name}'.")

        # Validate and refine the result.
        if not self._is_retrying:
            validated_result = self._get_validator().validate_and_refine(agent, content, final_result)
        else:
            self._is_retrying = False
            validated_result = final_result
        # Store the result in the agent's episodic memory as a stimulus
        stimulus_content = {
            "stimuli": [{
                "type": "TOOL_RESULT",
                "content": f"Action '{action_name}' result: {str(validated_result)}",
                "source": self.name
            }]
        }
        memory_entry = {
            'role': 'user',  # Stimuli are from the 'user' perspective for the agent
            'content': stimulus_content,
            'type': 'stimulus',
            'simulation_timestamp': agent.iso_datetime()
        }
        agent.store_in_memory(memory_entry)

        return True

    def actions_definitions_prompt(self) -> str:
        return """
        {
          "name": "computer_use",
          "description": "Perform a browser action.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "action_name": {
                "type": "string",
                "description": "The name of the action to perform."
              },
              "selector": {
                "type": "string",
                "description": "The CSS selector of the element to interact with."
              },
              "text": {
                "type": "string",
                "description": "The text to fill into an input field."
              },
              "url": {
                "type": "string",
                "description": "The URL to navigate to."
              },
              "keys": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "A list of keys to press."
              }
            },
            "required": ["action_name"]
          }
        }
        """

    def actions_constraints_prompt(self) -> str:
        return ""

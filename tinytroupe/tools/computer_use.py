from tinytroupe.agent.mental_faculty import TinyToolUse
from gradio_client import Client
import json

class ComputerUseTool(TinyToolUse):
    def __init__(self, client: Client):
        super().__init__(tools=[self])
        self.name = "computer_use"
        self.description = "A tool to interact with a Gradio API, allowing for calling specific API endpoints with parameters."
        self.actions_list = [
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
            "see": "/get-page-info",
            "click": "/click",
            "fill": "/fill",
            "submit": "/submit_form",
            "wait": "/wait_for_element",
            "scroll": "/scroll_page",
            "hover": "/hover_element",
            "press_key": "/press_key"
        }
        self.client = client

    def process_action(self, agent, action: dict) -> bool:
        if action['type'] == self.name:
            try:
                content = json.loads(action['content'])
                action_name = content.get('action')

                if not action_name:
                    agent.think("Error: 'action' is a required parameter for the computer_use tool.")
                    return False

                api_name = self.action_mapping.get(action_name)

                if not api_name:
                    agent.think(f"Error: Unknown action '{action_name}'.")
                    return False

                params = {k: v for k, v in content.items() if k != 'action'}
                params['use_persistent'] = True

                if action_name == 'press_key':
                    keys = params.get('keys', [])
                    results = []
                    for key in keys:
                        key_params = params.copy()
                        key_params['key'] = key
                        del key_params['keys']
                        result = self.client.predict(api_name=api_name, **key_params)
                        results.append(result)
                    final_result = ", ".join(results)
                else:
                    final_result = self.client.predict(api_name=api_name, **params)

                agent.think(f"Successfully performed action '{action_name}'.")
                agent.memory.add_observation(f"Action '{action_name}' result: {str(final_result)}")

                return True
            except json.JSONDecodeError:
                agent.think("Error: The 'content' for computer_use must be a valid JSON string.")
                return False
            except Exception as e:
                agent.think(f"Error using computer_use tool: {e}")
                return False
        return False

    def actions_definitions_prompt(self) -> str:
        # The prompt should describe the 'content' field as a JSON string
        return """
        {
          "name": "computer_use",
          "description": "Call a specific endpoint of the Gradio API. The 'content' field must be a JSON string containing the 'api_name' and any other parameters for the endpoint.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "content": {
                "type": "string",
                "description": "A JSON string with the API call details. Must include 'api_name' and can include other parameters as key-value pairs. For example: '{\\"api_name\\": \\"/lambda_1\\", \\"provider\\": \\"openai\\"}'"
              }
            },
            "required": ["content"]
          }
        }
        """

    def actions_constraints_prompt(self) -> str:
        return ""

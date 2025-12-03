from tinytroupe.agent.mental_faculty import TinyToolUse
from gradio_client import Client
import json

class ComputerUseTool(TinyToolUse):
    def __init__(self, client: Client = None):
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
        if client:
            self.client = client
        else:
            self.client = Client("diamond-in/Browser-Use-mcp")

    def process_action(self, agent, action: dict) -> bool:
        if action['type'] == self.name:
            try:
                content = action['content']
                parts = content.split(' ')
                action_name = parts[0]

                if not action_name:
                    agent.think("Error: 'action' is a required parameter for the computer_use tool.")
                    return False

                api_name = self.action_mapping.get(action_name)

                if not api_name:
                    agent.think(f"Error: Unknown action '{action_name}'.")
                    return False

                params = {}
                if len(parts) > 1:
                    if action_name == 'fill':
                        params['selector'] = parts[1]
                        params['text'] = ' '.join(parts[2:])
                    elif action_name == 'press_key':
                        params['keys'] = parts[1:]
                    else:
                        params['selector'] = parts[1]

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
            except Exception as e:
                agent.think(f"Error using computer_use tool: {e}")
                return False
        return False

    def actions_definitions_prompt(self) -> str:
        # The prompt should describe the 'content' field as a JSON string
        return """
        {
          "name": "computer_use",
          "description": "Perform a browser action. The 'content' is a string with the action and its parameters.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "content": {
                "type": "string",
                "description": "A string with the action and its parameters, e.g., 'click #submit-button' or 'fill #username-field John Doe'."
              }
            },
            "required": ["content"]
          }
        }
        """

    def actions_constraints_prompt(self) -> str:
        return ""

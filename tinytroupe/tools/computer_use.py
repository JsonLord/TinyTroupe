from tinytroupe.agent.mental_faculty import TinyToolUse
from gradio_client import Client
import json

class ComputerUseTool(TinyToolUse):
    def __init__(self):
        super().__init__(tools=[self])
        self.name = "computer_use"
        self.description = "A tool to interact with a Gradio API, allowing for calling specific API endpoints with parameters."
        self.url = "https://c2b846c65c20419ff6.gradio.live/"

    def process_action(self, agent, action: dict) -> bool:
        if action['type'] == self.name:
            try:
                content = json.loads(action['content'])
                api_name = content.get('api_name')

                if not api_name:
                    agent.think("Error: 'api_name' is a required parameter for the computer_use tool.")
                    return False

                # All other parameters are passed as keyword arguments
                params = {k: v for k, v in content.items() if k != 'api_name'}

                client = Client(self.url)
                result = client.predict(api_name=api_name, **params)

                agent.think(f"Successfully called API '{api_name}'.")
                # The result might be complex, so we just log a summary
                # It's the agent's job to parse this in its next thought
                agent.memory.add_observation(f"API call result: {json.dumps(result)}")

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

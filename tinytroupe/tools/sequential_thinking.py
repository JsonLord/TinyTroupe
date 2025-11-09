import requests
import json
from tinytroupe.agent.mental_faculty import TinyToolUse

class SequentialThinkingTool(TinyToolUse):
    def __init__(self):
        super().__init__(tools=[self])
        self.url = "https://harvesthealth-sequential-thinking-mcp.hf.space/run"

    def process_action(self, agent, action: dict) -> bool:
        if action['type'] == 'SEQUENTIAL_THINKING':
            # The action content is a string, so we need to parse it as JSON
            try:
                arguments = json.loads(action['content'])
            except json.JSONDecodeError:
                # If the content is not a valid JSON string, we can't process it.
                return False

            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "sequentialthinking",
                    "arguments": arguments
                }
            }
            response_json = self.send_thought(payload)

            # Process the response
            if response_json and 'result' in response_json and 'content' in response_json['result']:
                content_text = response_json['result']['content'][0]['text']
                # The response text is a JSON string, so we need to parse it
                try:
                    response_data = json.loads(content_text)
                    # Now you can use the response_data to update the agent's state or memory
                    # For example, you could store the thought history length in the agent's memory
                    agent.think(f"Thought processed. History length: {response_data.get('thoughtHistoryLength')}")
                except json.JSONDecodeError:
                    # Handle cases where the response text is not valid JSON
                    agent.think("Received a response from the sequential thinking server, but it was not in the expected format.")

            return True
        return False

    def send_thought(self, thought_data: dict):
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.url, headers=headers, json=thought_data)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            # Handle network errors
            print(f"Error sending thought: {e}")
            return None

    def actions_definitions_prompt(self) -> str:
        return ""

    def actions_constraints_prompt(self) -> str:
        return ""

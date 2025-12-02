import requests
import json
from tinytroupe.tools.tiny_tool import TinyTool
from tinytroupe.utils.logger import get_logger

class SequentialThinkingTool(TinyTool):
    def __init__(self):
        super().__init__(
            name="sequential_thinking",
            description="A tool for dynamic and reflective problem-solving through a sequence of thoughts, interacting with an external MCP server."
        )
        self.url = "https://harvesthealth-sequential-thinking-mcp.hf.space/run"

    def _process_action(self, agent, action: dict) -> bool:
        if action['type'] == self.name:
            logger = get_logger(agent.name)

            try:
                arguments = json.loads(action['content'])
            except json.JSONDecodeError as e:
                logger.error(f"MCP Interaction - Invalid JSON in action content: {action['content']}. Error: {e}")
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

            logger.info(f"MCP Interaction - Request: {json.dumps(payload, indent=2)}")
            response_json = self.send_thought(payload)
            logger.info(f"MCP Interaction - Response: {json.dumps(response_json, indent=2)}")

            if response_json and 'result' in response_json and 'content' in response_json['result']:
                content_text = response_json['result']['content'][0]['text']
                try:
                    response_data = json.loads(content_text)
                    agent.think(f"Thought processed. History length: {response_data.get('thoughtHistoryLength')}")
                except json.JSONDecodeError:
                    logger.error(f"MCP Interaction - Could not decode response content: {content_text}")
                    agent.think("Received a response from the sequential thinking server, but it was not in the expected format.")

            return True
        return False

    def send_thought(self, thought_data: dict):
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.url, headers=headers, json=thought_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def actions_definitions_prompt(self) -> str:
        return """
        {
          "name": "sequential_thinking",
          "description": "A detailed tool for dynamic and reflective problem-solving through thoughts. The 'content' field must be a JSON string containing the arguments for the thinking step.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "content": {
                "type": "string",
                "description": "A JSON string with the thinking step details. Must include 'thought', 'nextThoughtNeeded', 'thoughtNumber', and 'totalThoughts'. For example: '{\\"thought\\": \\"My first thought...\\", \\"nextThoughtNeeded\\": true, \\"thoughtNumber\\": 1, \\"totalThoughts\\": 5}'"
              }
            },
            "required": ["content"]
          }
        }
        """

    def actions_constraints_prompt(self) -> str:
        return ""

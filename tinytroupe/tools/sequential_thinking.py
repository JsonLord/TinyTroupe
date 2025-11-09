import requests
from tinytroupe.agent.mental_faculty import TinyToolUse

class SequentialThinkingTool(TinyToolUse):
    def __init__(self):
        super().__init__(tools=[self])
        self.url = "https://harvesthealth-sequential-thinking-mcp.hf.space/run"

    def process_action(self, agent, action: dict) -> bool:
        if action['type'] == 'SEQUENTIAL_THINKING':
            self.send_thought(action['content'])
            return True
        return False

    def send_thought(self, thought_data: dict):
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.url, headers=headers, json=thought_data)
        return response.json()

    def actions_definitions_prompt(self) -> str:
        return ""

    def actions_constraints_prompt(self) -> str:
        return ""

from tinytroupe.agent.mental_faculty import TinyToolUse
from browser_use import Agent, Browser, ChatBrowserUse
import asyncio
import json

class ComputerUseTool(TinyToolUse):
    def __init__(self):
        super().__init__(tools=[self])
        self.name = "computer_use"
        self.description = "A tool to perform browser automation tasks using natural language."

    async def _run_browser_task(self, task):
        browser = Browser(use_cloud=True, allowed_domains=[])
        llm = ChatBrowserUse()
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            use_vision=True,
            use_thinking=False,
            flash_mode=False,
            highlight_elements=False,
        )
        history = await agent.run(max_steps=75)
        return history.final_result()

    def process_action(self, agent, action: dict) -> bool:
        if action['type'] == self.name:
            try:
                content = json.loads(action['content'])
                task = content.get('task')

                if not task:
                    agent.think("Error: 'task' is a required parameter for the computer_use tool.")
                    return False

                result = asyncio.run(self._run_browser_task(task))

                agent.think(f"Successfully executed browser task.")
                agent.memory.add_observation(f"Browser task result: {str(result)}")

                return True
            except json.JSONDecodeError:
                agent.think("Error: The 'content' for computer_use must be a valid JSON string.")
                return False
            except Exception as e:
                agent.think(f"Error using computer_use tool: {e}")
                return False
        return False

    def actions_definitions_prompt(self) -> str:
        return """
        {
          "name": "computer_use",
          "description": "Perform a browser automation task. The 'content' field must be a JSON string containing a 'task' written in natural language.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "content": {
                "type": "string",
                "description": "A JSON string with the browser task details. Must include a 'task' key. For example: '{\\"task\\": \\"Go to example.com and click the 'About Us' link.\\"}'"
              }
            },
            "required": ["content"]
          }
        }
        """

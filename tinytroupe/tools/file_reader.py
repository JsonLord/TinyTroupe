import json
from tinytroupe.agent.mental_faculty import TinyToolUse

class FileReaderTool(TinyToolUse):
    def __init__(self):
        super().__init__(tools=[self])
        self.name = "file_reader"
        self.description = "A tool for reading files from the repository."

    def process_action(self, agent, action: dict) -> str:
        if action["type"] == self.name:
            try:
                content = json.loads(action["content"])
                filepath = content.get("filepath")

                if not filepath:
                    return "Error: filepath is a required parameter."

                with open(filepath, "r") as f:
                    return f.read()
            except Exception as e:
                return f"Error using file_reader tool: {e}"
        return ""

    def actions_definitions_prompt(self) -> str:
        return """
        {
          "name": "file_reader",
          "description": "Read a file from the repository.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "filepath": {
                "type": "string",
                "description": "The path to the file to read."
              }
            },
            "required": ["filepath"]
          }
        }
        """

    def actions_constraints_prompt(self) -> str:
        return ""

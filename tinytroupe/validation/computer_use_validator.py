import json
from tinytroupe.agent.tiny_person import TinyPerson
from tinytroupe.tools.sequential_thinking import SequentialThinkingTool
from tinytroupe.tools.file_reader import FileReaderTool
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tinytroupe.tools.computer_use import ComputerUseTool


class ComputerUseValidator:
    def __init__(self, computer_use_tool: "ComputerUseTool"):
        self.computer_use_tool = computer_use_tool
        self.validation_agent = TinyPerson(
            name="ComputerUseValidator",
            mental_faculties=[SequentialThinkingTool(), computer_use_tool, FileReaderTool()]
        )
        self.validation_agent._persona["persona"] = "An AI agent that validates the output of the computer_use tool."

    def validate_and_refine(self, persona_agent: TinyPerson, action: dict, result: str, max_retries: int = 3) -> str:
        """
        Validates the result of a computer_use action and refines it if necessary.

        Args:
            persona_agent: The agent that called the computer_use tool.
            action: The action that was performed.
            result: The result of the action.
            max_retries: The maximum number of times to retry the action.

        Returns:
            The validated and refined result.
        """
        validation_history = []
        for i in range(max_retries):
            # Provide the validation agent with the context it needs to make a decision.
            last_thought = persona_agent.last_remembered_action(ignore_done=True)
            history_str = "\n".join(validation_history)
            context = f"""
            The user, {persona_agent.name}, had the following last thought:
            {last_thought}

            They then used the computer_use tool with the following action:
            {json.dumps(action, indent=2)}

            The tool returned the following result:
            {result}

            This is validation attempt {i + 1} of {max_retries}.
            Validation history:
            {history_str}

            Your task is to validate this result and refine it if necessary.
            - If the result is valid, return it to the user in a clear and concise message.
            - If the result is "successful" but does not contain the expected data (e.g., "no page info returned"), you should use the file_reader tool to consult `tinytroupe/tools/computer_use_documentation.txt`.
            - After reading the documentation, use the sequential_thinking tool to reason about the user's original goal and the available API calls to find a more suitable action.
            - If the result is invalid, use the sequential_thinking tool to determine the cause of the error and then use the computer_use tool to correct it.
            - If you have tried simple corrections and they have failed, you should use the sequential_thinking tool to reflect on the situation and come up with a better plan.
            - If you are unable to correct the error, return an error message to the user.
            """
            self.validation_agent._update_cognitive_state(context=context)

            # Have the validation agent think about the problem and decide on a course of action.
            self.validation_agent.think("I need to validate the result of the computer_use tool.")

            # Get the validation agent's response.
            response = self.validation_agent.act(return_actions=True)[0]['action']['content']

            # If the response is a tool call, execute it.
            if response.startswith("{"):
                response_action = json.loads(response)
                validation_history.append(f"Attempt {i + 1}: {response_action}")
                if response_action["tool"] == "sequential_thinking":
                    # The validation agent has determined that the result is invalid and is using the
                    # sequential_thinking tool to determine the cause of the error.
                    sequential_thinking_tool = next((t for t in self.validation_agent._mental_faculties if t.name == "sequential_thinking"), None)
                    if sequential_thinking_tool:
                        sequential_thinking_result = sequential_thinking_tool.process_action(self.validation_agent, response_action)
                        # The sequential_thinking tool will return a corrected computer_use action.
                        corrected_action = json.loads(sequential_thinking_result)
                    else:
                        # Handle the case where the tool is not found
                        return "Error: sequential_thinking tool not found."
                    # We need to set the _is_retrying flag to True to prevent the validator from
                    # re-validating its own actions.
                    self.computer_use_tool._is_retrying = True
                    result = self.computer_use_tool.process_action(self.validation_agent, corrected_action)
                elif response_action["tool"] == "computer_use":
                    # The validation agent has determined that the result is invalid and is
                    # correcting the error with a new computer_use action.
                    self.computer_use_tool._is_retrying = True
                    result = self.computer_use_tool.process_action(self.validation_agent, response_action)
            else:
                # If the response is not a tool call, it means the result is valid.
                return response
        # If the loop completes, it means the validation agent was unable to correct the error.
        return "Error: Unable to validate the result after multiple retries."

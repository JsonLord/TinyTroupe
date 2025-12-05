import pytest
import json
from unittest.mock import MagicMock, patch
from tinytroupe.tools.computer_use import ComputerUseTool
from tinytroupe.validation.computer_use_validator import ComputerUseValidator

@pytest.fixture
def mock_agent():
    """Fixture for a mock agent."""
    agent = MagicMock()
    agent.name = "TestAgent"
    agent.think = MagicMock()
    agent.act = MagicMock()
    agent.last_remembered_action = MagicMock(return_value="I want to click the button.")
    return agent

def test_validate_and_refine_success(mock_agent):
    """Test that the validator returns the result when the action is successful."""
    mock_computer_use_tool = MagicMock()
    validator = ComputerUseValidator(mock_computer_use_tool)
    action = {"action_name": "click", "selector": "#button"}
    result = "Success"

    with patch('tinytroupe.agent.tiny_person.TinyPerson.act') as mock_act:
        mock_act.return_value = [{'action': {'content': "The result is valid."}}]
        validated_result = validator.validate_and_refine(mock_agent, action, result)
        assert validated_result == "The result is valid."

def test_validate_and_refine_failure_and_retry(mock_agent):
    """Test that the validator retries the action when the action fails."""
    mock_computer_use_tool = MagicMock()
    validator = ComputerUseValidator(mock_computer_use_tool)
    action = {"action_name": "click", "selector": "#button"}
    result = "Error: Button not found."

    with patch('tinytroupe.agent.tiny_person.TinyPerson.act') as mock_act:
        mock_act.side_effect = [
            [{'action': {'content': json.dumps({
                "tool": "computer_use",
                "content": json.dumps({"action_name": "click", "selector": "#correct-button"})
            })}}],
            [{'action': {'content': "The result is valid."}}]
        ]
        mock_computer_use_tool.process_action.return_value = "Success"
        validator.validate_and_refine(mock_agent, action, result)
        assert mock_computer_use_tool.process_action.call_count == 1

def test_validate_and_refine_failure_and_sequential_thinking(mock_agent):
    """Test that the validator uses sequential thinking when the action fails and the cause is unknown."""
    mock_computer_use_tool = MagicMock()
    validator = ComputerUseValidator(mock_computer_use_tool)
    action = {"action_name": "click", "selector": "#button"}
    result = "Error: Unknown error."

    with patch('tinytroupe.agent.tiny_person.TinyPerson.act') as mock_act:
        mock_act.side_effect = [
            [{'action': {'content': json.dumps({
                "tool": "sequential_thinking",
                "content": json.dumps({"thought": "I need to figure out what went wrong."})
            })}}],
            [{'action': {'content': "The result is valid."}}]
        ]
        with patch('tinytroupe.tools.sequential_thinking.SequentialThinkingTool.process_action') as mock_sequential_thinking:
            mock_sequential_thinking.return_value = json.dumps({
                "tool": "computer_use",
                "content": json.dumps({"action_name": "click", "selector": "#correct-button"})
            })
            mock_computer_use_tool.process_action.return_value = "Success"
            validator.validate_and_refine(mock_agent, action, result)
            assert mock_computer_use_tool.process_action.call_count == 1

def test_validate_and_refine_multiple_retries(mock_agent):
    """Test that the validator retries multiple times before succeeding."""
    mock_computer_use_tool = MagicMock()
    validator = ComputerUseValidator(mock_computer_use_tool)
    action = {"action_name": "click", "selector": "#button"}
    result = "Error: Button not found."

    with patch('tinytroupe.agent.tiny_person.TinyPerson.act') as mock_act:
        mock_act.side_effect = [
            [{'action': {'content': json.dumps({
                "tool": "computer_use",
                "content": json.dumps({"action_name": "click", "selector": "#wrong-button"})
            })}}],
            [{'action': {'content': json.dumps({
                "tool": "sequential_thinking",
                "content": json.dumps({"thought": "The first attempt failed. I will try a different approach."})
            })}}],
            [{'action': {'content': "The result is valid."}}]
        ]
        with patch('tinytroupe.tools.sequential_thinking.SequentialThinkingTool.process_action') as mock_sequential_thinking:
            mock_sequential_thinking.return_value = json.dumps({
                "tool": "computer_use",
                "content": json.dumps({"action_name": "click", "selector": "#correct-button"})
            })
            mock_computer_use_tool.process_action.side_effect = ["Error: Still not found.", "Success"]
            validated_result = validator.validate_and_refine(mock_agent, action, result)
            assert validated_result == "The result is valid."
            assert mock_computer_use_tool.process_action.call_count == 2

def test_validate_and_refine_goal_oriented(mock_agent):
    """Test that the validator can infer the user's goal and find a better tool for the job."""
    mock_computer_use_tool = MagicMock()
    validator = ComputerUseValidator(mock_computer_use_tool)
    action = {"action_name": "navigate", "url": "https://example.com"}
    result = "Successfully performed action 'navigate', but no page info was returned."

    with patch('tinytroupe.agent.tiny_person.TinyPerson.act') as mock_act:
        mock_act.side_effect = [
            [{'action': {'content': json.dumps({
                "tool": "file_reader",
                "content": json.dumps({"filepath": "tinytroupe/tools/computer_use_documentation.txt"})
            })}}],
            [{'action': {'content': json.dumps({
                "tool": "sequential_thinking",
                "content": json.dumps({"thought": "The user wanted to see the page content, but the `navigate` action did not provide it. I should use the `get_html_source` action instead."})
            })}}],
            [{'action': {'content': "The result is valid."}}]
        ]
        with patch('tinytroupe.tools.file_reader.FileReaderTool.process_action') as mock_file_reader:
            mock_file_reader.return_value = "API documentation..."
            with patch('tinytroupe.tools.sequential_thinking.SequentialThinkingTool.process_action') as mock_sequential_thinking:
                mock_sequential_thinking.return_value = json.dumps({
                    "tool": "computer_use",
                    "content": json.dumps({"action_name": "get_html_source", "url": "https://example.com"})
                })
                mock_computer_use_tool.process_action.return_value = "<html>...</html>"
                validated_result = validator.validate_and_refine(mock_agent, action, result)
                assert validated_result == "The result is valid."
                assert mock_computer_use_tool.process_action.call_count == 1

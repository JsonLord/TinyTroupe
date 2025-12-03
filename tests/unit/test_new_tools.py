import pytest
from unittest.mock import MagicMock, patch
from tinytroupe.tools.sequential_thinking import SequentialThinkingTool
from tinytroupe.tools.computer_use import ComputerUseTool

@pytest.fixture
def mock_agent():
    """Fixture for a mock agent."""
    agent = MagicMock()
    agent.name = "TestAgent"
    # Mock the think method to prevent it from being called directly
    agent.think = MagicMock()
    # Mock memory to have an add_observation method
    agent.memory = MagicMock()
    agent.memory.add_observation = MagicMock()
    return agent

def test_sequential_thinking_tool_process_action(mock_agent):
    """Test that SequentialThinkingTool correctly processes a sequential_thinking action."""
    tool = SequentialThinkingTool()
    action = {
        'type': 'sequential_thinking',
        'content': '{"thought": "This is a test thought.", "nextThoughtNeeded": true, "thoughtNumber": 1, "totalThoughts": 1}'
    }

    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0", "id": 1, "result": { "content": [{ "type": "text", "text": '{"thoughtHistoryLength": 1}' }] }
        }
        mock_post.return_value = mock_response

        result = tool.process_action(mock_agent, action)
        assert result is True
        mock_agent.think.assert_called_with("Thought processed. History length: 1")

def test_computer_use_tool_process_action(mock_agent):
    """Test that ComputerUseTool correctly processes a computer_use action."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action = {
        'type': 'computer_use',
        'content': '{"action": "click", "param1": "value1"}'
    }

    mock_client.predict.return_value = {"status": "success"}

    result = tool.process_action(mock_agent, action)
    assert result is True
    mock_client.predict.assert_called_with(api_name="/click", use_persistent=True, param1="value1")
    mock_agent.think.assert_called_with("Successfully performed action 'click'.")

def test_computer_use_tool_missing_action(mock_agent):
    """Test that ComputerUseTool handles a missing action gracefully."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action = {
        'type': 'computer_use',
        'content': '{"param1": "value1"}'
    }

    result = tool.process_action(mock_agent, action)
    assert result is False
    mock_agent.think.assert_called_with("Error: 'action' is a required parameter for the computer_use tool.")

def test_computer_use_tool_press_key_action(mock_agent):
    """Test that ComputerUseTool correctly processes a press_key action."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action = {
        'type': 'computer_use',
        'content': '{"action": "press_key", "keys": ["a", "b", "c"]}'
    }

    mock_client.predict.return_value = "key pressed"

    result = tool.process_action(mock_agent, action)
    assert result is True
    assert mock_client.predict.call_count == 3
    mock_agent.think.assert_called_with("Successfully performed action 'press_key'.")

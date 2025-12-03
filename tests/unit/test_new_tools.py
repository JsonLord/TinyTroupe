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
        'content': 'click #some-button'
    }

    mock_client.predict.return_value = {"status": "success"}

    result = tool.process_action(mock_agent, action)
    assert result is True
    mock_client.predict.assert_called_with(api_name="/click", use_persistent=True, selector="#some-button")
    mock_agent.think.assert_called_with("Successfully performed action 'click'.")

def test_computer_use_tool_fill_action(mock_agent):
    """Test that ComputerUseTool correctly processes a fill action."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action = {
        'type': 'computer_use',
        'content': 'fill #username John Doe'
    }

    mock_client.predict.return_value = {"status": "success"}

    result = tool.process_action(mock_agent, action)
    assert result is True
    mock_client.predict.assert_called_with(api_name="/fill", use_persistent=True, selector="#username", text="John Doe")
    mock_agent.think.assert_called_with("Successfully performed action 'fill'.")

def test_computer_use_tool_press_key_action(mock_agent):
    """Test that ComputerUseTool correctly processes a press_key action."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action = {
        'type': 'computer_use',
        'content': 'press_key a b c'
    }

    mock_client.predict.return_value = "key pressed"

    result = tool.process_action(mock_agent, action)
    assert result is True
    assert mock_client.predict.call_count == 3
    mock_agent.think.assert_called_with("Successfully performed action 'press_key'.")

def test_computer_use_tool_no_client_provided(mock_agent):
    """Test that ComputerUseTool instantiates its own client when none is provided."""
    with patch('tinytroupe.tools.computer_use.Client') as mock_client_constructor:
        mock_client_instance = MagicMock()
        mock_client_instance.predict.return_value = {"status": "success"}
        mock_client_constructor.return_value = mock_client_instance

        tool = ComputerUseTool()
        action = {
            'type': 'computer_use',
            'content': 'click #some-button'
        }

        result = tool.process_action(mock_agent, action)
        assert result is True
        mock_client_instance.predict.assert_called_with(api_name="/click", use_persistent=True, selector="#some-button")
        mock_agent.think.assert_called_with("Successfully performed action 'click'.")

import pytest
import json
from unittest.mock import MagicMock, patch
from tinytroupe.tools.sequential_thinking import SequentialThinkingTool
from tinytroupe.tools.computer_use import ComputerUseTool

@pytest.fixture
def mock_agent():
    """Fixture for a mock agent."""
    agent = MagicMock()
    agent.name = "TestAgent"
    agent.think = MagicMock()
    agent.store_in_memory = MagicMock()
    agent.iso_datetime = MagicMock()
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

def test_computer_use_tool_click_action(mock_agent):
    """Test that ComputerUseTool correctly processes a click action with JSON input."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action_content = {
        "action_name": "click",
        "selector": "#some-button",
        "url": "https://example.com"
    }
    action = {
        'type': 'computer_use',
        'content': json.dumps(action_content)
    }

    mock_client.predict.return_value = {"status": "success"}

    result = tool.process_action(mock_agent, action)
    assert result is True
    mock_client.predict.assert_called_with(api_name="/click", use_persistent=True, selector="#some-button", url="https://example.com")
    mock_agent.think.assert_called_with("Successfully performed action 'click'.")

def test_computer_use_tool_fill_action(mock_agent):
    """Test that ComputerUseTool correctly processes a fill action with JSON input."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action_content = {
        "action_name": "fill",
        "selector": "#username",
        "text": "John Doe",
        "url": "https://example.com"
    }
    action = {
        'type': 'computer_use',
        'content': json.dumps(action_content)
    }

    mock_client.predict.return_value = {"status": "success"}

    result = tool.process_action(mock_agent, action)
    assert result is True
    mock_client.predict.assert_called_with(api_name="/fill", use_persistent=True, selector="#username", text="John Doe", url="https://example.com")
    mock_agent.think.assert_called_with("Successfully performed action 'fill'.")

def test_computer_use_tool_press_key_action(mock_agent):
    """Test that ComputerUseTool correctly processes a press_key action with JSON input."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action_content = {
        "action_name": "press_key",
        "keys": ["a", "b", "c"],
        "url": "https://example.com"
    }
    action = {
        'type': 'computer_use',
        'content': json.dumps(action_content)
    }

    mock_client.predict.return_value = "key pressed"

    result = tool.process_action(mock_agent, action)
    assert result is True
    assert mock_client.predict.call_count == 3
    mock_agent.think.assert_called_with("Successfully performed action 'press_key'.")

def test_computer_use_tool_navigate_action(mock_agent):
    """Test that ComputerUseTool correctly processes a navigate action."""
    mock_client = MagicMock()
    tool = ComputerUseTool(client=mock_client)
    action_content = {
        "action_name": "navigate",
        "url": "https://example.com"
    }
    action = {
        'type': 'computer_use',
        'content': json.dumps(action_content)
    }

    mock_client.predict.return_value = {"status": "success", "page_info": "Page loaded"}

    result = tool.process_action(mock_agent, action)
    assert result is True
    mock_client.predict.assert_called_with(api_name="/browse_and_extract", use_persistent=True, url="https://example.com")
    # Let's check the think message separately to avoid brittleness with the page_info content
    assert "Successfully performed action 'navigate'." in mock_agent.think.call_args[0][0]

def test_computer_use_tool_no_client_provided(mock_agent):
    """Test that ComputerUseTool instantiates its own client when none is provided."""
    with patch('tinytroupe.tools.computer_use.Client') as mock_client_constructor:
        mock_client_instance = MagicMock()
        mock_client_instance.predict.return_value = {"status": "success"}
        mock_client_constructor.return_value = mock_client_instance

        tool = ComputerUseTool()
        action_content = {
            "action_name": "click",
            "selector": "#some-button",
            "url": "https://example.com"
        }
        action = {
            'type': 'computer_use',
            'content': json.dumps(action_content)
        }

        result = tool.process_action(mock_agent, action)
        assert result is True
        mock_client_instance.predict.assert_called_with(api_name="/click", use_persistent=True, selector="#some-button", url="https://example.com")
        mock_agent.think.assert_called_with("Successfully performed action 'click'.")

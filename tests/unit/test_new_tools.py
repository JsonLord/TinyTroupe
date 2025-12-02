import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tinytroupe.tools.sequential_thinking import SequentialThinkingTool
from tinytroupe.tools.computer_use import ComputerUseTool

@pytest.fixture
def mock_agent():
    """Fixture for a mock agent."""
    agent = MagicMock()
    agent.name = "TestAgent"
    agent.think = MagicMock()
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

        result = tool._process_action(mock_agent, action)
        assert result is True
        mock_agent.think.assert_called_with("Thought processed. History length: 1")

@patch('tinytroupe.tools.computer_use.Agent', new_callable=MagicMock)
@patch('tinytroupe.tools.computer_use.Browser', new_callable=MagicMock)
@patch('tinytroupe.tools.computer_use.ChatBrowserUse', new_callable=MagicMock)
def test_computer_use_tool_process_action(mock_chat, mock_browser, mock_agent_class, mock_agent):
    """Test that ComputerUseTool correctly processes a computer_use action."""
    tool = ComputerUseTool()
    task_description = "Go to example.com and find the contact email."
    action = {
        'type': 'computer_use',
        'content': f'{{"task": "{task_description}"}}'
    }

    # Mock the async run method
    mock_run_history = MagicMock()
    mock_run_history.final_result.return_value = "Contact email is contact@example.com"

    mock_agent_instance = MagicMock()
    mock_agent_instance.run = AsyncMock(return_value=mock_run_history)
    mock_agent_class.return_value = mock_agent_instance

    result = tool._process_action(mock_agent, action)

    assert result is True
    mock_agent_class.assert_called_with(
        task=task_description,
        llm=mock_chat.return_value,
        browser=mock_browser.return_value,
        use_vision=True,
        use_thinking=False,
        flash_mode=False,
        highlight_elements=False
    )
    mock_agent_instance.run.assert_awaited_once()
    mock_agent.think.assert_called_with("Successfully executed browser task.")
    mock_agent.memory.add_observation.assert_called_with("Browser task result: Contact email is contact@example.com")

def test_computer_use_tool_missing_task(mock_agent):
    """Test that ComputerUseTool handles a missing task gracefully."""
    tool = ComputerUseTool()
    action = {
        'type': 'computer_use',
        'content': '{"other_param": "value"}'
    }

    result = tool._process_action(mock_agent, action)
    assert result is False
    mock_agent.think.assert_called_with("Error: 'task' is a required parameter for the computer_use tool.")

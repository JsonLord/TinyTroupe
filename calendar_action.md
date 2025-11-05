# Implementing a Calendar Action in TinyTroupe

A common point of inquiry is about a "calendar action" for scheduling and time management within TinyTroupe.

**To be clear, there is no built-in calendar functionality or a `CALENDAR` action in the current version of the framework.**

However, integrating such a feature is a natural extension of the TinyTroupe architecture and would enable significantly more complex and realistic simulations. This document outlines a high-level plan for how a calendar feature could be implemented.

## High-Level Implementation Plan

The implementation can be broken down into four main components: a `CalendarTool`, a new `CALENDAR` action type, a `SchedulingFaculty` for agents, and integration into the `TinyWorld` environment.

### 1. Create a `CalendarTool` Class
The first step is to create a standalone tool that handles all the core scheduling logic. This keeps the implementation clean and separates the tool's functionality from the agent's decision-making process.

- **Responsibilities:**
  - `create_event(title, time, duration, attendees)`: Adds a new event to a shared calendar.
  - `get_schedule(agent_name, date)`: Returns the schedule for a specific agent on a given day.
  - `find_free_slot(attendees, duration)`: A more advanced function that finds a common availability for a list of agents.
  - `cancel_event(event_id)`: Removes an event from the calendar.

### 2. Define a New `CALENDAR` Action Type
Agents need a way to express their intent to interact with the calendar. This is done by defining a new action type.

- **Structure:** The action's `payload` would contain the specific command and its parameters.

- **Example `CALENDAR` Actions:**

  - **To create an event:**
    ```json
    {
      "type": "CALENDAR",
      "content": "Scheduling a project sync-up.",
      "payload": {
        "command": "create_event",
        "title": "Project Sync-up",
        "time": "2025-11-06T15:00:00",
        "attendees": ["Lisa", "Oscar"]
      }
    }
    ```
  - **To check a schedule:**
    ```json
    {
      "type": "CALENDAR",
      "content": "I need to check my schedule for tomorrow.",
      "payload": {
        "command": "get_schedule",
        "agent_name": "Lisa",
        "date": "2025-11-07"
      }
    }
    ```

### 3. Implement a `SchedulingFaculty`
To give agents the "skill" of using the calendar, you would create a `MentalFaculty`. This faculty would provide the agent with the necessary prompts and understanding to use the `CALENDAR` action intelligently.

- **Responsibilities:**
  - **Extend Agent Prompts:** The faculty would inject information into the agent's system prompt, explaining what the `CALENDAR` action is and how to use it with different payloads.
  - **Process Calendar Stimuli:** It would help the agent understand calendar-related stimuli, such as `EVENT_CONFIRMATION` or `SCHEDULE_CONFLICT`.

### 4. Integrate with the `TinyWorld` Environment
Finally, the `TinyWorld` environment needs to be taught how to handle the new `CALENDAR` action.

- **Logic:**
  1.  In the `_handle_actions` method of `TinyWorld`, add a new condition to check for `action["type"] == "CALENDAR"`.
  2.  When a `CALENDAR` action is detected, the environment calls the appropriate method on the `CalendarTool` instance (e.g., `calendar_tool.create_event(...)`).
  3.  After the tool executes, the `TinyWorld` should generate a new stimulus and send it back to the agent who initiated the action (and potentially other involved agents).

- **Example Stimuli:**
  - **Success:**
    ```json
    { "type": "CALENDAR_CONFIRMATION", "content": "The event 'Project Sync-up' has been successfully scheduled for 3 PM." }
    ```
  - **Failure:**
    ```json
    { "type": "CALENDAR_CONFLICT", "content": "Could not schedule event. Oscar is already booked at that time." }
    ```

By following this plan, you can create a robust and well-integrated scheduling system that greatly expands the capabilities of your TinyTroupe simulations.

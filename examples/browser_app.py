import gradio as gr
import sys
import os
import re

# Add the root directory to the Python path to allow imports from tinytroupe
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tinytroupe.agent.tiny_person import TinyPerson
from tinytroupe.agent.browser_faculty import BrowserFaculty
# The following import is needed to initialize some example builders, etc.
import tinytroupe.examples

def strip_rich_markup(text):
    """
    A simple function to remove rich-style markup tags like [bold] or [red] from a string.
    """
    return re.sub(r'\[/?.*?\]', '', text)

def run_agent(name, age, occupation, url, task):
    """
    This function creates a TinyPerson with browser capabilities, runs it on a given task,
    and captures the output for display in the Gradio interface.
    """
    # Clear any previously created agents to avoid name clashes
    TinyPerson.clear_agents()

    # 1. Create the persona
    persona = TinyPerson(name)
    persona.define("age", int(age))
    persona.define("occupation", {"title": occupation})

    # 2. Add the browser faculty to give the agent browsing capabilities
    browser_faculty = BrowserFaculty()
    persona.add_mental_faculty(browser_faculty)

    # 3. Prevent the agent from printing directly to the console
    TinyPerson.communication_display = False

    output_log = []

    # 4. Give the agent its initial instruction
    initial_instruction = (
        f"Your task is to go to {url} and {task}. "
        "Use the browser tools to navigate and interact with the page. "
        "Think step-by-step and use screenshots to help you see what's on the page."
    )

    # 5. Run the agent and capture its communications
    persona.listen(initial_instruction)
    comms = persona.pop_and_display_latest_communications()
    for comm in comms:
        output_log.append(strip_rich_markup(comm['rendering']))

    persona.act(until_done=True)
    comms = persona.pop_and_display_latest_communications()
    for comm in comms:
        output_log.append(strip_rich_markup(comm['rendering']))

    return "\n".join(output_log)

# Define the Gradio interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 TinyTroupe Browser Agent Demo")
    gr.Markdown(
        "This demo lets you create a `TinyPerson` persona and give it a task to perform on a website. "
        "The agent will use its browsing capabilities to try to complete the task."
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 1. Define the Persona")
            name_input = gr.Textbox(label="Name", value="Alex")
            age_input = gr.Number(label="Age", value=30)
            occupation_input = gr.Textbox(label="Occupation", value="Web Analyst")

            gr.Markdown("## 2. Define the Task")
            url_input = gr.Textbox(label="URL", placeholder="e.g., https://www.gradio.app/guides")
            task_input = gr.Textbox(label="Task", placeholder="e.g., Find the guide on 'Key Features'")

            run_button = gr.Button("🚀 Run Agent", variant="primary")

        with gr.Column(scale=2):
            gr.Markdown("## Agent Actions")
            output_display = gr.Textbox(
                label="Output Log",
                lines=20,
                interactive=False,
                placeholder="Agent's actions will appear here..."
            )

    # Connect the button to the agent function
    run_button.click(
        fn=run_agent,
        inputs=[name_input, age_input, occupation_input, url_input, task_input],
        outputs=output_display
    )

if __name__ == "__main__":
    demo.launch()

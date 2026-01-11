import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import gradio as gr
import json


from tinytroupe.factory import TinyPersonFactory
def generate_personas(business_description, customer_profile, num_personas):
    """
    Generates a list of TinyPerson instances based on the provided inputs.
    """
    try:
        # The number of personas needs to be an integer.
        num_personas = int(num_personas)

        # Create a factory instance with the user-provided context and customer profile.
        factory = TinyPersonFactory(
            context=business_description,
            sampling_space_description=customer_profile,
            total_population_size=num_personas
        )

        # Generate the specified number of personas.
        # We'll run this sequentially for simplicity in this environment.
        people = factory.generate_people(number_of_people=num_personas, parallelize=False)

        # Extract the persona data from each generated TinyPerson object.
        personas_data = [person._persona for person in people]

        # Return the data as a JSON object.
        return personas_data
    except Exception as e:
        # In case of an error, return a descriptive message.
        return {"error": str(e)}

with gr.Blocks() as demo:
    gr.Markdown("<h1>Tiny Persona Generator</h1>")
    with gr.Row():
        with gr.Column():
            business_description_input = gr.Textbox(label="What is your business about?", lines=5)
            customer_profile_input = gr.Textbox(label="Information about your customer profile", lines=5)
            num_personas_input = gr.Number(label="Number of personas to generate", value=1, minimum=1, step=1)
            generate_button = gr.Button("Generate Personas")
        with gr.Column():
            output_json = gr.JSON(label="Generated Personas")

    generate_button.click(
        fn=generate_personas,
        inputs=[business_description_input, customer_profile_input, num_personas_input],
        outputs=output_json,
        api_name="generate_personas"
    )

if __name__ == "__main__":
    demo.queue().launch()

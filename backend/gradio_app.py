import gradio as gr
from backend.services.tinytroupe_manager import tinytroupe_manager
from backend.services.persona_matcher import persona_matcher
from backend.core.job_registry import job_registry
import uuid
import time
import json

def manual_generate_personas(business_desc, cust_profile, num):
    job_id = str(uuid.uuid4())
    job_registry.create_job(job_id)

    # Run synchronously for Gradio interface demo (or we could poll, but blocks are simpler here)
    tinytroupe_manager.generate_personas_async(business_desc, cust_profile, int(num), job_id, job_registry)

    # Wait for completion (simple polling)
    while True:
        job = job_registry.get_job(job_id)
        if job["status"] in ["COMPLETED", "FAILED"]:
            break
        time.sleep(1)

    if job["status"] == "FAILED":
        return f"Error: {job.get('message')}"

    personas = job.get("results", {}).get("personas", [])
    return json.dumps(personas, indent=2)

def create_gradio_app():
    with gr.Blocks(title="TinyTroupe Admin") as app:
        gr.Markdown("# Admin Interface for Persona Generation")
        with gr.Row():
            with gr.Column():
                biz_desc = gr.Textbox(label="Business Description")
                cust_prof = gr.Textbox(label="Customer Profile")
                num_personas = gr.Number(label="Count", value=3)
                generate_btn = gr.Button("Generate Personas")
            with gr.Column():
                output_json = gr.JSON(label="Generated Personas")

        generate_btn.click(
            fn=manual_generate_personas,
            inputs=[biz_desc, cust_prof, num_personas],
            outputs=output_json
        )

    return app

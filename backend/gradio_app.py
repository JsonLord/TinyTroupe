import gradio as gr
from backend.services.tinytroupe_manager import tinytroupe_manager
from backend.services.persona_matcher import persona_matcher
from backend.core.job_registry import job_registry
import uuid
import time
import json
import logging

logger = logging.getLogger(__name__)

def manual_generate_personas(business_desc, cust_profile, num):
    job_id = str(uuid.uuid4())
    job_registry.create_job(job_id)

    # Run synchronously for Gradio interface demo
    tinytroupe_manager.generate_personas_async(business_desc, cust_profile, int(num), job_id, job_registry)

    # Wait for completion (simple polling)
    while True:
        job = job_registry.get_job(job_id)
        if job["status"] in ["COMPLETED", "FAILED"]:
            break
        time.sleep(1)

    if job["status"] == "FAILED":
        return {"Error": job.get('message')}

    personas = job.get("results", {}).get("personas", [])
    return personas

def run_simulation(sim_name, content_input, content_format, num_personas_sim, focus_group_id):
    job_id = str(uuid.uuid4())
    job_registry.create_job(job_id)

    # We mock fetch some personas for this UI interaction based on the count requested
    mock_personas_data = [{"name": f"Agent {i}_{job_id[:4]}", "occupation": "Reviewer"} for i in range(int(num_personas_sim))]

    tinytroupe_manager.run_simulation_async(
        job_id,
        content_input,
        mock_personas_data,
        content_format,
        {},
        job_registry
    )

    while True:
        job = job_registry.get_job(job_id)
        if job["status"] in ["COMPLETED", "FAILED"]:
            break
        time.sleep(1)

    if job["status"] == "FAILED":
        logger.error(f"Simulation failed: {job.get('message')}")
        return [], [], []

    results = job.get("results", {})
    dialogue = results.get("agent_dialogue", [])

    # Format for dataframe: ["persona_name", "opinion", "analysis", "implications"]
    df_data = []
    nodes = []
    edges = []

    for i, d in enumerate(dialogue):
        name = d.get("name", "Unknown")
        comment = d.get("comment", "")
        impact = d.get("impact_score", 0)

        # Add to DF
        df_data.append([
            name,
            comment,
            f"Impact: {impact}",
            "Strong agreement" if impact > 80 else "Mixed feelings"
        ])

        # Add to nodes
        nodes.append({
            "id": name,
            "label": name,
            "title": f"Impact: {impact}"
        })

        # Add edges randomly for mesh simulation
        if i > 0:
            edges.append({"from": nodes[0]["id"], "to": name})

    return df_data, nodes, edges, job_id

def create_gradio_app():
    with gr.Blocks(
        css=".big-input textarea { height: 300px !important; } #mesh-network-container { height: 600px; background: #101622; border-radius: 12px; }",
        title="UserSync AI Backend UI"
    ) as app:
        gr.HTML('<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>')
        gr.Markdown("# 🌐 UserSync Backend Administration & Simulation")

        current_sim_id = gr.State()

        with gr.Tabs():
            with gr.Tab("Simulation Dashboard"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📝 Content Input")
                        sim_name = gr.Textbox(label="Simulation Name", value="Test Simulation")
                        focus_group = gr.Dropdown(choices=["tech_founders_eu", "marketing_pros_us"], label="Focus Group", value="tech_founders_eu")
                        content_input = gr.Textbox(label="Content (Article, Idea, etc.)", lines=10, elem_classes="big-input")
                        content_format = gr.Dropdown(choices=["Article", "Product Idea", "Website"], label="Format", value="Article")
                        num_personas_sim = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="Number of Personas (Limit for HF)")
                        run_btn = gr.Button("🚀 Run Simulation", variant="primary")
                    with gr.Column(scale=2):
                        gr.Markdown("### 🕸️ Focus Group Network")
                        gr.HTML('<div id="mesh-network-container"></div>')
                        with gr.Accordion("Detailed Agent Profile", open=False):
                            detail_name = gr.Textbox(label="Name", interactive=False)
                            detail_json = gr.Code(label="Profile Information", language="json")

                gr.Markdown("### 📊 Simulation Analysis Results")
                analysis_table = gr.Dataframe(headers=["persona_name", "opinion", "analysis", "implications"], label="Aggregated Output")

            with gr.Tab("Persona Generator / Sync"):
                with gr.Row():
                    with gr.Column():
                        biz_desc = gr.Textbox(label="Business Description", lines=5)
                        cust_prof = gr.Textbox(label="Customer Profile", lines=5)
                        num_personas = gr.Number(label="Target Focus Group Size", value=3)
                        generate_btn = gr.Button("Evaluate & Generate Personas")
                    with gr.Column():
                        output_json = gr.JSON(label="Persona Generation / Match Output")

        nodes_state = gr.State([])
        edges_state = gr.State([])

        # Hidden elements for JS integration
        js_trigger = gr.Textbox(visible=False, elem_id="js_trigger_textbox")
        js_trigger_btn = gr.Button("trigger", visible=False, elem_id="js_trigger_btn")

        run_btn.click(
            fn=run_simulation,
            inputs=[sim_name, content_input, content_format, num_personas_sim, focus_group],
            outputs=[analysis_table, nodes_state, edges_state, current_sim_id]
        ).then(
            fn=None, inputs=[nodes_state, edges_state], outputs=None,
            js="""(nodes, edges) => {
                const container = document.getElementById('mesh-network-container');
                if(!container) return;
                const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
                const options = {
                    nodes: { shape: 'dot', size: 25, font: { color: '#fff', size: 16 }, color: { background: '#135bec', border: '#fff' }, shadow: true },
                    edges: { color: 'rgba(19,91,236,0.4)', width: 2, smooth: { type: 'continuous' } },
                    physics: { enabled: true, stabilization: false, barnesHut: { gravitationalConstant: -3000 } }
                };
                const network = new vis.Network(container, data, options);
                network.on("click", (params) => {
                    if(params.nodes.length) {
                        const node = nodes.find(n => n.id === params.nodes[0]);
                        const trigger = document.getElementById('js_trigger_textbox').querySelector('input');
                        trigger.value = node.id;
                        trigger.dispatchEvent(new Event('input'));
                        document.getElementById('js_trigger_btn').click();
                    }
                });
            }"""
        )

        def mock_persona_details(name):
            return name, json.dumps({"description": f"Details for {name} currently engaged in simulation."}, indent=2)

        js_trigger_btn.click(mock_persona_details, inputs=[js_trigger], outputs=[detail_name, detail_json])

        generate_btn.click(
            fn=manual_generate_personas,
            inputs=[biz_desc, cust_prof, num_personas],
            outputs=output_json
        )

    return app

if __name__ == "__main__":
    app = create_gradio_app()
    app.launch()

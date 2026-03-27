import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import gradio as gr
from tinytroupe.examples import create_lisa_the_data_scientist

app = FastAPI(
    title="UserSync API",
    description="Backend built with FastAPI and Gradio, designed for parallel focus group simulations using Microsoft's tinytroupe library.",
    version="1.0.0",
    docs_url="/api-docs"
)

@app.get("/health")
async def health_check():
    """Health check endpoint to confirm the app is running."""
    return JSONResponse(content={"status": "ok"})

@app.post("/predict")
async def predict(request: Request):
    """Run model inference by simulating a conversation with a TinyPerson."""
    data = await request.json()
    text = data.get("text", "")

    if not text:
        return JSONResponse(content={"error": "No text provided"}, status_code=400)

    # Create Lisa from tinytroupe examples
    lisa = create_lisa_the_data_scientist()

    # Send the speech to Lisa and get the actions
    actions = lisa.listen_and_act(text, return_actions=True)

    # actions could be a list, or an object, we serialize it to string as the prediction
    # or extract the content from TALK action
    prediction = ""

    if actions and isinstance(actions, list):
        for action in actions:
            if isinstance(action, dict) and action.get("action", {}).get("type") == "TALK":
                prediction += action.get("action", {}).get("content", "") + "\n"

    if not prediction:
        prediction = f"Lisa processed your request: {text}"

    return JSONResponse(content={"prediction": prediction})

# Mount a simple Gradio interface as required
def greet(name):
    return "Hello " + name + "!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")
app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

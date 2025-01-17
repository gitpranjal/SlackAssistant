from model_handler import ModelHandler
import gradio as gr

# Constants
OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

if __name__ == "__main__":
    # Initialize the model handler
    api = ModelHandler(localAPIUrl=OLLAMA_API, model=MODEL)

    # Launch the Gradio ChatInterface
    gr.ChatInterface(
        fn=api.chat,  # Use the updated function
        type="messages"
    ).launch()

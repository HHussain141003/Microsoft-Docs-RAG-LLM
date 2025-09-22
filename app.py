import gradio as gr
from model import generate_answer

def chat_interface(message, history):
    """Chat interface function for Gradio."""
    try:
        response = generate_answer(message)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# Create the interface
demo = gr.ChatInterface(
    fn=chat_interface,
    title="Microsoft Learn RAG Assistant",
    description="Ask questions about Microsoft technologies (Power Platform, Azure, Microsoft 365)",
    examples=[
        "How do I create a Power App?",
        "What is Azure Active Directory?",
        "How to set up SharePoint Online?",
        "What are Power Automate flows?",
    ],
    theme="soft"
)

if __name__ == "__main__":
    demo.launch(share=True)

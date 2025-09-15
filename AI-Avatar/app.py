from dotenv import load_dotenv
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import random

from openai import AzureOpenAI
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")


load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = AzureOpenAI(api_key=azure_openai_api_key, azure_endpoint=azure_openai_endpoint, api_version="2024-10-21")
        self.name = "Vikash Vishwakarma"
        reader = PdfReader("me/backend_SDE.pdf")
        self.resume = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.resume += text
        with open("me/Experence.txt", "r", encoding="utf-8") as f:
            self.experence = f.read()


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a experence of {self.name}'s background and Resume profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Experence:\n{self.experence}\n\n## Resume Profile:\n{self.resume}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="r360-gpt-4o", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

def create_enhanced_interface():
    """Create an enhanced Gradio interface with better UI/UX"""
    
    # Sample questions for quick interaction
    suggested_questions = [
        "What is your educational background?",
        "How many years of experience do you have?",
        "What makes you passionate about software engineering?",
        "Can you share your experience with Spring Boot?",
        "What cloud technologies have you worked with?",
        "What is your experience with Java and backend development?",
        "Can you tell me about your AI and machine learning projects?",
        "What frameworks are you proficient in?",
        "Can you describe your experience with microservices?",
        "What's your experience with databases like PostgreSQL and MongoDB?",
        "Tell me about your customer automation project with SDLC"
    ]
    
    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
    }
    #header-section {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    }
    #chatbot-container {
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        background: white;
    }
    .suggested-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 25px;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 5px;
        font-size: 14px;
    }
    .suggested-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    #question-section {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
    }
    .footer-section {
        text-align: center;
        margin-top: 30px;
        color: white;
        font-size: 14px;
    }
    """
    
    # Initialize the Me class
    me = Me()
    
    with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="Vikash Vishwakarma - Career Chatbot") as demo:
        with gr.Column(elem_classes="main-container"):
            # Header Section
            with gr.Column(elem_id="header-section"):
                gr.Markdown(
                    """
                    # 👨‍💻 Vikash Vishwakarma - Career Conversation Bot
                    
                    ### Welcome! I'm here to discuss my professional journey and expertise
                    
                    🎯 **5+ Years of Experience** in Backend Development, AI/ML, and Enterprise Solutions  
                    💼 **Specializing in:** Java, Spring Boot, Microservices, AI Integration, and Cloud Technologies  
                    🚀 **Passionate about:** Building scalable solutions and leading cross-functional teams
                    
                    Feel free to ask me anything about my experience, skills, or career journey!
                    
                    ---
                    
                    ### 📬 **Connect With Me:**
                    
                    📧 **Email:** [vikashsharma190@gmail.com](mailto:vikashsharma190@gmail.com)  
                    💼 **LinkedIn:** [linkedin.com/in/vikashvishwakarma190](https://www.linkedin.com/in/vikashvishwakarma190/)  
                    🐙 **GitHub:** [github.com/vikash-sharma-190](https://github.com/vikash-sharma-190)  
                    📱 **Phone:** +91 7814455206
                    """,
                    elem_classes="header-content"
                )
            
            # Chat Interface
            with gr.Column(elem_id="chatbot-container"):
                chatbot = gr.Chatbot(
                    value=[{"role": "assistant", "content": "Hello! I'm Vikash Vishwakarma. Welcome to my career conversation bot! 👋\n\nI'm a software engineer with 5+ years of experience in backend development, AI/ML, and enterprise solutions. I'd be happy to discuss:\n\n• My technical expertise and project experience\n• Skills in Java, Spring Boot, and microservices\n• AI and automation projects I've worked on\n• Career goals and opportunities\n\nFeel free to ask me anything or try one of the suggested questions below!"}],
                    height=500,
                    type="messages",
                    show_label=False,
                    avatar_images=(None, "https://ui-avatars.com/api/?name=VV&background=667eea&color=fff&size=128"),
                    render_markdown=True
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Your Message",
                        placeholder="Type your question here... (e.g., 'What is your experience with Java?')",
                        lines=2,
                        max_lines=4,
                        show_label=False,
                        container=False,
                        scale=4
                    )
                    submit_btn = gr.Button(
                        "Ask Vikash 📤",
                        variant="primary",
                        scale=1
                    )
                
                clear_btn = gr.ClearButton(
                    [msg, chatbot],
                    value="🔄 Start New Conversation"
                )
            
            # Suggested Questions Section
            with gr.Column(elem_id="question-section"):
                gr.Markdown("### 💡 **Suggested Questions** - Click any to get started!")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("**🎓 Background & Education**")
                        for q in suggested_questions[7:9]:
                            gr.Button(
                                q,
                                elem_classes="suggested-btn",
                                size="sm"
                            ).click(
                                fn=lambda x=q: x,
                                outputs=msg
                            )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("**💻 Technical Skills**")
                        for q in suggested_questions[0:3]:
                            gr.Button(
                                q,
                                elem_classes="suggested-btn",
                                size="sm"
                            ).click(
                                fn=lambda x=q: x,
                                outputs=msg
                            )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("**🚀 Projects & Experience**")
                        for q in suggested_questions[4:7]:
                            gr.Button(
                                q,
                                elem_classes="suggested-btn",
                                size="sm"
                            ).click(
                                fn=lambda x=q: x,
                                outputs=msg
                            )
                
                # Random question generator
                def get_random_question():
                    return random.choice(suggested_questions)
                
                with gr.Row():
                    random_btn = gr.Button(
                        "🎲 Surprise Me with a Random Question",
                        elem_classes="suggested-btn",
                        variant="secondary"
                    )
                    random_btn.click(
                        fn=get_random_question,
                        outputs=msg
                    )
            
            # Tips Section
            with gr.Accordion("📚 Tips for Better Conversation", open=False):
                gr.Markdown(
                    """
                    - **Be specific**: Ask about particular technologies or projects for detailed responses
                    - **Career focused**: Questions about professional experience get the best answers
                    - **Get in touch**: If you're interested in collaboration, don't hesitate to share your contact
                    - **Technical depth**: Feel free to dive deep into technical topics
                    - **Project details**: Ask about specific projects mentioned in my experience
                    """
                )
            
            # Footer
            gr.HTML(
                """
                <div class="footer-section">
                    <p>💼 Open to exciting opportunities | 📧 Let's connect and discuss potential collaborations</p>
                    <p>Built with ❤️ using Gradio and Azure OpenAI</p>
                </div>
                """
            )
        
        # Event handlers
        def respond(message, chat_history):
            bot_message = me.chat(message, chat_history)
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": bot_message})
            return "", chat_history
        
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        submit_btn.click(respond, [msg, chatbot], [msg, chatbot])
    
    return demo

if __name__ == "__main__":
    demo = create_enhanced_interface()
    demo.launch()
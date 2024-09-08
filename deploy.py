import os
import json
import re
import time
import threading
import streamlit as st
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
HISTORY_FILE = "conversation_history.json"

# Reset conversation history
def reset_conversation_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)

reset_conversation_history()

# Load conversation history
def load_conversation_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as json_file:
                return json.load(json_file)
    except IOError as e:
        st.error(f"Error loading conversation history: {e}")
    return []

conversation_history = load_conversation_history()

# Define prompts
prompt1 = ChatPromptTemplate.from_messages(
    [
        ("system", 
         "You are an Indian Railways complaint help assistant named Sahayika. "
         "Based on the user's complaint, predict the department, urgency level between 1 to 5, and a one-line context of the problem. "
         "The departments are: ['technical', 'medical', 'cleaning', 'security', 'mechanical', 'IRCTC', 'Railway police force']. "
         "Respond to the user with a relieving and a logical message towards the problem and the response should be in points. "
         "Also, return a JSON with department, urgency, sentiment, and context."),
        ("user", "Complaint: {question}")
    ]
)
prompt2 = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an Indian Railways complaint help assistant named Sahayika. Just return things that help the user calm down and present facts."),
        ("user", "Complaint: {question}")
    ]
)

llm = Ollama(model="llama3:8b")
output_parser = StrOutputParser()

chain1 = prompt1 | llm | output_parser
chain2 = prompt2 | llm | output_parser

# Parse output to extract JSON
def parse_output(output):
    json_match = re.search(r'\{(?:[^{}"]|"[^"]*"|\d+|true|false|null)+\}', output)
    if json_match:
        json_str = json_match.group()
        try:
            parsed_info = json.loads(json_str)
            return parsed_info
        except json.JSONDecodeError as e:
            st.error(f"Error parsing JSON: {e}")
            return {}
    else:
        st.warning("No JSON found in the output.", icon="⚠️")
        return {}

# Store conversation history in a JSON file
def store_conversation_in_json(conversation_history):
    try:
        with open(HISTORY_FILE, "w") as json_file:
            json.dump(conversation_history, json_file, indent=4)
        st.success("Conversation history successfully saved.")
    except IOError as e:
        st.error(f"Error saving conversation history: {e}")

# Handle input and generate responses
def handle_input(input_text):
    output1 = chain1.invoke({'question': input_text})
    output2 = chain2.invoke({'question': input_text})
    parsed_output1 = parse_output(output1)
    if parsed_output1:
        conversation_history.append({
            "question": input_text,
            "response": parsed_output1
        })
        store_conversation_in_json(conversation_history)
    else:
        st.warning("No valid response to store.", icon="⚠️")
    return output2

# Display response word by word, with points starting on a new line
def display_response_word_by_word(response):
    response_container = st.empty()
    
    # Regular expression to split points:
    # Matches patterns like "1.", "2.", or bullet points such as "•" or "-"
    points = re.split(r'(\d+\.\s|•\s|-{1,2}\s)', response)

    displayed_text = ""
    current_point = ""
    for i, part in enumerate(points):
        # Reconstruct the point: If it's a number or bullet, combine it with the next part
        if re.match(r'\d+\.\s|•\s|-{1,2}\s', part):
            current_point = part  # This is the bullet or numbered prefix
        else:
            current_point += part.strip()  # Combine with the next content after the bullet or number
            displayed_text += current_point + "\n"  # Add the full point and a newline
            current_point = ""  # Reset for the next point
        
        formatted_text = f"""
            <div style="line-height: 1.8;">{displayed_text}</div>
        """
        response_container.markdown(formatted_text, unsafe_allow_html=True)
        time.sleep(0.05)  # Simulate typing effect

st.title("Sahayika ")
st.write("Enter your complaint and Sahayika will assist you!")
input_text = st.text_input("Enter your complaint here")

if st.button("Submit"):
    if input_text:
        reply = handle_input(input_text)
        display_response_word_by_word(reply)
    else:
        st.warning("Please enter a complaint.", icon="⚠️")

# Watchdog Integration

# Create a list to store file events
event_logs = []

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        event_logs.append(f'Modified: {event.src_path}')
    
    def on_created(self, event):
        event_logs.append(f'Created: {event.src_path}')
    
    def on_deleted(self, event):
        event_logs.append(f'Deleted: {event.src_path}')
    
    def on_moved(self, event):
        event_logs.append(f'Moved: {event.src_path} to {event.dest_path}')

def start_watchdog(path="."):
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Run Watchdog in a background thread
def run_watchdog_in_background():
    thread = threading.Thread(target=start_watchdog, args=(".",))
    thread.start()

# Start the file system monitoring when the app runs
st.sidebar.header("File System Monitor")
if st.sidebar.button("Start Monitoring"):
    run_watchdog_in_background()
    st.sidebar.success("Monitoring started!")

# Display file system events
st.sidebar.subheader("File Events")
if event_logs:
    for log in event_logs:
        st.sidebar.write(log)

# Sidebar with conversation history and image
image = Image.open('unnamed.png')
resized_image = image.resize((120, 120))

with st.sidebar:
    st.image(resized_image, caption="Sahayika - Your Assistant", use_column_width=False)
    st.header("Conversation History")
    if conversation_history:
        for i, entry in enumerate(conversation_history):
            response = entry.get("response", {})
            context = response.get("context", "No context available")
            st.write(f"Complaint {i+1}: {entry['question']}")
            st.write(f"Context: {context}")  
            st.write("---")
    else:
        st.write("No conversation history yet.")

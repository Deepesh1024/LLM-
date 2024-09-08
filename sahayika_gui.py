import os
import json
import re
import time  
import streamlit as st
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
HISTORY_FILE = "conversation_history.json"
def reset_conversation_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)

reset_conversation_history()
def load_conversation_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as json_file:
                return json.load(json_file)
    except IOError as e:
        st.error(f"Error loading conversation history: {e}")
    return []

conversation_history = load_conversation_history()
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
def store_conversation_in_json(conversation_history):
    try:
        with open(HISTORY_FILE, "w") as json_file:
            json.dump(conversation_history, json_file, indent=4)
        st.success("Conversation history successfully saved.")
    except IOError as e:
        st.error(f"Error saving conversation history: {e}")
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
def display_response_word_by_word(response):
    response_container = st.empty()
    points = re.split(r'(\d+\.\s|•\s|-{1,2}\s)', response)
    displayed_text = ""
    current_point = ""
    for i, part in enumerate(points):
        if re.match(r'\d+\.\s|•\s|-{1,2}\s', part):
            current_point = part  
        else:
            current_point += part.strip()  
            displayed_text += current_point + "\n"  
            current_point = "" 
        formatted_text = f"""
            <div style="line-height: 1.8;">{displayed_text}</div>
        """
        response_container.markdown(formatted_text, unsafe_allow_html=True)
        time.sleep(0.05)  
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
def set_input_text(value):
    st.session_state.input_text = value
st.title("Sahayika")
st.write("Enter your complaint and Sahayika will assist you!")
col1, col2, col3,   = st.columns(3)

with col1:
    if st.button("Unclean Coach", key="unclean_coach"):
        set_input_text("The coach is very dirty and the cleaning staff is unresponsive.")
with col2:
    if st.button("No medical assistance", key="no_medical_assistance"):
        set_input_text("I am feeling unwell and there is no medical staff available on the train.")
with col3:
    if st.button("Sexual Disrespect", key="sexual_harassment"):
        set_input_text("Facing issues that concerns my dignity and sexual disrespect or misbehave.")
input_text = st.text_input("Enter your complaint here", value=st.session_state.input_text)
if st.button("Submit", key="submit"):
    if input_text:
        reply = handle_input(input_text)
        display_response_word_by_word(reply)
    else:
        st.warning("Please enter a complaint.", icon="⚠️")
from PIL import Image
image = Image.open('unnamed.png')
resized_image = image.resize((120,120))
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

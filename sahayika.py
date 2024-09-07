import os
import json
import re
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
conversation_history = []
prompt1 = ChatPromptTemplate.from_messages(
    [
        ("system", 
         "You are an Indian Railways complaint help assistant named Sahayika. "
         "Based on the user's complaint, predict the department, urgency level between 1 to 5, and a one-line context of the problem. "
         "The departments are: ['technical', 'medical', 'cleaning', 'security', 'mechanical', 'IRCTC', 'Railway police force']. "
         "Respond to the user with a relieving and a logical message towards the problem. Also, return a JSON with department, urgency, sentiment, and context."),
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
            print(f"Error parsing JSON: {e}")
            return {}
    else:
        print("No JSON found in the output.")
        return {}

def store_conversation_in_json(conversation_history):
    try:
        with open("conversation_history.json", "w") as json_file:
            json.dump(conversation_history, json_file, indent=4)
        print("Conversation history successfully saved.")
    except IOError as e:
        print(f"Error saving conversation history: {e}")

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
        print("No valid response to store.")

    return output2

if __name__ == "__main__":
    while True:
        input_text = input("Enter your complaint: ")
        if input_text.lower() == "exit":
            break
        reply = handle_input(input_text)
        print(reply)

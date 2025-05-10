#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from crewai import Agent, Task, Crew, LLM
from dotenv import load_dotenv
import json
import os
import whisper
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

load_dotenv()


def transcribe_audio(audio_path):
    model = whisper.load_model("medium")  # Or use "small", "medium" if you want better quality
    result = model.transcribe(audio_path)
    return result["text"]
#LLM
llm = LLM(
    provider="gemini",  # Use Gemini directly, not through LangChain
    model=os.getenv("MODEL", "gemini-1.5-flash"),
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)
# Agents
mood_agent = Agent(
    role="Mood Detector",
    goal="Understand user's emotional tone from journal input",
    backstory="A compassionate AI designed to detect and understand human emotions based on journal text.",
    llm=llm  # Changed from mood_llm
)

coach_agent = Agent(
    role="Reflection Coach",
    goal="Encourage user to explore their emotions",
    backstory="A thoughtful AI that guides users through introspection and emotional growth.",
    llm=llm  # Changed from coach_llm
)

logger_agent = Agent(
    role="Journal Logger",
    goal="Format and log mood + reflection as structured JSON",
    backstory="A helpful assistant that securely logs emotional reflections for personal growth.",
    llm=llm  # Changed from logger_llm
)

audio_path = "meme.wav"
text = transcribe_audio(audio_path)

# Tasks
task1 = Task(
    agent=mood_agent,
    description="Analyze the user's journal input and detect emotional tone.",
    expected_output="Mood label (e.g., 'anxious') and confidence score.",
    input=text
)

task2 = Task(
    agent=coach_agent,
    description="Based on the detected mood, ask the user personalized reflection questions.",
    expected_output="A list of 2–3 introspective prompts encouraging emotional reflection.",
    depends_on=[task1]
)

task3 = Task(
    agent=logger_agent,
    description="Take the detected mood and user responses to create a structured journal entry.",
    expected_output="A JSON-formatted journal entry containing mood, confidence, and reflections.",
    depends_on=[task2]
)


def run(journal_text):
    try:
        crew = Crew(
            agents=[mood_agent, coach_agent, logger_agent],
            tasks=[task1, task2, task3]
        )
        output = crew.kickoff()
        print(output)
        
        # Extract the JSON data from the raw output
        formatted_output = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "mood": "Unknown",
            "confidence": 0.5,
            "reflections": []
        }
        
        # Check if we have output data
        if hasattr(output, 'dict') and callable(output.dict):
            output_dict = output.dict()
            
            # Try to extract the journal entry from the raw field
            if 'raw' in output_dict and output_dict['raw']:
                try:
                    # The raw field contains a JSON string with markdown code blocks
                    raw_text = output_dict['raw']
                    # Extract JSON from markdown code block if present
                    if '```json' in raw_text and '```' in raw_text.split('```json', 1)[1]:
                        json_text = raw_text.split('```json', 1)[1].split('```', 1)[0].strip()
                        journal_data = json.loads(json_text)
                        
                        # Update the formatted output with the extracted data
                        #if 'date' in journal_data:
                            #formatted_output['date'] = journal_data['date']
                        if 'mood' in journal_data:
                            formatted_output['mood'] = journal_data['mood']
                        if 'confidence' in journal_data:
                            formatted_output['confidence'] = journal_data['confidence']
                        if 'reflections' in journal_data:
                            # Handle different reflection formats
                            if isinstance(journal_data['reflections'], dict):
                                # Convert dict to list of prompt/response pairs
                                reflections_list = []
                                for key, value in journal_data['reflections'].items():
                                    if isinstance(value, dict):
                                        # Handle nested dict
                                        sub_reflections = []
                                        for sub_key, sub_value in value.items():
                                            sub_reflections.append({
                                                "prompt": sub_key,
                                                "response": sub_value
                                            })
                                        reflections_list.append({
                                            "prompt": key,
                                            "response": sub_reflections
                                        })
                                    else:
                                        reflections_list.append({
                                            "prompt": key,
                                            "response": value
                                        })
                                formatted_output['reflections'] = reflections_list
                            elif isinstance(journal_data['reflections'], list):
                                formatted_output['reflections'] = journal_data['reflections']
                except Exception as e:
                    print(f"Error parsing raw JSON: {e}")
            
            # If we still don't have reflections, try the tasks output
            if not formatted_output['reflections'] and 'tasks_output' in output_dict:
                if len(output_dict['tasks_output']) >= 3:
                    task3_output = output_dict['tasks_output'][2]
                    if 'raw' in task3_output:
                        try:
                            raw_text = task3_output['raw']
                            if '```json' in raw_text and '```' in raw_text.split('```json', 1)[1]:
                                json_text = raw_text.split('```json', 1)[1].split('```', 1)[0].strip()
                                journal_data = json.loads(json_text)
                                
                                # Update formatted output if needed
                                if 'date' in journal_data and formatted_output['date'] == datetime.now().strftime("%Y-%m-%d"):
                                    pass
                                    #formatted_output['date'] = journal_data['date']
                                if 'mood' in journal_data and formatted_output['mood'] == "Unknown":
                                    formatted_output['mood'] = journal_data['mood']
                                if 'confidence' in journal_data and formatted_output['confidence'] == 0.5:
                                    formatted_output['confidence'] = journal_data['confidence']
                                
                                # Format reflections
                                if 'reflections' in journal_data:
                                    if isinstance(journal_data['reflections'], dict):
                                        # Convert to list format expected by the UI
                                        reflections_list = []
                                        for key, value in journal_data['reflections'].items():
                                            if isinstance(value, dict):
                                                detail = f"{key}:\n"
                                                for sub_key, sub_value in value.items():
                                                    if sub_key != 'reason':  # Skip reason keys as they're handled with their pairs
                                                        reason = value.get(f"reason", "")
                                                        detail += f"- {sub_key}: {sub_value}\n"
                                                        if reason:
                                                            detail += f"  Reason: {reason}\n"
                                                reflections_list.append({
                                                    "prompt": key,
                                                    "response": detail.strip()
                                                })
                                            else:
                                                reflections_list.append({
                                                    "prompt": key,
                                                    "response": value
                                                })
                                        formatted_output['reflections'] = reflections_list
                                    elif isinstance(journal_data['reflections'], list):
                                        formatted_output['reflections'] = journal_data['reflections']
                        except Exception as e:
                            print(f"Error parsing task output JSON: {e}")
        
        # Save the formatted output
        os.makedirs("logs", exist_ok=True)
        # Force use of current system date
        formatted_output['date'] = datetime.now().strftime("%Y-%m-%d")  # Add this line
        with open("logs/journal_entry.json", "w") as f:
            json.dump(formatted_output, f, indent=2)
        
        print("Mood journaling complete. Entry saved to logs/journal_entry.json.")
        return formatted_output
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        journal_text = transcribe_audio(audio_path)
        print(f"Transcribed text: {journal_text}")
    elif os.environ.get("JOURNAL_TEXT"):
        # Get text from environment variable (set by Streamlit)
        audio_path = None
        journal_text = os.environ.get("JOURNAL_TEXT")
        print(f"Using provided text: {journal_text[:50]}...")
    else:
        audio_path = "meme.wav"  # Default audio file
        journal_text = transcribe_audio(audio_path)

    run(journal_text)

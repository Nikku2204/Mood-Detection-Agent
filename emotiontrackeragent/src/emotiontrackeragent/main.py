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

# LLMs
mood_llm = LLM(model="claude-3-5-sonnet-20240620", api_key=os.getenv("ANTHROPIC_API_KEY"))
coach_llm = LLM(model="claude-3-5-sonnet-20240620", api_key=os.getenv("ANTHROPIC_API_KEY"))
logger_llm = LLM(model="claude-3-5-sonnet-20240620", api_key=os.getenv("ANTHROPIC_API_KEY"))

# Agents
mood_agent = Agent(
    role="Mood Detector",
    goal="Understand user's emotional tone from journal input",
    backstory="A compassionate AI designed to detect and understand human emotions based on journal text.",
    llm=mood_llm
)

coach_agent = Agent(
    role="Reflection Coach",
    goal="Encourage user to explore their emotions",
    backstory="A thoughtful AI that guides users through introspection and emotional growth.",
    llm=coach_llm
)

logger_agent = Agent(
    role="Journal Logger",
    goal="Format and log mood + reflection as structured JSON",
    backstory="A helpful assistant that securely logs emotional reflections for personal growth.",
    llm=logger_llm
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
        with open("logs/journal_entry.json", "w") as f:
            json.dump(output.dict(), f, indent=2)
        print("Mood journaling complete. Entry saved to logs/journal_entry.json.")
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        journal_text = transcribe_audio(audio_path)
        print(journal_text)
    else:
        audio_path = None
        journal_text = "Today I feel overwhelmed and distant."

    run(journal_text)
    

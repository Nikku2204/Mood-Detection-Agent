import streamlit as st
import subprocess
import json
import os
import tempfile
from datetime import datetime


# Set page configuration
st.set_page_config(
    page_title="Emotion Tracker Agent",
    page_icon="😊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4b6cb7;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #6a8bab;
        margin-top: 1.5rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        border-left: 4px solid #4b6cb7;
    }
    .mood-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    .prompt-text {
        font-style: italic;
        color: #495057;
    }
    .response-text {
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>Emotion Tracker Agent</h1>", unsafe_allow_html=True)
st.markdown("Analyze your emotions through audio or text journal entries")

# With custom CSS for video container
st.markdown("""
<style>
.video-container {
    margin: 20px 0;
    border-radius: 10px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

video_html = """
<div class="video-container">
  <video autoplay loop muted playsinline style="width:100%; height:auto;">
    <source src="data:video/mp4;base64,{}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</div>
"""
# Read and encode the video file
import base64
with open("art.mp4", "rb") as video_file:
    video_bytes = video_file.read()
    video_base64 = base64.b64encode(video_bytes).decode()

# Display the video without controls
st.markdown(video_html.format(video_base64), unsafe_allow_html=True)

# After the header
st.markdown("""
<div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 2rem; border-left: 4px solid #4b6cb7;">
    <h3>How It Works</h3>
    <p>This tool uses AI to analyze your emotional state based on journal entries or audio recordings.</p>
    <ol>
        <li><strong>Input your thoughts</strong> - Choose from text entry, audio upload, or recording</li>
        <li><strong>AI analysis</strong> - Our multi-agent system detects your emotional state</li>
        <li><strong>Get insights</strong> - View your detected mood, confidence level, and personalized reflections</li>
    </ol>
    <p>The personalized reflections help you explore your emotions more deeply and gain insights into your emotional well-being.</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'journal_entry' not in st.session_state:
    st.session_state.journal_entry = None
if 'input_text' not in st.session_state:
    st.session_state.input_text = None
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None

# Sidebar options
st.sidebar.title("Input Options")
input_option = st.sidebar.radio("Choose input method:", ["Upload Audio", "Sample Audio Files", "Text Input"])

def run_mood_detection(input_type, input_value=None):
    """Run the mood detection agent with the specified input"""
    with st.spinner("Processing your entry... This may take a minute..."):
        if input_type == "upload_audio":
            # Save uploaded file to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(input_value.getvalue())
                tmp_filename = tmp.name
            
            st.session_state.audio_path = tmp_filename
            subprocess.run(["python", "main.py", tmp_filename], capture_output=True)
            
        elif input_type == "sample_audio":
            st.session_state.audio_path = input_value
            subprocess.run(["python", "main.py", input_value], capture_output=True)
            
        elif input_type == "text":
            # Create a temp file with the text
            with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt") as tmp:
                tmp.write(input_value)
                tmp_filename = tmp.name
            
            # Modify command to handle text input
            os.environ["JOURNAL_TEXT"] = input_value  # Pass via environment variable
            subprocess.run(["python", "main.py"], capture_output=True)
            os.unlink(tmp_filename)
        
        # Load the results
        try:
            with open("logs/journal_entry.json", "r") as f:
                st.session_state.journal_entry = json.load(f)
                return True
        except FileNotFoundError:
            st.error("Error: Journal entry file not found. The analysis might have failed.")
            return False

# Handle different input methods
if input_option == "Upload Audio":
    # Create tabs for uploading vs recording
    upload_tab, record_tab = st.tabs(["Upload Audio File", "Record Audio"])
    
    with upload_tab:
        uploaded_file = st.file_uploader("Upload an audio file (.wav)", type=["wav"])
        
        if uploaded_file is not None:
            st.audio(uploaded_file)
            if st.button("Analyze Uploaded Audio"):
                success = run_mood_detection("upload_audio", uploaded_file)
                if success:
                    st.session_state.input_text = "Audio file analysis"
    
    with record_tab:
        st.write("Record your voice to analyze your mood:")
        st.info("📱 Due to technical limitations, please use your phone or computer's voice recorder app, then upload the file here.")
        
        st.markdown("""
        **Instructions:**
        1. Use your phone's voice recorder app or computer's audio recorder
        2. Save the recording as a WAV file
        3. Upload it below
        """)
        
        st.markdown("""
        **Try saying something like:**
        - "I'm feeling really anxious about my upcoming presentation tomorrow."
        - "Today was a great day! I accomplished everything on my to-do list."
        - "I'm feeling a bit down and unmotivated today."
        """)
        
        recorded_file = st.file_uploader("Upload your recorded audio (.wav)", type=["wav"], key="record_uploader")
        
        if recorded_file is not None:
            st.audio(recorded_file)
            if st.button("Analyze This Recording"):
                success = run_mood_detection("upload_audio", recorded_file)
                if success:
                    st.session_state.input_text = "Recorded audio analysis"

elif input_option == "Sample Audio Files":
    # Find sample audio files
    sample_files = [f for f in os.listdir(".") if f.endswith(".wav")]
    
    if sample_files:
        selected_file = st.sidebar.selectbox("Select a sample audio file:", sample_files)
        st.sidebar.audio(selected_file)
        if st.sidebar.button("Analyze Mood"):
            success = run_mood_detection("sample_audio", selected_file)
            if success:
                st.session_state.input_text = f"Analysis of {selected_file}"
    else:
        st.sidebar.warning("No sample .wav files found in the current directory.")

elif input_option == "Text Input":
    journal_text = st.sidebar.text_area(
        "Enter your journal entry:", 
        "Today I feel overwhelmed and distant.",
        height=200
    )
    
    if st.sidebar.button("Analyze Mood"):
        success = run_mood_detection("text", journal_text)
        if success:
            st.session_state.input_text = journal_text

# Display results if available
if st.session_state.journal_entry:
    journal = st.session_state.journal_entry
    
    # Display audio if available
    if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
        st.subheader("Audio Input")
        st.audio(st.session_state.audio_path)
    
    # Display text input if available
    if st.session_state.input_text:
        st.markdown("<h2 class='sub-header'>Journal Entry</h2>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>{st.session_state.input_text}</div>", unsafe_allow_html=True)
        # Add explanation about results
        st.markdown("""
        <div style="background-color: #eaf7ff; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
            <h4>Understanding Your Results</h4>
            <p>Based on your entry, our AI system has analyzed your emotional state:</p>
            <ul>
                <li><strong>Detected Mood</strong>: The primary emotion identified in your entry</li>
                <li><strong>Confidence</strong>: How certain the AI is about its mood assessment</li>
                <li><strong>Reflections</strong>: Personalized prompts to help you explore your emotions more deeply</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    # Display mood analysis results
    st.markdown("<h2 class='sub-header'>Mood Analysis Results</h2>", unsafe_allow_html=True)
    
    # Create columns for mood display
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Determine mood from different possible key structures
        detected_mood = None
        if 'mood' in journal:
            detected_mood = journal['mood']
        elif 'detected_mood' in journal:
            detected_mood = journal['detected_mood']
        elif 'mood_analysis' in journal and 'detected_mood' in journal['mood_analysis']:
            detected_mood = journal['mood_analysis']['detected_mood']
        else:
            # If we still don't have a mood, check the entire structure
            st.warning(f"Could not find mood key. Available keys: {list(journal.keys())}")
            detected_mood = "Unknown"
        
        mood_color = {
            "Happy": "#4CAF50",
            "Sad": "#2196F3",
            "Angry": "#F44336",
            "Anxious": "#FF9800",
            "Neutral": "#9E9E9E"
        }.get(detected_mood, "#9E9E9E")
        
        st.markdown(
            f"""
            <div class='mood-card' style='background-color: {mood_color}20; border-left: 4px solid {mood_color};'>
                <h3>Detected Mood</h3>
                <h2>{detected_mood}</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        # Get confidence with fallback options
        confidence = None
        if 'confidence' in journal:
            confidence = journal['confidence']
        elif 'mood_analysis' in journal and 'confidence' in journal['mood_analysis']:
            confidence = journal['mood_analysis']['confidence']
        else:
            confidence = 0.5  # Default confidence if not found
            st.warning("Could not find confidence value")
        
        confidence_value = int(confidence * 100) if isinstance(confidence, (int, float)) else 50
        
        st.markdown(
            f"""
            <div class='mood-card' style='background-color: #f8f9fa; border-left: 4px solid #6a8bab;'>
                <h3>Confidence</h3>
                <h2>{confidence_value}%</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        # Get date with fallback
        date = None
        if 'date' in journal:
            date = journal['date']
        else:
            date = datetime.now().strftime("%Y-%m-%d")
            st.warning("Could not find date value")
        
        st.markdown(
            f"""
            <div class='mood-card' style='background-color: #f8f9fa; border-left: 4px solid #6a8bab;'>
                <h3>Date</h3>
                <h2>{date}</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Display reflections
    st.markdown("<h2 class='sub-header'>Reflections</h2>", unsafe_allow_html=True)
    
    if 'reflections' in journal:
        reflections = journal['reflections']
        if reflections and isinstance(reflections, list):
            for i, reflection in enumerate(reflections, 1):
                with st.expander(f"Reflection #{i}", expanded=True):
                    if isinstance(reflection, dict):
                        if 'prompt' in reflection and 'response' in reflection:
                            st.markdown(f"<p class='prompt-text'>{reflection['prompt']}</p>", unsafe_allow_html=True)
                            st.markdown(f"<p class='response-text'>{reflection['response']}</p>", unsafe_allow_html=True)
                        else:
                            # Just display whatever keys are available
                            for key, value in reflection.items():
                                st.markdown(f"<p><strong>{key}:</strong> {value}</p>", unsafe_allow_html=True)
                    elif isinstance(reflection, str):
                        st.markdown(f"<p>{reflection}</p>", unsafe_allow_html=True)
        else:
            st.warning("Reflections data is not in the expected format")
    else:
        st.warning("No reflections found in the journal entry")
    # Raw JSON output
    with st.expander("View Raw JSON"):
        st.json(journal)
    # Debug information (MOVED INSIDE THE if block)
    with st.expander("Debug Information", expanded=False):
        st.write("Journal Entry Keys:", list(journal.keys()))
        if 'mood_analysis' in journal:
            st.write("Mood Analysis Keys:", list(journal['mood_analysis'].keys()))
        st.json(journal)    
else:
    # Display instructions when no analysis has been run
    st.info("👈 Select an input method from the sidebar and click 'Analyze Mood' to get started!")



# Add information about the project
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown(
    "This demo uses a multi-agent AI system to analyze mood from journal entries "
    "and provide personalized reflections."
)
st.sidebar.markdown("**Built with:** Whisper, CrewAI, Gemini")
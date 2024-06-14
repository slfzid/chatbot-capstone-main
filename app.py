import json
import time
import os
from services import bedrock_agent_runtime
from dotenv import load_dotenv
import streamlit as st
import uuid
from streamlit_option_menu import option_menu

# Get config from environment variables
load_dotenv('.env')
agent_id = os.getenv('agent_id')
agent_alias_id = os.getenv('agentAliasId')
ui_title = os.environ.get("BEDROCK_AGENT_TEST_UI_TITLE", "NIRVITA HEALTHCARE ASSISTANT")
ui_icon = os.environ.get("BEDROCK_AGENT_TEST_UI_ICON")

def init_state():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.citations = []
    st.session_state.trace = {}

# General page configuration and initialization
st.set_page_config(page_title=ui_title, page_icon=ui_icon, layout="wide")
st.title(ui_title)
if len(st.session_state.items()) == 0:
    init_state()

# Sidebar button to reset session state
selected = option_menu(
    menu_title=None,
    options=["Home", "Chatbot", "About"],
    icons=["house", "book", "envelope"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "margin": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "orange", "font-size": "18px"}, 
        "nav-link": {"font-size": "18px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "green"},
    }
)

# Messages in the conversation
if selected == "Home":
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
    # Chat input that invokes the agent
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("...")
            response = bedrock_agent_runtime.invoke_agent(
                agent_id,
                agent_alias_id,
                st.session_state.session_id,
                prompt
            )
            output_text = response["output_text"]

            def stream_data():
                for word in output_text.split(" "):
                    yield word + " "
                    time.sleep(0.02)

            # Add citations
            if len(response["citations"]) > 0:
                citation_num = 1
                num_citation_chars = 0
                citation_locs = ""
                for citation in response["citations"]:
                    end_span = citation["generatedResponsePart"]["textResponsePart"]["span"]["end"] + 1
                    for retrieved_ref in citation["retrievedReferences"]:
                        citation_marker = f"[{citation_num}]"
                        output_text = output_text[:end_span + num_citation_chars] + citation_marker + output_text[end_span + num_citation_chars:]
                        citation_locs = citation_locs + "\n<br>" + citation_marker + " " + retrieved_ref["location"]["s3Location"]["uri"]
                        citation_num = citation_num + 1
                        num_citation_chars = num_citation_chars + len(citation_marker)
                    output_text = output_text[:end_span + num_citation_chars] + "\n" + output_text[end_span + num_citation_chars:]
                    num_citation_chars = num_citation_chars + 1
                output_text = output_text + "\n" + citation_locs

            placeholder.markdown(output_text, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": output_text})
            st.session_state.citations = response["citations"]
            st.session_state.trace = response["trace"]

elif selected == "Chatbot":
    st.title(f"{selected}")
    st.write("Chatbot page content goes here.")

elif selected == "About":
    st.title(f"{selected}")
    st.write("About page content goes here.")

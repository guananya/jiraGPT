import streamlit as st
from jira import JIRA 
from openai import OpenAI
import time

# Initialize session state variables to store summary and description
if 'summ' not in st.session_state:
    st.session_state.summ = ""
if 'desc' not in st.session_state:
    st.session_state.desc = ""

# Function to create an OpenAI assistant
def makeAssistant(instruction, client):
    assistant = client.beta.assistants.create(
        name="jellyfish",
        instructions=instruction,
        model="gpt-3.5-turbo-1106"
    )
    return assistant

# Function to get output from the OpenAI assistant
def getOutput(assistant, prompt):
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    # Delay to ensure response is received
    time.sleep(8)
    
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    
    # Extract and format the response from messages
    for message in reversed(messages.data):
        allData = message.content[0].text.value

    summ = (allData.split("summary")[1].split('fleshedOut')[0]).replace('\n', "")
    desc = (allData.split('fleshedOut')[1]).replace('\n', "")

    return summ, desc

# Function to add a new issue to Jira
def addToJira(summ, desc, jira, jiraProjectName):
    issue_dict = {
        'project': {'key': jiraProjectName},
        'summary': summ,
        'description': desc,
        'issuetype': {'name': 'Task'},
    }
    try:
        new_issue = jira.create_issue(fields=issue_dict)
        print(f"Issue created: {new_issue.key}")
    except Exception as e:
        print(f"Error: {e}")

# Streamlit app setup
st.title('Jira Ticket Creator')
st.text('This is a web app that allows you to take one-line descriptions of a task and make fleshed out software implementation tickets that gets uploaded to your Jira!')

# Input field for task description
st.subheader('Task Input')
task_description = st.text_input("Task Description", placeholder="Enter the task")
custom_assistant = st.text_input("Instructing the Assistant (optional)", placeholder="Add specific things you want from your assistant. For example, sub tasks or task deadlines.")

openAIKey = st.text_input("Open AI API Key", placeholder="Enter your Open AI API key (not stored anywhere)", type="password")

# Initialize OpenAI client
client = OpenAI(api_key=openAIKey)

# Button to generate Jira ticket
if st.button('Generate Ticket'):
    instruction = "You are on the engineering team managing tickets. You transform brief software engineering task titles into a fully fleshed ticket that can be used in things like Jira. You should take in a short engineering task as input. You should output a completed scope for the task that could include descriptions, acceptance criteria, sub-tasks, assumptions, and any other relevant details.You output should be json of 'summary' and 'fleshedOut' only."
    assistant = makeAssistant(instruction + custom_assistant, client)
    st.session_state.summ, st.session_state.desc = getOutput(assistant, task_description)
    st.markdown("### Generated Summary")
    st.write(st.session_state.summ)
    st.markdown("### Generated Description")
    st.write(st.session_state.desc)

# Input fields for Jira connection
st.subheader('Connect to Jira')
jiraUsername = st.text_input("Jira Username", placeholder="Enter your Jira username")
jiraAPI = st.text_input("Jira API Key", placeholder="Enter your Jira API key", type="password")
jiraOptions = st.text_input("Jira Link", placeholder="Enter your Jira link")
jiraProjectName = st.text_input("Jira Project Name", placeholder="Enter your Jira project name")


# Button to add ticket to Jira
if st.button('🚀 Add to Jira'):
    # Check if all Jira fields are filled
    if jiraUsername and jiraAPI and jiraOptions and jiraProjectName:
        jira = JIRA(options={'server': jiraOptions}, basic_auth=(jiraUsername, jiraAPI)) 
        if st.session_state.summ and st.session_state.desc:
            addToJira(st.session_state.summ, st.session_state.desc, jira, jiraProjectName)
            st.success("Ticket successfully added to Jira!")
        else:
            st.error("No ticket information available. Please generate a ticket first.")
    else:
        st.error("Please enter all Jira variables details before adding to Jira.")

# Optional: Display all issues in the Jira project
if st.checkbox('Show All Issues in Project'):
    if jiraUsername and jiraAPI and jiraOptions and jiraProjectName:
        jira = JIRA(options={'server': jiraOptions}, basic_auth=(jiraUsername, jiraAPI)) 
        for singleIssue in jira.search_issues('project = ' + jiraProjectName): 
            st.write(f'{singleIssue.key}: {singleIssue.fields.summary}')
    else:
        st.error("Please enter all Jira variables details before connecting to Jira.")

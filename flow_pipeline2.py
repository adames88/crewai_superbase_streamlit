from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, List, Set, Tuple
import yaml
from crewai import Flow
from crewai.flow.flow import listen, start, router, or_
import warnings
warnings.filterwarnings("always", module="pydantic")
import logging
import re
import pandas as pd
import streamlit as st
import smtplib
from email.message import EmailMessage
import time 
from superbase_tools import (
    supabase_get_row_tool, 
    supabase_get_all_rows_tool, 
    supabase_insert_row_tool, 
    supabase_delete_row_tool, 
    supabase_update_tool
)
from helper import load_env, get_supabase_url, get_supabase_key, get_serper_api_key
import os
load_env()

url: str = os.getenv("SUPERBASE_URL")
key: str = os.getenv("SUPERBASE_KEY")
os.environ['SERPER_API_KEY'] = get_serper_api_key()

logging.basicConfig(level=logging.DEBUG)


# Create instances of the tools
get_row_tool = supabase_get_row_tool.SupabaseGetRowTool()  # Instantiate the tool
get_all_rows = supabase_get_all_rows_tool.SupabaseGetAllRowsTool()
insert_row = supabase_insert_row_tool.SupabaseInsertRowTool()
delete_row = supabase_delete_row_tool.SupabaseDeleteRowTool()
update_row = supabase_update_tool.SupabaseUpdateRowTool()


class LeadPersonalInfo(BaseModel):
    name: str = Field(description="The full name of the lead.")
    job_title: str = Field(description="The job title of the lead.")
    role_relevance: int = Field(ge=0, le=10, description="A score representing how relevant the lead's role is to the decision-making process (0-10).")
    professional_background: Optional[str] = Field(description="A brief description of the lead's professional background.")

class CompanyInfo(BaseModel):
    company_name: str = Field(description="The name of the company the lead works for.")
    industry: str = Field(description="The industry in which the company operates.")
    company_size: int = Field(description="The size of the company in terms of employee count.")
    revenue: Optional[float] = Field(None, description="The annual revenue of the company, if available.")
    market_presence: int = Field(ge=0, le=10, description="A score representing the company's market presence (0-10).")

class LeadScore(BaseModel):
    score: int = Field(ge=0, le=100, description="The final score assigned to the lead (0-100).")
    scoring_criteria: List[str] = Field(description="The criteria used to determine the lead's score.")
    validation_notes: Optional[str] = Field(None, description="Any notes regarding the validation of the lead score.")
    scored_leads_feedback: str = Field(description="Feedback provided by user")

class LeadScoringResult(BaseModel):
    personal_info: LeadPersonalInfo = Field(description="Personal information about the lead.")
    company_info: CompanyInfo = Field(description="Information about the lead's company.")
    lead_score: LeadScore = Field(description="The calculated score and related information for the lead.")

files = {'agents': 'config/agents.yaml', 'tasks': 'config/tasks.yaml'}
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

agents_config = configs['agents']
tasks_config = configs['tasks']


class StreamToExpander:
    def __init__(self, expander):
        self.expander = expander
        self.buffer = []
        self.avatars = {
            'Entering new CrewAgentExecutor chain': '🔄',
            'Lead Data Specialist': '📊',
            'Cultural Fit Analyst': '🎯',
            'Lead Scorer and Validator': '⭐',
            'Supabase Agent': '💾',
            'Email Content Writer': '✍️',
            'Engagement Optimization Specialist': '📈',
            'Finished chain.': '✅'
        }  # Define a list of colors

    def write(self, data):
        # Filter out ANSI escape codes using a regular expression
        cleaned_data = re.sub(r'\x1B\[[0-9;]*[mK]', '', data)

        # More comprehensive URL pattern that handles various URL formats
        url_pattern = r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»""'']))'
        urls = re.findall(url_pattern, cleaned_data)
        if urls:
            # Extract the full URL from the match tuples and add to session state
            new_urls = [url[0] for url in urls if url[0] not in st.session_state.captured_urls]
            st.session_state.captured_urls.extend(new_urls)
        # Check if the data contains 'task' information
        task_match_object = re.search(r'\"task\"\s*:\s*\"(.*?)\"', cleaned_data, re.IGNORECASE)
        task_match_input = re.search(r'task\s*:\s*([^\n]*)', cleaned_data, re.IGNORECASE)
        task_value = None
        if task_match_object:
            task_value = task_match_object.group(1)
        elif task_match_input:
            task_value = task_match_input.group(1).strip()

        if task_value:
            st.toast(":robot_face: " + task_value)

        # Check if the text contains the specified phrase and apply color
        if "Entering new CrewAgentExecutor chain" in cleaned_data:
            # Apply different color and switch color index
            #self.color_index = self.colors[0]  # Increment color index and wrap around if necessary

            cleaned_data = cleaned_data.replace("Entering new CrewAgentExecutor chain", f"{self.avatars["Entering new CrewAgentExecutor chain"]} Entering new CrewAgentExecutor chain")

        if "Lead Data Specialist" in cleaned_data:
            # Apply different color 
            cleaned_data = cleaned_data.replace("Lead Data Specialist", f"{self.avatars["Lead Data Specialist"]} Lead Data Specialist")
            #self.color_index = (self.color_index + 1) % len(self.colors)
        if "Cultural Fit Analyst" in cleaned_data:
            cleaned_data = cleaned_data.replace("Cultural Fit Analyst", f":{self.avatars["Cultural Fit Analyst"]} Cultural Fit Analyst")
            #self.color_index = (self.color_index + 1) % len(self.colors)
        if "Lead Scorer and Validator" in cleaned_data:
            cleaned_data = cleaned_data.replace("Lead Scorer and Validator", f":{self.avatars["Lead Scorer and Validator"]} Lead Scorer and Validator")
            #self.color_index = (self.color_index + 1) % len(self.colors)
        if "Supabase" in cleaned_data:
            cleaned_data = cleaned_data.replace("Supabase Agent", f":{self.avatars["Supabase Agent"]} Supabase Agent")
            #self.color_index = (self.color_index + 1) % len(self.colors)
        if "Email Content Writer" in cleaned_data:
            cleaned_data = cleaned_data.replace("Email Content Writer", f":{self.avatars["Email Content Writer"]} Email Content Writer")
            #self.color_index = (self.color_index + 1) % len(self.colors)
        if "Engagement Optimization Specialist" in cleaned_data:
            cleaned_data = cleaned_data.replace("Engagement Optimization Specialist", f":{self.avatars["Engagement Optimization Specialist"]} Engagement Optimization Specialist")
            #self.color_index = (self.color_index + 1) % len(self.colors)
        if "Finished chain." in cleaned_data:
            cleaned_data = cleaned_data.replace("Finished chain.", f":{self.avatars["Finished chain."]} Finished chain.")
            #self.color_index = (self.color_index + 1) % len(self.colors)

        self.buffer.append(cleaned_data)
        if "\n" in data:
            self.expander.markdown(''.join(self.buffer), unsafe_allow_html=True)
            self.buffer = []

# Creating Agents
lead_data_agent = Agent(
  config=agents_config['lead_data_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()],
  step_callback=StreamToExpander
)

cultural_fit_agent = Agent(
  config=agents_config['cultural_fit_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()],
  step_callback=StreamToExpander
)

scoring_validation_agent = Agent(
  config=agents_config['scoring_validation_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()],
  step_callback=StreamToExpander
)

# Creating Tasks
lead_data_task = Task(
  config=tasks_config['lead_data_collection'],
  agent=lead_data_agent,
)

cultural_fit_task = Task(
  config=tasks_config['cultural_fit_analysis'],
  agent=cultural_fit_agent,
)

scoring_validation_task = Task(
  config=tasks_config['lead_scoring_and_validation'],
  agent=scoring_validation_agent,
  context=[lead_data_task, cultural_fit_task],
  output_pydantic=LeadScoringResult,
)

# Creating Crew
lead_scoring_crew = Crew(
  agents=[
    lead_data_agent,
    cultural_fit_agent,
    scoring_validation_agent
  ],
  tasks=[
    lead_data_task,
    cultural_fit_task,
    scoring_validation_task
  ],
  verbose=True
)


# Creating Agents
email_content_specialist = Agent(
  config=agents_config['email_content_specialist'],
  step_callback=StreamToExpander
)

engagement_strategist = Agent(
  config=agents_config['engagement_strategist'],
  step_callback=StreamToExpander
)

# Creating Tasks
email_drafting = Task(
  config=tasks_config['email_drafting'],
  agent=email_content_specialist,
)

engagement_optimization = Task(
  config=tasks_config['engagement_optimization'],
  agent=engagement_strategist,
)

# Creating Crew
email_writing_crew = Crew(
    agents=[
    email_content_specialist,
    engagement_strategist
  ],
  tasks=[
    email_drafting,
    engagement_optimization
  ],
  verbose=True
)

superbase_agent = Agent(
  config=agents_config['superbase_agent'],
  tools=[get_row_tool,get_all_rows,insert_row,delete_row,update_row],
  step_callback=StreamToExpander,
  #knowledge_sources=[text_knowledge],
)

# Creating Tasks
database_query = Task(
  config=tasks_config['database_query'],
  agent=superbase_agent,
)

# Creating Crew
superbase_crew = Crew(
  agents=[superbase_agent],
  tasks=[database_query],
  verbose=True,
  #knowledge_sources=[text_knowledge],
)

class SalesPipeline(Flow):
    @start()
    def fetch_leads(self):
        st.session_state.progress.progress(10, text='Fetching Leads')  # Progress update
        time.sleep(3)

        # Check if user uploaded a file
        if "uploaded_leads" in st.session_state:
            leads_df = st.session_state["uploaded_leads"]
        else:
            excel_file_path = "./sales_leads.csv"
            try:
                leads_df = pd.read_csv(excel_file_path)
            except FileNotFoundError:
                raise FileNotFoundError(f"Excel file not found at {excel_file_path}. Please check the path.")

        # Convert data into lead format
        leads = []
        for _, row in leads_df.iterrows():
            lead = {
                "lead_data": {
                    "name": row["name"],
                    "job_title": row["job_title"],
                    "company": row["company"],
                    "email": row["email"],
                    "use_case": row["usecase"],
                    "scored_leads_feedback": ""
                },
            }
            leads.append(lead)

        return leads


    @listen(fetch_leads)
    def score_leads(self, leads):
        st.session_state.progress.progress(30,text='Scoring Leads')  # Progress update
        scores = lead_scoring_crew.kickoff_for_each(leads) # This is the crew that will score the leads
        self.state["score_crews_results"] = scores

        return scores

    
    @listen(score_leads)
    def store_leads_score(self, scores):
        # Here we would store the scores in the database
        st.session_state.progress.progress(50, text='storing leads at supabase')
        result_py = [score.to_dict() for score in scores]
        superbase_crew.kickoff_for_each(result_py)
        
        return scores
        

    @listen(score_leads)
    def filter_leads(self, scores):
        st.session_state.progress.progress(60, text='Filtering Leads')
        filtered_leads = [score for score in scores if score['lead_score'].score >= 60]
       
        return filtered_leads

    @listen(filter_leads)
    def write_email(self, filtered_leads):
        st.session_state.progress.progress(70, text='Writing Email')  # Progress update
        scored_leads = [lead.to_dict() for lead in filtered_leads]
        emails = email_writing_crew.kickoff_for_each(scored_leads)
        return emails

    @listen(write_email)
    def send_email(self, emails):
        st.session_state.progress.progress(100, text='Email Complete')  # Completion
        return emails
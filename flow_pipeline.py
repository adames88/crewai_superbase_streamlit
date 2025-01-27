from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, List, Set, Tuple
import yaml
from crewai import Flow
from crewai.flow.flow import listen, start
import warnings
warnings.filterwarnings("always", module="pydantic")
import logging
import re
import pandas as pd
import streamlit as st
import smtplib
from email.message import EmailMessage
import agentops
import os
#agentops.init("10d2ae41-41a5-468a-a0da-b0ab4225a8b0",skip_auto_end_session=True)

from helper import load_env, get_supabase_url, get_supabase_key

load_env()

url: str = os.getenv("SUPERBASE_URL")
key: str = os.getenv("SUPERBASE_KEY")

from superbase_tools import (
    supabase_get_row_tool, 
    supabase_get_all_rows_tool, 
    supabase_insert_row_tool, 
    supabase_delete_row_tool, 
    supabase_update_tool
)

from crewai_tools import FileWriterTool
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

text_knowledge = open("knowledge/table_info.txt", "r").read()

file_writer = FileWriterTool(
    file_path="./knowledge/table_info.txt",
    name="Table Info"
)

# Create instances of the tools
get_row_tool = supabase_get_row_tool.SupabaseGetRowTool()  # Instantiate the tool
get_all_rows = supabase_get_all_rows_tool.SupabaseGetAllRowsTool()
insert_row = supabase_insert_row_tool.SupabaseInsertRowTool()
delete_row = supabase_delete_row_tool.SupabaseDeleteRowTool()
update_row = supabase_update_tool.SupabaseUpdateRowTool()

logging.basicConfig(
    level=logging.DEBUG
) 

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

class LeadScoringResult(BaseModel):
    personal_info: LeadPersonalInfo = Field(description="Personal information about the lead.")
    company_info: CompanyInfo = Field(description="Information about the lead's company.")
    lead_score: LeadScore = Field(description="The calculated score and related information for the lead.")


        # Define file paths for YAML configurations
files = {
        'agents': 'config/agents.yaml',
        'tasks': 'config/tasks.yaml'
    }
# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

agents_config = configs['agents']
tasks_config = configs['tasks']

# class StreamToExpander:
#     def __init__(self, expander):
#         self.expander = expander
#         self.buffer = []
#         self.colors = ['red', 'green', 'blue', 'orange', "yellow","pink", "gray"]  # Define a list of colors
#         self.color_index = 0  # Initialize color index

#     def write(self, data):
#         # Filter out ANSI escape codes using a regular expression
#         cleaned_data = re.sub(r'\x1B\[[0-9;]*[mK]', '', data)

#         # Check if the data contains 'task' information
#         task_match_object = re.search(r'\"task\"\s*:\s*\"(.*?)\"', cleaned_data, re.IGNORECASE)
#         task_match_input = re.search(r'task\s*:\s*([^\n]*)', cleaned_data, re.IGNORECASE)
#         task_value = None
#         if task_match_object:
#             task_value = task_match_object.group(1)
#         elif task_match_input:
#             task_value = task_match_input.group(1).strip()

#         if task_value:
#             st.toast(":robot_face: " + task_value)

#         # Check if the text contains the specified phrase and apply color
#         if "Entering new CrewAgentExecutor chain" in cleaned_data:
#             # Apply different color and switch color index
#             self.color_index = (self.color_index + 1) % len(self.colors)  # Increment color index and wrap around if necessary

#             cleaned_data = cleaned_data.replace("Entering new CrewAgentExecutor chain", f":{self.colors[self.color_index]}[Entering new CrewAgentExecutor chain]")

#         if "Lead Data Specialistt" in cleaned_data:
#             # Apply different color 
#             cleaned_data = cleaned_data.replace("Lead Data Specialist", f":{self.colors[self.color_index]}[Lead Data Specialist]")
#             self.color_index = (self.color_index + 1) % len(self.colors)
#         if "Cultural Fit Analyst" in cleaned_data:
#             cleaned_data = cleaned_data.replace("Cultural Fit Analyst", f":{self.colors[self.color_index]}[Cultural Fit Analyst]")
#             self.color_index = (self.color_index + 1) % len(self.colors)
#         if "Lead Scorer and Validator" in cleaned_data:
#             cleaned_data = cleaned_data.replace("Lead Scorer and Validator", f":{self.colors[self.color_index]}[Lead Scorer and Validator]")
#             self.color_index = (self.color_index + 1) % len(self.colors)
#         if "Email Content Writer" in cleaned_data:
#             cleaned_data = cleaned_data.replace("Email Content Writer", f":{self.colors[self.color_index]}[Email Content Writer]")
#             self.color_index = (self.color_index + 1) % len(self.colors)
#         if "Engagement Optimization Specialist" in cleaned_data:
#             cleaned_data = cleaned_data.replace("Engagement Optimization Specialist", f":{self.colors[self.color_index]}[Engagement Optimization Specialist]")
#             self.color_index = (self.color_index + 1) % len(self.colors)
#         if "Finished chain." in cleaned_data:
#             cleaned_data = cleaned_data.replace("Finished chain.", f":{self.colors[self.color_index]}[Finished chain.]")
#             self.color_index = (self.color_index + 1) % len(self.colors)

#         self.buffer.append(cleaned_data)
#         if "\n" in data:
#             self.expander.markdown(''.join(self.buffer), unsafe_allow_html=True)
#             self.buffer = []

# Creating Agents
lead_data_agent = Agent(
  config=agents_config['lead_data_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()],
)

cultural_fit_agent = Agent(
  config=agents_config['cultural_fit_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()],
)

scoring_validation_agent = Agent(
  config=agents_config['scoring_validation_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()],
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
)

engagement_strategist = Agent(
  config=agents_config['engagement_strategist'],
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
  tools=[get_row_tool,get_all_rows,insert_row,delete_row,update_row,file_writer],
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
  process=Process.sequential,
)

class SalesPipeline(Flow):
    @start()
    def fetch_leads(self):
      # Specify the path to your Excel file
      excel_file_path = "./sales_leads.csv"

      # Read the Excel file
      try:
          leads_df = pd.read_csv(excel_file_path)
      except FileNotFoundError:
          raise FileNotFoundError(f"Excel file not found at {excel_file_path}. Please check the path.")
      
      # Convert the DataFrame to the required format
      leads = []
      for _, row in leads_df.iterrows():
          lead = {
              "lead_data": {
                  "name": row["name"],
                  "job_title": row["job_title"],
                  "company": row["company"],
                  "email": row["email"],
                  "use_case": row["usecase"]
              },
          }
          leads.append(lead)
    
      return leads
    # def fetch_leads(self):
        # Pull our leads from the database
        # leads = [
        #     {
        #         "lead_data": {
        #             "name": "Pavel Sher",
        #             "job_title": "CEO of FuseBase",
        #             "company": "FuseBase",
        #             "email": "paul@fusebase.com",
        #             "use_case": "Using AI Agent to do better data enrichment."
        #         },
        #     },
        #                 {
        #         "lead_data": {
        #             "name": "Abdulaziz AlMulhem ",
        #             "job_title": "Founder & CEO of packman.ai",
        #             "company": "packman.ai",
        #             "email": "Abdulaziz@packman.ai",
        #             "use_case": "Using AI Agent for automation."
        #         },
        #     },
        # ]
        # return leads

    @listen(fetch_leads)
    def score_leads(self, leads):
        scores = lead_scoring_crew.kickoff_for_each(leads)
        self.state["score_crews_results"] = scores
        return scores

    @listen(score_leads)
    def store_leads_score(self, scores):
        # Here we would store the scores in the database

        data = superbase_crew.kickoff_for_each(scores)
        print(data)
        return scores

    @listen(score_leads)
    def filter_leads(self, scores):
        return [score for score in scores if score['lead_score'].score >= 60]

    @listen(filter_leads)
    def write_email(self, leads):
        scored_leads = [lead.to_dict() for lead in leads]
        emails = email_writing_crew.kickoff_for_each(scored_leads)
        #self.state.leads = leads
        return emails

    @listen(write_email)
    def send_email(self, emails):
      """
      Sends an email with the given content to the specified recipient.

      :param email_content: The content of the email (string).
      :param recipient_email: The recipient's email address (string).
      """
      # for index, email in emails:
      #   email_content = email[index]
      #   lead = self.state.leads[index]["lead_data"].email
      #   # Email configuration
      #   smtp_server = 'smtp.gmail.com'
      #   port = 587  # SMTP port for TLS
      #   sender_email = 'adamelshimi@sensai-consulting.com'
      #   sender_password = 'gldg ncwg kivt ofoq'

      #   # Email subject
      #   subject = f'Email - {lead}'

      #   # Construct the email message
      #   msg = EmailMessage()
      #   msg['Subject'] = subject
      #   msg['From'] = sender_email
      #   msg['To'] = "adamelshimi@gmail.com"
      #   msg.set_content(email_content)

      #   # Send the email
      #   try:
      #       # Connect to the SMTP server
      #       with smtplib.SMTP(smtp_server, port) as server:
      #           server.starttls()  # Secure the connection
      #           server.login(sender_email, sender_password)  # Login to your email account
      #           server.send_message(msg)  # Send the email
      #       print(f"Email sent successfully to {lead}!")
      #   except Exception as e:
      #       print(f"Failed to send email: {e}")

      return emails

if __name__ == "__main__":
    flow = SalesPipeline()
    flow.kickoff()
# End of program

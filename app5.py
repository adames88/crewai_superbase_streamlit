from helper import load_env
load_env()
import streamlit as st
import os
from flow_pipeline2 import SalesPipeline
import pandas as pd
import textwrap
from IPython.display import HTML
from flow_pipeline2 import StreamToExpander
import sys
import textwrap

# Set OpenAI Model
os.environ['OPENAI_MODEL_NAME'] = 'gpt-4o-mini'

# Initialize the SalesPipeline
flow = SalesPipeline()


# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "state" not in st.session_state:
    st.session_state.state = {
        "score_crews_results": [],
        "filtered_leads": [],
        "emails": [],
        "cost": [],
    }
if "progress" not in st.session_state:
    st.session_state.progress = st.empty()


if "captured_urls" not in st.session_state:
    st.session_state.captured_urls = []

# # Helper function: Add to chat history
def add_to_chat(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)


# Function to parse pipeline outputs
def process_pipeline_outputs(emails):
    """Parse the outputs of tasks from the pipeline and update session state."""

    # Process lead scores
    scores = flow.state["score_crews_results"]
    if scores:
        for i in range(len(scores)):
            lead_scoring_result = scores[i].pydantic

            # Prepare data for Lead Scores tab
            lead_data = {
                'Name': lead_scoring_result.personal_info.name,
                'Job Title': lead_scoring_result.personal_info.job_title,
                'Role Relevance': lead_scoring_result.personal_info.role_relevance,
                'Professional Background': lead_scoring_result.personal_info.professional_background,
                'Company Name': lead_scoring_result.company_info.company_name,
                'Industry': lead_scoring_result.company_info.industry,
                'Company Size': lead_scoring_result.company_info.company_size,
                'Revenue': lead_scoring_result.company_info.revenue,
                'Market Presence': lead_scoring_result.company_info.market_presence,
                'Lead Score': lead_scoring_result.lead_score.score,
                'Scoring Criteria': ', '.join(lead_scoring_result.lead_score.scoring_criteria),
                'Validation Notes': lead_scoring_result.lead_score.validation_notes
            }
            st.session_state.state["score_crews_results"].append(lead_data)

            # Process filtered leads
            filtered_leads_data = {
                'Name': lead_scoring_result.personal_info.name,
                'Job Title': lead_scoring_result.personal_info.job_title,
                'Role Relevance': lead_scoring_result.personal_info.role_relevance,
                'Professional Background': lead_scoring_result.personal_info.professional_background,
                'Company Name': lead_scoring_result.company_info.company_name,
                'Industry': lead_scoring_result.company_info.industry,
                'Validation Notes': lead_scoring_result.lead_score.validation_notes
            }
            st.session_state.state["filtered_leads"].append(filtered_leads_data)

    # Process emails
    #emails = flow.state["emails"]
    if emails:
        for email in emails:
            wrapped_email = textwrap.fill(email.raw, width=80)
            st.session_state.state["emails"].append(wrapped_email)

        for index, cost in enumerate(st.session_state.state["score_crews_results"]):
            scores = st.session_state.state["score_crews_results"]
            lead_scoring_result = scores[index]
            # Convert UsageMetrics instance to a DataFrame
            df_usage_scoreLead_metrics = pd.DataFrame([flow.state["score_crews_results"][index].token_usage.dict()])
            # Convert UsageMetrics instance to a DataFrame
            df_usage_email_metrics = pd.DataFrame([emails[index].token_usage.dict()])
            # Calculate total costs
            costs_score = 0.150 * df_usage_scoreLead_metrics['total_tokens'].sum() / 1_000_000
            costs_email = 0.150 * df_usage_email_metrics['total_tokens'].sum() / 1_000_000
            st.session_state.state["cost"].append({f"Lead Name":f"{lead_scoring_result["Name"]} - {lead_scoring_result["Company Name"]}", 
                                                    "Total Lead Score cost": f"{costs_score:.4f} ($)", 
                                                    "Total Email Costs": f"{costs_email:.4f} ($)",
                                                    "Total Costs": str(float(f"{costs_email:.4f}") + float(f"{costs_score:.4f}")) + " $"})



# Main pipeline execution
def kickoff_pipeline():
    with st.spinner("Running the pipeline..."):
        add_to_chat("assistant", "Starting the pipeline...")
        emails = flow.kickoff()
        process_pipeline_outputs(emails)
        add_to_chat("assistant", "Pipeline execution complete!")
    return emails 

# Streamlit UI components
st.title("Lead Scoring and Engagement Dashboard")

# Chat interface for pipeline execution
st.header("💬 SensAI Agents Interface",divider="green")
if st.button("Run Pipeline"):
    with st.status("🤖 **SenAI Agents at work...**", state="running", expanded=True) as status:
        with st.container(height=500, border=False):
            sys.stdout = StreamToExpander(st)
            result = kickoff_pipeline()
        status.update(label="✅ Email Campaign Ready!",
                        state="complete", expanded=False)
    # Add a message indicating completion to the chat history
    #add_to_chat("assistant", "Pipeline execution complete! You can now explore the results.")

with st.sidebar:
    st.header("🔗 References - URLs Used by the Agents")
    if st.session_state.captured_urls:
        for url in st.session_state.captured_urls:
            st.markdown(f"- [{url}]({url})")
    else:
        st.info("No URLs found yet. Run the pipeline to discover URLs.")

# Tabs for parsed outputs
st.header("Pipeline Outputs")
tab1, tab2, tab3, tab4= st.tabs(
    ["Lead Scores", "Filtered Leads", "Generated Emails", "Costs"]
)

# Tab 1: Lead Scores
with tab1:
    st.write("Lead Scores:")
    if st.session_state.state["score_crews_results"]:
        for i in range(len(st.session_state.state["score_crews_results"])):
            lead_scores_df = pd.DataFrame.from_dict(
                st.session_state.state["score_crews_results"][i], orient="index", columns=["Value"]
            ).reset_index().rename(columns={"index": "Attribute"})
            st.table(lead_scores_df)

            # Add a download button
            csv = lead_scores_df.to_csv(index=False)
            st.download_button(
                label="Download Lead Scores as CSV",
                data=csv,
                file_name=f"lead_scores_{i+1}.csv",
                mime="text/csv",
            )
    else:
        st.warning("No scores available yet. Run the pipeline.")

# Tab 2: Filtered Leads
with tab2:
    st.write("Filtered Leads:")
    if st.session_state.state["filtered_leads"]:
        filtered_leads_df = pd.DataFrame(st.session_state.state["filtered_leads"])
        st.table(filtered_leads_df)

        # Add a download button
        csv = filtered_leads_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Leads as CSV",
            data=csv,
            file_name="filtered_leads.csv",
            mime="text/csv",
        )
    else:
        st.warning("No filtered leads available yet. Run the pipeline.")

# Tab 3: Generated Emails
with tab3:
    st.write("Generated Emails:")
    if st.session_state.state["emails"]:
        all_emails = []
        if st.session_state.state["emails"]:
            for index, email in enumerate(st.session_state.state["emails"]):
                scores = st.session_state.state["score_crews_results"]
                lead_scoring_result = scores[index]
                st.text_area(f"Generated Email - {lead_scoring_result['Company Name']}", email, height=150)
                
                # Save individual email to a list
                all_emails.append({"Lead Name": lead_scoring_result['Name'], "Email": email})
            
            # Convert emails to a DataFrame
            emails_df = pd.DataFrame(all_emails)
            
            # Add a download button
            csv = emails_df.to_csv(index=False)
            st.download_button(
                label="Download All Emails as CSV",
                data=csv,
                file_name="generated_emails.csv",
                mime="text/csv",
            )
        else:
            st.warning("No emails generated yet. Run the pipeline.")


# Tab 4: Costs
with tab4:
    st.write("Cost Analysis:")
    # process costs
    if st.session_state.state["emails"]:
            costs_df = pd.DataFrame(st.session_state.state["cost"])
            st.table(costs_df)
            
            # Add a download button
            csv = costs_df.to_csv(index=False)
            st.download_button(
                label="Download Cost Analysis as CSV",
                data=csv,
                file_name="cost_analysis.csv",
                mime="text/csv",
                )
    else:
        st.warning("No usage metrics available yet. Run the pipeline.")

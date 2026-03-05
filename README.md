
# Time Leak Detector (ITSM)

Operational analytics pipeline for diagnosing time leakage in IT service workflows.

This project simulates Jira/ServiceNow ticket lifecycles, computes operational metrics, identifies workflow bottlenecks, and estimates cost savings from process improvements.

Key capabilities:

• Detect workflow inefficiencies across teams and statuses  
• Quantify operational time leakage in ticket lifecycles  
• Simulate intervention strategies before implementation  
• Generate executive-ready narratives from operational metrics  
• Provide an interactive analytics dashboard via Streamlit

Overview

Time Leak Detector is an operational analytics pipeline designed to identify workflow inefficiencies in IT Service Management (ITSM) ticket lifecycles.

The system simulates realistic Jira/ServiceNow-style ticket data, computes time-based performance metrics, attributes operational leakage across teams and statuses, estimates cost impact, and enables scenario-based intervention modeling.

The platform also includes an LLM-assisted executive narrative generator with structured fact validation to translate analytics outputs into executive-ready summaries.

The goal of the project is to demonstrate how structured analytics pipelines can surface operational inefficiencies and quantify savings opportunities in a repeatable, automated way.

Problem Statement

IT operations teams frequently rely on manual exports and spreadsheet analysis to diagnose workflow inefficiencies.

Typical workflow:

Export tickets from Jira or ServiceNow

Clean and normalize timestamp data

Manually compute cycle time and queue delays

Build pivot tables by team, category, or priority

Estimate cost exposure from delays

This process is time-consuming, inconsistent, and difficult to scale.

Time Leak Detector automates this workflow end-to-end using a modular analytics pipeline.

What This Project Demonstrates

This project shows how operational analytics can be used to:

Diagnose workflow inefficiencies in IT service management systems

Quantify operational time leakage across teams and processes

Simulate operational interventions before implementation

Translate operational metrics into financial impact estimates

The system combines:

Data engineering pipelines

Operational analytics

Simulation modeling

LLM-assisted reporting

into a single reproducible workflow.

System Architecture
Synthetic Data Generator

Generates realistic ITSM ticket lifecycles including priorities, handoffs, waiting states, and resolution patterns.

Data Contract and Schema Validation

Validates required columns, timestamp formats, and data types before processing.

Ingestion and Normalization

Standardizes timestamps, identifiers, and canonical dataframe structures.

Feature Engineering

Computes operational metrics including:

cycle time

queue time (first-touch delay)

idle time (waiting states)

time-in-status breakdown

handoff count

Leakage Attribution Engine

Ranks time leakage by:

team

ticket category

priority

workflow status

Intervention Simulator

Runs scenario modeling (e.g., reduce handoffs or waiting time) and estimates cost savings ranges.

Feedback Loop

Compares predicted vs observed improvements to measure simulation calibration accuracy.

Executive Narrative Generator

Produces structured executive summaries from computed metrics with fact validation to prevent hallucinations.

Streamlit Dashboard

Interactive interface for:

overview metrics

scoped team analysis

intervention simulation

executive summary generation

Key Metrics
Per Ticket

cycle_hours

queue_hours

idle_hours

handoff_count

time_in_*_hours

Aggregated Outputs

Total leakage hours by team

Leakage distribution by priority

Status-level bottlenecks

Estimated annualized cost impact

Benchmark: Automated vs Manual Analysis

Diagnosing operational inefficiencies in IT systems often requires manual data analysis.

Typical manual workflow:

Export ticket and status data

Clean timestamps

Build spreadsheet pivots

Identify bottlenecks

Estimate cost impact

This process typically requires 2–3 hours per week for a mid-sized operations team.

Automated Pipeline Performance

Using the Time Leak Detector pipeline:

Dataset size: 2,000 tickets / 13,022 status events

Full pipeline runtime: ~4 seconds

Operational insights that previously required hours of manual analysis can be produced in seconds.

Example Findings (Synthetic Dataset)

Using 2,000 simulated tickets:

P3 tickets accounted for the majority of total leakage hours

Tier1 handled the largest ticket volume and accumulated the highest leakage

IN_PROGRESS and TRIAGE represented the largest share of lifecycle time

Intervention Simulation

Scenario:

Reduce queue delays by 20%

Reduce idle time by 15%

Reduce handoffs by 25%

Estimated savings:

Scenario	Estimated Savings
Low	$924,849
Base	$929,664
High	$934,426

Simulation calibration:

Predicted savings: $929,664

Observed savings: $930,998

Prediction error: −0.14%

This demonstrates stable and reliable operational improvement estimates.

## Case Study Narrative (Synthetic Example)

In this simulated dataset (2,000 tickets), the largest leakage concentrated in **Tier1 handling high-volume P3 requests**. A recurring pattern shows tickets spending extended time in **TRIAGE → IN_PROGRESS**, with additional delay introduced during handoffs (Tier1 → Tier2) and waiting states.  

Using the simulator, we modeled an operational improvement plan: **reduce queue delays by 20%**, **reduce idle time by 15%**, and **reduce handoffs by 25%**. The model estimates **~$924K–$934K** in annualized savings, and the feedback loop shows the prediction is stable (≈ **−0.14% error** vs observed).  

This demonstrates how the pipeline turns raw ticket lifecycles into a concrete “where the time goes” story, and quantifies what a process change could return in dollars before any real rollout.

Technology Stack

Python

Pandas

NumPy

Streamlit

Pandera / Pydantic (schema validation)

OpenAI API (structured narrative generation)

How to Run
Create environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Generate synthetic data
python data/synthetic_generator.py
Run pipeline
./run.sh
Launch dashboard
PYTHONPATH=. streamlit run app/streamlit_app.py
Enable executive summary generation
export OPENAI_API_KEY=your_key_here
Project Purpose

This project demonstrates:

Operational analytics design

Time-based workflow diagnostics

Cost impact modeling

Scenario-based intervention analysis

Controlled LLM integration with validation

End-to-end analytics product thinking

It reflects a business analyst approach to diagnosing inefficiency, quantifying impact, and communicating findings in an executive-ready format.
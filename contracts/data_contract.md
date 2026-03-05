# Data Contract

This project expects two input tables:

tickets
status_history

## tickets schema

ticket_id (string) — unique identifier  
created_at (timestamp UTC) — ticket creation time  
resolved_at (timestamp UTC) — ticket resolution time  
priority (string) — allowed values: P0, P1, P2, P3  
team_id (string) — team responsible for ticket  
category (string) — ticket category

## status_history schema

ticket_id (string) — ticket identifier  
status (string) — workflow state  
status_start (timestamp UTC) — status start time  
status_end (timestamp UTC) — status end time  
assigned_team (string) — team responsible during status
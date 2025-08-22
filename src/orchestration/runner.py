"""
Orchestration runner for executing agent tasks.

This module coordinates the execution of all pending tasks for a given plan,
managing the workflow from task assignment to completion.
"""

import sqlite3
from ..agents.specialists import agent_registry
from ..models.dataModel import AgentType, TaskStatus


def run_plan(plan_id: str):
    """
    Fetches and executes all pending tasks for a given plan sequentially.
    
    Args:
        plan_id: The unique identifier for the plan to execute
    """
    print(f"Orchestrator starting run for plan_id: {plan_id}")
    
    # NOTE: You will need to build out your state store functions
    # For now, we can use direct DB calls as a placeholder
    conn = _connect()  # Your SQLite connection function from main.py
    
    try:
        # Get all pending tasks for this plan
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE plan_id = ? AND state = ?", 
            (plan_id, TaskStatus.PENDING.value)
        ).fetchall()
        
        print(f"Found {len(tasks)} pending tasks to execute")
        
        for task_data in tasks:
            task_id = task_data['task_id']
            agent_type = AgentType(task_data['agent'])
            description = task_data['description']
            
            print(f"Processing task {task_id} for agent {agent_type.value}")
            
            # 1. Get the correct agent from the registry
            agent = agent_registry.get(agent_type)
            if not agent:
                print(f"Warning: No agent found for type {agent_type}. Skipping task.")
                # Mark task as failed/escalated in DB
                conn.execute(
                    "UPDATE tasks SET state = ?, last_error = ? WHERE task_id = ?",
                    (TaskStatus.FAILED.value, f"No agent found for type {agent_type}", task_id)
                )
                conn.commit()
                continue

            # 2. Mark task as 'in_progress' in the DB
            conn.execute(
                "UPDATE tasks SET state = ? WHERE task_id = ?",
                (TaskStatus.IN_PROGRESS.value, task_id)
            )
            conn.commit()
            
            # 3. Execute the agent's task
            try:
                response = agent.execute(description)
                print(f"Agent {agent_type.value} finished. Storing response.")
                
                # 4. Record the agent's response in the DB (you'll need a new table for this)
                # and mark the task as 'completed'
                # store_agent_response(task_id, response)  # A function you'll write
                
                # For now, just mark as completed
                conn.execute(
                    "UPDATE tasks SET state = ? WHERE task_id = ?",
                    (TaskStatus.COMPLETED.value, task_id)
                )
                conn.commit()
                
                print(f"Task {task_id} completed successfully")
                
            except Exception as e:
                print(f"Error executing task {task_id}: {e}")
                # Mark task as failed
                conn.execute(
                    "UPDATE tasks SET state = ?, last_error = ? WHERE task_id = ?",
                    (TaskStatus.FAILED.value, str(e), task_id)
                )
                conn.commit()
        
        print(f"Orchestrator finished run for plan_id: {plan_id}")
        # Eventually, this will trigger the final synthesis step
        
    except Exception as e:
        print(f"Error in orchestration run: {e}")
        raise
    finally:
        conn.close()


def _connect() -> sqlite3.Connection:
    """Create a database connection."""
    # This should match the connection logic from main.py
    import os
    from pathlib import Path
    
    # Get the repo root (two levels up from this file)
    repo_root = Path(__file__).resolve().parents[2]
    state_db_path = os.environ.get("STATE_DB_PATH", "./state/the_board_state.db")
    state_db = (repo_root / state_db_path).resolve()
    
    conn = sqlite3.connect(state_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

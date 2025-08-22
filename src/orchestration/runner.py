"""
Orchestration runner for the_board multi-agent system.

This module coordinates the execution of tasks across different agent specialists,
managing the workflow from task assignment to completion.
"""

import logging
from typing import Dict, Any

from ..state.store import state_store
from ..agents.specialists import agent_registry
from ..models.dataModel import TaskStatus, AgentType
from .synthesizer import synthesize_plan

# Set up logging
logger = logging.getLogger("the_board.orchestration")

def run_plan(plan_id: str) -> Dict[str, Any]:
    """
    Execute a complete plan by orchestrating all pending tasks.
    
    Args:
        plan_id: The unique identifier for the plan to execute
        
    Returns:
        Dict containing execution summary and results
    """
    logger.info(f"[ORCHESTRATOR] Starting execution of plan: {plan_id}")
    
    try:
        # Get all pending tasks for this plan
        tasks = state_store.get_pending_tasks(plan_id)
        logger.info(f"[ORCHESTRATOR] Found {len(tasks)} pending tasks for plan {plan_id}")
        
        if not tasks:
            logger.warning(f"[ORCHESTRATOR] No pending tasks found for plan {plan_id}")
            return {
                "plan_id": plan_id,
                "status": "completed",
                "message": "No pending tasks to execute",
                "tasks_processed": 0
            }
        
        # Track execution results
        results = {
            "plan_id": plan_id,
            "status": "in_progress",
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "started_at": state_store._utc_now(),
            "completed_at": None
        }
        
        # Execute each task sequentially
        for task in tasks:
            task_id = task['task_id']
            agent_type = task['agent']
            description = task['description']
            
            logger.info(f"[ORCHESTRATOR] Processing task {task_id} with agent {agent_type}")
            
            try:
                # Update task status to in_progress
                state_store.update_task_status(task_id, TaskStatus.IN_PROGRESS.value)
                
                # Get the appropriate agent
                if agent_type not in agent_registry:
                    raise ValueError(f"Unknown agent type: {agent_type}")
                
                agent = agent_registry[agent_type]
                
                # Execute the task
                logger.info(f"[ORCHESTRATOR] Executing task {task_id} with {agent_type} agent")
                response = agent.execute(description)
                
                # Log the agent's response
                logger.info(f"[ORCHESTRATOR] Agent {agent_type} completed task {task_id} with confidence {response.confidence}")
                
                # Update task status to completed
                state_store.update_task_status(task_id, TaskStatus.COMPLETED.value)
                
                # Record successful completion
                results["tasks_succeeded"] += 1
                
                # Record the event using StateStore
                state_store.record_event(
                    plan_id, 
                    task_id, 
                    "task_completed",
                    f"Agent {agent_type} completed task successfully with confidence {response.confidence}"
                )
                
            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Task {task_id} failed: {str(e)}")
                
                # Update task status to failed with error message
                state_store.update_task_status(task_id, TaskStatus.FAILED.value, str(e))
                
                # Record failure
                results["tasks_failed"] += 1
                
                # Record the error event using StateStore
                state_store.record_event(
                    plan_id, 
                    task_id, 
                    "task_failed",
                    f"Agent {agent_type} failed: {str(e)}"
                )
            
            results["tasks_processed"] += 1
        
        # Determine final status
        if results["tasks_failed"] == 0:
            results["status"] = "completed"
            logger.info(f"[ORCHESTRATOR] Plan {plan_id} completed successfully")
        elif results["tasks_succeeded"] == 0:
            results["status"] = "failed"
            logger.error(f"[ORCHESTRATOR] Plan {plan_id} failed completely")
        else:
            results["status"] = "partially_completed"
            logger.warning(f"[ORCHESTRATOR] Plan {plan_id} partially completed with {results['tasks_failed']} failures")
        
        results["completed_at"] = state_store._utc_now()
        
        # Update plan status in the database using StateStore
        close_plan = results["status"] in ["completed", "failed"]
        state_store.update_plan_status(plan_id, results["status"], close_plan)
        
        # After the loop finishes, call the synthesizer if plan completed successfully
        if results["status"] == "completed":
            logger.info(f"All tasks for plan_id: {plan_id} are complete. Starting synthesis.")
            
            final_plan = synthesize_plan(plan_id)
            
            if final_plan:
                # Save the final plan to the database and mark the plan as 'closed'
                state_store.save_final_plan(plan_id, final_plan)
                state_store.update_plan_status(plan_id, "closed")
                logger.info(f"Synthesis complete. Plan {plan_id} is now closed.")
            else:
                # Handle synthesis failure
                state_store.update_plan_status(plan_id, "synthesis_failed")
                logger.error(f"Synthesis failed for plan {plan_id}")
        
        logger.info(f"[ORCHESTRATOR] Plan {plan_id} execution finished: {results['status']}")
        return results
        
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Critical error executing plan {plan_id}: {str(e)}")
        # Update plan status to failed
        state_store.update_plan_status(plan_id, "failed")
        raise

def get_plan_execution_status(plan_id: str) -> Dict[str, Any]:
    """
    Get the current execution status of a plan.
    
    Args:
        plan_id: The unique identifier for the plan
        
    Returns:
        Dict containing current execution status
    """
    try:
        # Use the enhanced StateStore method
        return state_store.get_plan_task_summary(plan_id)
    except Exception as e:
        logger.error(f"Failed to get plan execution status: {e}")
        return {"error": f"Failed to retrieve status: {str(e)}"}

def retry_failed_task(task_id: str) -> Dict[str, Any]:
    """
    Retry a failed task by resetting its status and incrementing attempts.
    
    Args:
        task_id: The unique identifier for the task to retry
        
    Returns:
        Dict containing retry status
    """
    try:
        # Get the task details
        task = state_store.get_task_by_id(task_id)
        if not task:
            return {"error": "Task not found"}
        
        if task['state'] not in ['failed', 'escalated', 'cancelled']:
            return {"error": "Task cannot be retried from current state"}
        
        # Increment attempts and reset status
        state_store.increment_task_attempts(task_id)
        state_store.update_task_status(task_id, TaskStatus.PENDING.value)
        
        # Record retry event
        state_store.record_event(
            task['plan_id'], 
            task_id, 
            "task_retry",
            f"Task retry initiated, attempt {task['attempts'] + 1}"
        )
        
        return {
            "task_id": task_id,
            "status": "retry_initiated",
            "new_state": "pending",
            "attempts": task['attempts'] + 1
        }
        
    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}")
        return {"error": f"Failed to retry task: {str(e)}"}

def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a task by setting its status to cancelled.
    
    Args:
        task_id: The unique identifier for the task to cancel
        
    Returns:
        Dict containing cancellation status
    """
    try:
        # Get the task details
        task = state_store.get_task_by_id(task_id)
        if not task:
            return {"error": "Task not found"}
        
        if task['state'] in ['completed', 'cancelled']:
            return {"error": "Task cannot be cancelled from current state"}
        
        # Cancel the task
        state_store.update_task_status(task_id, TaskStatus.CANCELLED.value)
        
        # Record cancellation event
        state_store.record_event(
            task['plan_id'], 
            task_id, 
            "task_cancelled",
            "Task cancelled by user request"
        )
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task successfully cancelled"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return {"error": f"Failed to cancel task: {str(e)}"}

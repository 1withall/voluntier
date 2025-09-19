"""Specialized workflows for telemetry, onboarding, and other support functions."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

from .activities import (
    data_activities,
    notification_activities,
    security_activities,
    volunteer_activities,
)
from .schemas import (
    TelemetryEventRequest,
    OnboardingProgressRequest,
)


@workflow.defn
class TelemetryTrackingWorkflow:
    """Workflow for processing telemetry events."""
    
    @workflow.run
    async def run(self, request: TelemetryEventRequest) -> Dict[str, Any]:
        """
        Telemetry tracking workflow.
        
        Args:
            request: Telemetry event request
            
        Returns:
            Telemetry processing result
        """
        workflow.logger.info(f"Processing telemetry event: {request.event_type}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=1.5,
            maximum_interval=timedelta(seconds=15),
            maximum_attempts=2,  # Don't retry telemetry too much
        )
        
        try:
            # Step 1: Store telemetry event
            telemetry_result = await workflow.execute_activity(
                data_activities.store_telemetry_event,
                {
                    "user_id": request.user_id,
                    "event_type": request.event_type,
                    "category": request.category,
                    "label": request.label,
                    "value": request.value,
                    "metadata": request.metadata,
                    "timestamp": request.timestamp.isoformat(),
                },
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            # Step 2: Update user analytics (if user_id provided)
            if request.user_id:
                analytics_result = await workflow.execute_activity(
                    data_activities.update_user_analytics,
                    {
                        "user_id": request.user_id,
                        "event_type": request.event_type,
                        "category": request.category,
                        "timestamp": request.timestamp.isoformat(),
                    },
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy,
                )
            
            # Step 3: Check for anomalies in user behavior (security)
            if request.user_id and request.category in ["authentication", "security", "events"]:
                anomaly_check = await workflow.execute_activity(
                    security_activities.check_user_behavior_anomaly,
                    {
                        "user_id": request.user_id,
                        "event_type": request.event_type,
                        "metadata": request.metadata,
                        "timestamp": request.timestamp.isoformat(),
                    },
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy,
                )
                
                # If anomaly detected, trigger security alert
                if anomaly_check.get("anomaly_detected"):
                    security_alert = {
                        "threat_type": "behavioral_anomaly",
                        "severity": "medium",
                        "description": f"Behavioral anomaly detected for user {request.user_id}",
                        "affected_resources": [request.user_id],
                        "metadata": {
                            "anomaly_details": anomaly_check,
                            "triggering_event": request.dict(),
                        },
                    }
                    
                    workflow.start_activity(
                        security_activities.log_security_event,
                        {
                            "event_type": "behavioral_anomaly",
                            "details": security_alert,
                            "user_id": request.user_id,
                        },
                        start_to_close_timeout=timedelta(minutes=1),
                        retry_policy=retry_policy,
                    )
            
            return {
                "success": True,
                "event_id": telemetry_result.get("event_id"),
                "processed_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            workflow.logger.error(f"Telemetry tracking workflow failed: {str(e)}")
            # Don't fail hard on telemetry - just log and continue
            return {
                "success": False,
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat(),
            }


@workflow.defn
class OnboardingWorkflow:
    """Workflow for managing user onboarding progress."""
    
    @workflow.run
    async def run(self, request: OnboardingProgressRequest) -> Dict[str, Any]:
        """
        Onboarding progress workflow.
        
        Args:
            request: Onboarding progress request
            
        Returns:
            Onboarding progress result
        """
        workflow.logger.info(f"Processing onboarding for user: {request.user_id}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )
        
        try:
            # Step 1: Update onboarding progress
            progress_result = await workflow.execute_activity(
                volunteer_activities.update_onboarding_progress,
                {
                    "user_id": request.user_id,
                    "user_type": request.user_type,
                    "completed_steps": request.completed_steps,
                    "current_step": request.current_step,
                },
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            # Step 2: Check if onboarding is complete
            if progress_result.get("onboarding_complete"):
                # Send completion notification
                completion_notification = {
                    "user_id": request.user_id,
                    "type": "onboarding_complete",
                    "content": {
                        "subject": "Welcome to Voluntier! Onboarding Complete",
                        "message": "Congratulations! You've successfully completed the onboarding process.",
                        "next_steps": progress_result.get("next_steps", []),
                    },
                    "delivery_method": "email",
                }
                
                await workflow.execute_activity(
                    notification_activities.send_notification,
                    completion_notification,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry_policy,
                )
                
                # Update user status to fully onboarded
                await workflow.execute_activity(
                    volunteer_activities.update_user_status,
                    {
                        "user_id": request.user_id,
                        "status": "onboarded",
                        "metadata": {
                            "onboarding_completed_at": datetime.utcnow().isoformat(),
                            "completed_steps": request.completed_steps,
                        },
                    },
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy,
                )
            
            # Step 3: Check for next step recommendations
            elif request.current_step:
                next_step_recommendations = await workflow.execute_activity(
                    volunteer_activities.get_onboarding_recommendations,
                    {
                        "user_id": request.user_id,
                        "user_type": request.user_type,
                        "current_step": request.current_step,
                        "completed_steps": request.completed_steps,
                    },
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy,
                )
                
                # Send reminder notification if user has stalled
                if next_step_recommendations.get("send_reminder"):
                    reminder_notification = {
                        "user_id": request.user_id,
                        "type": "onboarding_reminder",
                        "content": {
                            "subject": "Complete Your Voluntier Setup",
                            "message": next_step_recommendations.get("reminder_message"),
                            "next_step": next_step_recommendations.get("next_step"),
                        },
                        "delivery_method": "email",
                    }
                    
                    workflow.start_activity(
                        notification_activities.send_notification,
                        reminder_notification,
                        start_to_close_timeout=timedelta(minutes=2),
                        retry_policy=retry_policy,
                    )
            
            return {
                "success": True,
                "progress_updated": True,
                "onboarding_complete": progress_result.get("onboarding_complete", False),
                "next_steps": progress_result.get("next_steps", []),
                "completion_percentage": progress_result.get("completion_percentage", 0),
            }
            
        except Exception as e:
            workflow.logger.error(f"Onboarding workflow failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }


@workflow.defn
class SystemMaintenanceWorkflow:
    """Workflow for scheduled system maintenance tasks."""
    
    @workflow.run
    async def run(self, maintenance_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        System maintenance workflow.
        
        Args:
            maintenance_config: Maintenance configuration
            
        Returns:
            Maintenance result
        """
        workflow.logger.info("Starting system maintenance workflow")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=2),
            maximum_attempts=3,
        )
        
        maintenance_results = []
        
        try:
            # Step 1: Database maintenance
            if maintenance_config.get("database_maintenance", True):
                db_maintenance_result = await workflow.execute_activity(
                    data_activities.perform_database_maintenance,
                    {
                        "vacuum_tables": True,
                        "analyze_tables": True,
                        "reindex_tables": True,
                        "cleanup_old_data": True,
                        "retention_days": maintenance_config.get("retention_days", 90),
                    },
                    start_to_close_timeout=timedelta(minutes=30),
                    retry_policy=retry_policy,
                )
                maintenance_results.append({"task": "database_maintenance", "result": db_maintenance_result})
            
            # Step 2: Security scan
            if maintenance_config.get("security_scan", True):
                security_scan_result = await workflow.execute_activity(
                    security_activities.perform_security_scan,
                    {
                        "scan_type": "comprehensive",
                        "include_vulnerability_scan": True,
                        "include_log_analysis": True,
                    },
                    start_to_close_timeout=timedelta(minutes=20),
                    retry_policy=retry_policy,
                )
                maintenance_results.append({"task": "security_scan", "result": security_scan_result})
            
            # Step 3: Data backup
            if maintenance_config.get("backup", True):
                backup_result = await workflow.execute_activity(
                    data_activities.create_backup,
                    {
                        "backup_type": "incremental",
                        "include_logs": True,
                        "compress": True,
                    },
                    start_to_close_timeout=timedelta(minutes=45),
                    retry_policy=retry_policy,
                )
                maintenance_results.append({"task": "backup", "result": backup_result})
            
            # Step 4: Analytics processing
            if maintenance_config.get("analytics_processing", True):
                analytics_result = await workflow.execute_activity(
                    data_activities.process_analytics_batch,
                    {
                        "batch_size": 10000,
                        "process_user_analytics": True,
                        "process_event_analytics": True,
                        "generate_reports": True,
                    },
                    start_to_close_timeout=timedelta(minutes=15),
                    retry_policy=retry_policy,
                )
                maintenance_results.append({"task": "analytics_processing", "result": analytics_result})
            
            # Step 5: Memory optimization
            if maintenance_config.get("memory_optimization", True):
                memory_optimization_result = await workflow.execute_activity(
                    data_activities.optimize_memory_storage,
                    {
                        "cleanup_old_embeddings": True,
                        "optimize_graph_storage": True,
                        "rebuild_indexes": True,
                    },
                    start_to_close_timeout=timedelta(minutes=20),
                    retry_policy=retry_policy,
                )
                maintenance_results.append({"task": "memory_optimization", "result": memory_optimization_result})
            
            # Step 6: Generate maintenance report
            report_result = await workflow.execute_activity(
                data_activities.generate_maintenance_report,
                {
                    "maintenance_results": maintenance_results,
                    "start_time": maintenance_config.get("start_time", datetime.utcnow().isoformat()),
                    "end_time": datetime.utcnow().isoformat(),
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            
            # Step 7: Send maintenance completion notification to admins
            notification_data = {
                "user_id": "admin",
                "type": "maintenance_complete",
                "content": {
                    "subject": "System Maintenance Complete",
                    "message": "Scheduled system maintenance has been completed successfully.",
                    "report": report_result,
                    "tasks_completed": len(maintenance_results),
                },
                "delivery_method": "email",
            }
            
            workflow.start_activity(
                notification_activities.send_notification,
                notification_data,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            workflow.logger.info("System maintenance workflow completed successfully")
            
            return {
                "success": True,
                "tasks_completed": len(maintenance_results),
                "maintenance_results": maintenance_results,
                "report": report_result,
                "completed_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            workflow.logger.error(f"System maintenance workflow failed: {str(e)}")
            
            # Send failure notification
            failure_notification = {
                "user_id": "admin",
                "type": "maintenance_failed",
                "content": {
                    "subject": "System Maintenance Failed",
                    "message": f"Scheduled system maintenance failed: {str(e)}",
                    "partial_results": maintenance_results,
                    "error": str(e),
                },
                "delivery_method": "email",
                "priority": "high",
            }
            
            workflow.start_activity(
                notification_activities.send_notification,
                failure_notification,
                start_to_close_timeout=timedelta(minutes=2),
            )
            
            return {
                "success": False,
                "error": str(e),
                "partial_results": maintenance_results,
                "failed_at": datetime.utcnow().isoformat(),
            }


@workflow.defn
class HealthCheckWorkflow:
    """Workflow for system health monitoring."""
    
    @workflow.run
    async def run(self, health_check_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        System health check workflow.
        
        Args:
            health_check_config: Health check configuration
            
        Returns:
            Health check result
        """
        workflow.logger.info("Starting system health check workflow")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=1.5,
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=2,
        )
        
        health_results = []
        overall_health = "healthy"
        
        try:
            # Check database health
            db_health = await workflow.execute_activity(
                data_activities.check_database_health,
                {},
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            health_results.append({"component": "database", "status": db_health})
            
            if db_health.get("status") != "healthy":
                overall_health = "degraded"
            
            # Check memory system health
            memory_health = await workflow.execute_activity(
                data_activities.check_memory_system_health,
                {},
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            health_results.append({"component": "memory_system", "status": memory_health})
            
            if memory_health.get("status") != "healthy":
                overall_health = "degraded"
            
            # Check security system health
            security_health = await workflow.execute_activity(
                security_activities.check_security_system_health,
                {},
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            health_results.append({"component": "security_system", "status": security_health})
            
            if security_health.get("status") != "healthy":
                overall_health = "critical" if security_health.get("status") == "critical" else "degraded"
            
            return {
                "overall_health": overall_health,
                "components": health_results,
                "checked_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            workflow.logger.error(f"Health check workflow failed: {str(e)}")
            return {
                "overall_health": "critical",
                "error": str(e),
                "partial_results": health_results,
                "checked_at": datetime.utcnow().isoformat(),
            }
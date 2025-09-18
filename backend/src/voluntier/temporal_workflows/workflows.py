"""Core Temporal workflows for Voluntier platform."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from temporalio import workflow
from temporalio.common import RetryPolicy

from .activities import (
    volunteer_activities,
    event_activities,
    notification_activities,
    security_activities,
    data_activities,
    llm_activities,
)
from .schemas import (
    VolunteerRegistrationRequest,
    EventCreationRequest,
    NotificationRequest,
    SecurityThreatAlert,
    DataSyncRequest,
    AgentDecisionRequest,
)


@workflow.defn
class VolunteerManagementWorkflow:
    """Workflow for managing volunteer lifecycle operations."""
    
    @workflow.run
    async def run(self, request: VolunteerRegistrationRequest) -> Dict[str, Any]:
        """
        Main workflow for volunteer management.
        
        Args:
            request: Volunteer registration request
            
        Returns:
            Result of volunteer management process
        """
        workflow.logger.info(f"Starting volunteer management for user {request.user_id}")
        
        # Create retry policy
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )
        
        try:
            # Step 1: Validate user data
            validation_result = await workflow.execute_activity(
                volunteer_activities.validate_user_profile,
                request.profile_data,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            if not validation_result["valid"]:
                workflow.logger.warning(f"Validation failed: {validation_result['errors']}")
                return {"status": "failed", "reason": "validation_failed", "errors": validation_result["errors"]}
            
            # Step 2: Check for duplicate registration
            duplicate_check = await workflow.execute_activity(
                volunteer_activities.check_duplicate_registration,
                request.profile_data["email"],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            if duplicate_check["is_duplicate"]:
                workflow.logger.warning(f"Duplicate registration attempt for {request.profile_data['email']}")
                return {"status": "failed", "reason": "duplicate_registration"}
            
            # Step 3: Create user profile
            user_creation_result = await workflow.execute_activity(
                volunteer_activities.create_user_profile,
                request.profile_data,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            
            # Step 4: Initialize verification process
            verification_request = {
                "user_id": user_creation_result["user_id"],
                "verification_type": "email",
                "metadata": {"email": request.profile_data["email"]},
            }
            
            verification_result = await workflow.execute_activity(
                volunteer_activities.initiate_verification,
                verification_request,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            # Step 5: Send welcome notification
            welcome_notification = NotificationRequest(
                user_id=user_creation_result["user_id"],
                type="welcome",
                content={
                    "subject": "Welcome to Voluntier!",
                    "message": "Thank you for joining our community. Please check your email to verify your account.",
                },
                delivery_method="email",
            )
            
            await workflow.execute_activity(
                notification_activities.send_notification,
                welcome_notification,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            # Step 6: Update community graph
            graph_update_request = {
                "user_id": user_creation_result["user_id"],
                "action": "add_volunteer",
                "metadata": {
                    "skills": request.profile_data.get("skills", []),
                    "interests": request.profile_data.get("interests", []),
                    "location": request.profile_data.get("location"),
                },
            }
            
            await workflow.execute_activity(
                data_activities.update_community_graph,
                graph_update_request,
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=retry_policy,
            )
            
            workflow.logger.info(f"Successfully completed volunteer registration for user {user_creation_result['user_id']}")
            
            return {
                "status": "success",
                "user_id": user_creation_result["user_id"],
                "verification_token": verification_result["token"],
                "next_steps": [
                    "verify_email",
                    "complete_profile",
                    "browse_opportunities",
                ],
            }
            
        except Exception as e:
            workflow.logger.error(f"Volunteer management workflow failed: {str(e)}")
            return {"status": "error", "message": str(e)}


@workflow.defn
class EventManagementWorkflow:
    """Workflow for managing event lifecycle operations."""
    
    @workflow.run
    async def run(self, request: EventCreationRequest) -> Dict[str, Any]:
        """
        Main workflow for event management.
        
        Args:
            request: Event creation request
            
        Returns:
            Result of event management process
        """
        workflow.logger.info(f"Starting event management for organizer {request.organizer_id}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )
        
        try:
            # Step 1: Validate event data
            validation_result = await workflow.execute_activity(
                event_activities.validate_event_data,
                request.event_data,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            if not validation_result["valid"]:
                return {"status": "failed", "reason": "validation_failed", "errors": validation_result["errors"]}
            
            # Step 2: Check organizer permissions
            permission_check = await workflow.execute_activity(
                event_activities.check_organizer_permissions,
                {"organizer_id": request.organizer_id, "organization_id": request.event_data.get("organization_id")},
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            if not permission_check["authorized"]:
                return {"status": "failed", "reason": "unauthorized"}
            
            # Step 3: Create event
            event_creation_result = await workflow.execute_activity(
                event_activities.create_event,
                request.event_data,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            
            event_id = event_creation_result["event_id"]
            
            # Step 4: If event is published, trigger additional workflows
            if request.event_data.get("status") == "published":
                # Update community graph
                graph_update_request = {
                    "event_id": event_id,
                    "action": "add_event",
                    "metadata": {
                        "categories": request.event_data.get("categories", []),
                        "skills": request.event_data.get("required_skills", []),
                        "location": request.event_data.get("location"),
                    },
                }
                
                await workflow.execute_activity(
                    data_activities.update_community_graph,
                    graph_update_request,
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=retry_policy,
                )
                
                # Schedule volunteer matching
                await workflow.execute_activity(
                    event_activities.schedule_volunteer_matching,
                    {"event_id": event_id},
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry_policy,
                )
                
                # Send notifications to interested volunteers
                matching_request = {
                    "event_id": event_id,
                    "criteria": {
                        "skills": request.event_data.get("required_skills", []),
                        "interests": request.event_data.get("categories", []),
                        "location": request.event_data.get("location"),
                    },
                }
                
                volunteer_matches = await workflow.execute_activity(
                    volunteer_activities.find_matching_volunteers,
                    matching_request,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                
                # Send notifications to matched volunteers
                for volunteer_id in volunteer_matches["matches"]:
                    notification = NotificationRequest(
                        user_id=volunteer_id,
                        type="event_opportunity",
                        content={
                            "subject": f"New Volunteer Opportunity: {request.event_data['title']}",
                            "event_id": event_id,
                            "event_title": request.event_data["title"],
                        },
                        delivery_method="email",
                    )
                    
                    await workflow.execute_activity(
                        notification_activities.send_notification,
                        notification,
                        start_to_close_timeout=timedelta(minutes=1),
                        retry_policy=retry_policy,
                    )
            
            workflow.logger.info(f"Successfully created event {event_id}")
            
            return {
                "status": "success",
                "event_id": event_id,
                "matches_found": len(volunteer_matches.get("matches", [])) if 'volunteer_matches' in locals() else 0,
            }
            
        except Exception as e:
            workflow.logger.error(f"Event management workflow failed: {str(e)}")
            return {"status": "error", "message": str(e)}


@workflow.defn
class NotificationWorkflow:
    """Workflow for managing notification delivery."""
    
    @workflow.run
    async def run(self, request: NotificationRequest) -> Dict[str, Any]:
        """
        Main workflow for notification management.
        
        Args:
            request: Notification request
            
        Returns:
            Result of notification delivery
        """
        workflow.logger.info(f"Processing notification for user {request.user_id}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=2),
            maximum_attempts=5,
        )
        
        try:
            # Step 1: Get user preferences
            user_preferences = await workflow.execute_activity(
                notification_activities.get_user_preferences,
                request.user_id,
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            # Step 2: Check if user allows this type of notification
            if not user_preferences.get("notifications", {}).get(request.type, True):
                workflow.logger.info(f"User {request.user_id} has disabled {request.type} notifications")
                return {"status": "skipped", "reason": "user_preference"}
            
            # Step 3: Personalize content if needed
            if request.content.get("personalize", False):
                personalized_content = await workflow.execute_activity(
                    llm_activities.personalize_content,
                    {
                        "user_id": request.user_id,
                        "content": request.content,
                        "user_preferences": user_preferences,
                    },
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry_policy,
                )
                request.content = personalized_content["content"]
            
            # Step 4: Send notification
            delivery_result = await workflow.execute_activity(
                notification_activities.send_notification,
                request,
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=retry_policy,
            )
            
            # Step 5: Log delivery
            await workflow.execute_activity(
                notification_activities.log_notification_delivery,
                {
                    "user_id": request.user_id,
                    "notification_type": request.type,
                    "delivery_method": request.delivery_method,
                    "status": delivery_result["status"],
                    "metadata": delivery_result.get("metadata", {}),
                },
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            return delivery_result
            
        except Exception as e:
            workflow.logger.error(f"Notification workflow failed: {str(e)}")
            return {"status": "error", "message": str(e)}


@workflow.defn
class SecurityMonitoringWorkflow:
    """Workflow for security monitoring and threat response."""
    
    @workflow.run
    async def run(self, alert: SecurityThreatAlert) -> Dict[str, Any]:
        """
        Main workflow for security monitoring.
        
        Args:
            alert: Security threat alert
            
        Returns:
            Result of security response
        """
        workflow.logger.warning(f"Processing security alert: {alert.threat_type}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=1.5,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=5,
        )
        
        try:
            # Step 1: Analyze threat severity
            threat_analysis = await workflow.execute_activity(
                security_activities.analyze_threat,
                alert,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            severity = threat_analysis["severity"]
            workflow.logger.info(f"Threat severity assessed as: {severity}")
            
            # Step 2: Immediate automated response for high-severity threats
            if severity in ["high", "critical"]:
                automated_response = await workflow.execute_activity(
                    security_activities.execute_automated_response,
                    {"alert": alert, "analysis": threat_analysis},
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy,
                )
                
                # Step 3: Alert administrators for critical threats
                if severity == "critical":
                    admin_notification = NotificationRequest(
                        user_id="admin",  # Special admin user
                        type="security_alert",
                        content={
                            "subject": f"CRITICAL Security Alert: {alert.threat_type}",
                            "alert_data": alert.dict(),
                            "analysis": threat_analysis,
                            "automated_response": automated_response,
                        },
                        delivery_method="email",
                        priority="high",
                    )
                    
                    # Send notification without waiting
                    workflow.start_activity(
                        notification_activities.send_notification,
                        admin_notification,
                        start_to_close_timeout=timedelta(minutes=2),
                        retry_policy=retry_policy,
                    )
            
            # Step 4: Update security metrics
            await workflow.execute_activity(
                security_activities.update_security_metrics,
                {
                    "threat_type": alert.threat_type,
                    "severity": severity,
                    "response_time": (datetime.utcnow() - alert.timestamp).total_seconds(),
                    "automated_response": severity in ["high", "critical"],
                },
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            # Step 5: Learn from incident
            learning_request = {
                "alert": alert,
                "analysis": threat_analysis,
                "response_effectiveness": threat_analysis.get("response_effectiveness", "unknown"),
            }
            
            await workflow.execute_activity(
                security_activities.update_threat_intelligence,
                learning_request,
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=retry_policy,
            )
            
            return {
                "status": "processed",
                "severity": severity,
                "automated_response": severity in ["high", "critical"],
                "human_intervention_required": severity == "critical",
            }
            
        except Exception as e:
            workflow.logger.error(f"Security monitoring workflow failed: {str(e)}")
            # For security workflows, we still want to alert on failures
            return {"status": "error", "message": str(e), "requires_attention": True}


@workflow.defn
class AgentOrchestrationWorkflow:
    """Meta-workflow for autonomous agent decision-making and orchestration."""
    
    @workflow.run
    async def run(self, request: AgentDecisionRequest) -> Dict[str, Any]:
        """
        Main workflow for agent orchestration.
        
        Args:
            request: Agent decision request
            
        Returns:
            Result of agent decision and orchestration
        """
        workflow.logger.info(f"Processing agent decision for context: {request.context}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )
        
        try:
            # Step 1: Analyze context and determine appropriate action
            decision_analysis = await workflow.execute_activity(
                llm_activities.analyze_context_and_decide,
                {
                    "context": request.context,
                    "available_actions": request.available_actions,
                    "constraints": request.constraints,
                    "historical_data": request.historical_data,
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            
            recommended_action = decision_analysis["recommended_action"]
            confidence = decision_analysis["confidence"]
            reasoning = decision_analysis["reasoning"]
            
            workflow.logger.info(f"Agent recommends: {recommended_action} (confidence: {confidence})")
            
            # Step 2: Check if human approval is required
            requires_approval = await workflow.execute_activity(
                llm_activities.check_human_approval_required,
                {
                    "action": recommended_action,
                    "context": request.context,
                    "confidence": confidence,
                },
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            if requires_approval["required"]:
                workflow.logger.info(f"Human approval required for action: {recommended_action}")
                
                # Send approval request to appropriate human
                approval_notification = NotificationRequest(
                    user_id=requires_approval["approver_id"],
                    type="approval_request",
                    content={
                        "subject": f"Agent Action Approval Required: {recommended_action}",
                        "context": request.context,
                        "recommended_action": recommended_action,
                        "reasoning": reasoning,
                        "confidence": confidence,
                        "approval_token": requires_approval["approval_token"],
                    },
                    delivery_method="email",
                    priority="high",
                )
                
                await workflow.execute_activity(
                    notification_activities.send_notification,
                    approval_notification,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry_policy,
                )
                
                # Wait for approval with timeout
                approval_result = await workflow.wait_condition(
                    lambda: self._check_approval_status(requires_approval["approval_token"]),
                    timeout=timedelta(hours=24),  # 24-hour timeout for human approval
                )
                
                if not approval_result:
                    workflow.logger.warning(f"Approval timeout for action: {recommended_action}")
                    return {"status": "timeout", "action": recommended_action, "reason": "approval_timeout"}
                
                if approval_result["status"] != "approved":
                    workflow.logger.info(f"Action rejected: {recommended_action}")
                    return {"status": "rejected", "action": recommended_action, "reason": approval_result.get("reason")}
            
            # Step 3: Execute the approved/auto-approved action
            execution_result = await workflow.execute_activity(
                llm_activities.execute_agent_action,
                {
                    "action": recommended_action,
                    "context": request.context,
                    "parameters": decision_analysis.get("parameters", {}),
                },
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )
            
            # Step 4: Monitor execution and learn from results
            monitoring_request = {
                "action": recommended_action,
                "execution_result": execution_result,
                "context": request.context,
                "predicted_outcome": decision_analysis.get("predicted_outcome"),
            }
            
            await workflow.execute_activity(
                llm_activities.monitor_and_learn,
                monitoring_request,
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=retry_policy,
            )
            
            return {
                "status": "executed",
                "action": recommended_action,
                "execution_result": execution_result,
                "confidence": confidence,
                "human_approved": requires_approval.get("required", False),
            }
            
        except Exception as e:
            workflow.logger.error(f"Agent orchestration workflow failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _check_approval_status(self, approval_token: str) -> Optional[Dict[str, Any]]:
        """Check if approval has been granted for the given token."""
        try:
            approval_status = await workflow.execute_activity(
                llm_activities.get_approval_status,
                {"approval_token": approval_token},
                start_to_close_timeout=timedelta(seconds=30),
            )
            return approval_status if approval_status["status"] != "pending" else None
        except Exception:
            return None


@workflow.defn
class DataSyncWorkflow:
    """Workflow for data synchronization across different systems."""
    
    @workflow.run
    async def run(self, request: DataSyncRequest) -> Dict[str, Any]:
        """
        Main workflow for data synchronization.
        
        Args:
            request: Data sync request
            
        Returns:
            Result of data synchronization
        """
        workflow.logger.info(f"Starting data sync: {request.sync_type}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )
        
        try:
            # Step 1: Validate sync request
            validation_result = await workflow.execute_activity(
                data_activities.validate_sync_request,
                request,
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            if not validation_result["valid"]:
                return {"status": "failed", "reason": "validation_failed", "errors": validation_result["errors"]}
            
            # Step 2: Create backup before sync
            backup_result = await workflow.execute_activity(
                data_activities.create_backup,
                {"sync_type": request.sync_type, "tables": request.target_tables},
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )
            
            # Step 3: Execute synchronization
            sync_result = await workflow.execute_activity(
                data_activities.execute_sync,
                request,
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
            )
            
            # Step 4: Validate sync results
            validation_result = await workflow.execute_activity(
                data_activities.validate_sync_results,
                {
                    "sync_type": request.sync_type,
                    "sync_result": sync_result,
                    "expected_changes": request.expected_changes,
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            
            if not validation_result["valid"]:
                # Rollback if validation fails
                await workflow.execute_activity(
                    data_activities.rollback_sync,
                    {"backup_id": backup_result["backup_id"]},
                    start_to_close_timeout=timedelta(minutes=15),
                    retry_policy=retry_policy,
                )
                return {"status": "rolled_back", "reason": "validation_failed", "errors": validation_result["errors"]}
            
            # Step 5: Update system metrics
            await workflow.execute_activity(
                data_activities.update_sync_metrics,
                {
                    "sync_type": request.sync_type,
                    "records_processed": sync_result["records_processed"],
                    "execution_time": sync_result["execution_time"],
                    "status": "success",
                },
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            return {
                "status": "success",
                "records_processed": sync_result["records_processed"],
                "execution_time": sync_result["execution_time"],
                "backup_id": backup_result["backup_id"],
            }
            
        except Exception as e:
            workflow.logger.error(f"Data sync workflow failed: {str(e)}")
            return {"status": "error", "message": str(e)}
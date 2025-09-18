"""LLM and AI activities for autonomous decision-making."""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from temporalio import activity
import httpx

from voluntier.config import settings
from voluntier.services.llm import LLMService
from voluntier.services.memory import MemoryService
from voluntier.services.approval import ApprovalService
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)


class LLMActivities:
    """Activities related to LLM and AI operations."""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.memory_service = MemoryService()
        self.approval_service = ApprovalService()
    
    @activity.defn
    async def analyze_context_and_decide(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze context and make autonomous decisions.
        
        Args:
            request: Context and decision parameters
            
        Returns:
            Decision analysis and recommendation
        """
        context = request["context"]
        available_actions = request["available_actions"]
        constraints = request.get("constraints", {})
        historical_data = request.get("historical_data", {})
        
        logger.info(f"Analyzing context for decision-making: {context.get('scenario', 'unknown')}")
        
        try:
            # Retrieve relevant memory context
            memory_context = await self.memory_service.get_relevant_context(
                query=json.dumps(context),
                limit=10,
                include_related=True,
            )
            
            # Build comprehensive prompt for decision analysis
            prompt = self._build_decision_prompt(
                context=context,
                available_actions=available_actions,
                constraints=constraints,
                historical_data=historical_data,
                memory_context=memory_context,
            )
            
            # Get LLM analysis
            analysis_result = await self.llm_service.analyze(
                prompt=prompt,
                model="gpt-4o",
                temperature=0.3,  # Lower temperature for more deterministic decisions
                max_tokens=1500,
                json_mode=True,
            )
            
            # Parse and validate the analysis
            analysis_data = json.loads(analysis_result)
            
            # Validate that recommended action is in available actions
            recommended_action = analysis_data.get("recommended_action")
            if recommended_action not in available_actions:
                logger.warning(f"LLM recommended unavailable action: {recommended_action}")
                # Fall back to a safe default action
                recommended_action = available_actions[0] if available_actions else "no_action"
                analysis_data["recommended_action"] = recommended_action
                analysis_data["confidence"] = max(0.1, analysis_data.get("confidence", 0.5) * 0.5)
                analysis_data["reasoning"] += f" (Fallback to {recommended_action} due to invalid recommendation)"
            
            # Store decision context in memory for future reference
            await self.memory_service.store_decision_context(
                context=context,
                decision=analysis_data,
                timestamp=datetime.utcnow(),
            )
            
            return {
                "recommended_action": recommended_action,
                "confidence": analysis_data.get("confidence", 0.5),
                "reasoning": analysis_data.get("reasoning", ""),
                "predicted_outcome": analysis_data.get("predicted_outcome", ""),
                "risk_assessment": analysis_data.get("risk_assessment", {}),
                "parameters": analysis_data.get("parameters", {}),
                "alternative_actions": analysis_data.get("alternative_actions", []),
                "metadata": {
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "memory_contexts_used": len(memory_context),
                    "model_used": "gpt-4o",
                },
            }
        
        except Exception as e:
            logger.error(f"Failed to analyze context and decide: {str(e)}")
            # Return a safe fallback decision
            return {
                "recommended_action": available_actions[0] if available_actions else "no_action",
                "confidence": 0.1,
                "reasoning": f"Analysis failed: {str(e)}. Defaulting to safe action.",
                "predicted_outcome": "uncertain",
                "risk_assessment": {"level": "high", "reason": "analysis_failure"},
                "parameters": {},
                "alternative_actions": [],
                "error": str(e),
            }
    
    @activity.defn
    async def check_human_approval_required(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if human approval is required for an action.
        
        Args:
            request: Action and context details
            
        Returns:
            Approval requirement assessment
        """
        action = request["action"]
        context = request["context"]
        confidence = request.get("confidence", 0.5)
        
        logger.info(f"Checking approval requirements for action: {action}")
        
        try:
            # Check against configured approval requirements
            requires_approval = (
                action in settings.agent.human_approval_required
                or confidence < 0.7  # Low confidence requires approval
                or context.get("risk_level") == "high"
                or context.get("financial_impact", 0) > 1000  # High financial impact
                or context.get("user_data_involved", False)  # User data operations
            )
            
            if not requires_approval:
                return {"required": False}
            
            # Determine appropriate approver
            approver_id = await self._determine_approver(action, context)
            
            # Generate approval token
            approval_token = str(uuid.uuid4())
            
            # Store approval request
            await self.approval_service.create_approval_request(
                token=approval_token,
                action=action,
                context=context,
                approver_id=approver_id,
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )
            
            return {
                "required": True,
                "approver_id": approver_id,
                "approval_token": approval_token,
                "reason": self._get_approval_reason(action, context, confidence),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Failed to check approval requirements: {str(e)}")
            # Default to requiring approval on error
            return {
                "required": True,
                "approver_id": "admin",
                "approval_token": str(uuid.uuid4()),
                "reason": f"Error in approval check: {str(e)}",
                "error": str(e),
            }
    
    @activity.defn
    async def execute_agent_action(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an approved agent action.
        
        Args:
            request: Action execution details
            
        Returns:
            Execution result
        """
        action = request["action"]
        context = request["context"]
        parameters = request.get("parameters", {})
        
        logger.info(f"Executing agent action: {action}")
        
        try:
            # Route to appropriate execution handler
            if action == "send_notification":
                result = await self._execute_notification_action(context, parameters)
            elif action == "update_user_profile":
                result = await self._execute_profile_update_action(context, parameters)
            elif action == "create_event":
                result = await self._execute_event_creation_action(context, parameters)
            elif action == "moderate_content":
                result = await self._execute_content_moderation_action(context, parameters)
            elif action == "optimize_matching":
                result = await self._execute_matching_optimization_action(context, parameters)
            elif action == "generate_report":
                result = await self._execute_report_generation_action(context, parameters)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # Log successful execution
            await self.memory_service.store_execution_result(
                action=action,
                context=context,
                parameters=parameters,
                result=result,
                timestamp=datetime.utcnow(),
            )
            
            return {
                "success": True,
                "action": action,
                "result": result,
                "execution_timestamp": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Failed to execute agent action {action}: {str(e)}")
            return {
                "success": False,
                "action": action,
                "error": str(e),
                "execution_timestamp": datetime.utcnow().isoformat(),
            }
    
    @activity.defn
    async def monitor_and_learn(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor action execution results and learn from outcomes.
        
        Args:
            request: Monitoring and learning request
            
        Returns:
            Learning insights
        """
        action = request["action"]
        execution_result = request["execution_result"]
        context = request["context"]
        predicted_outcome = request.get("predicted_outcome")
        
        logger.info(f"Monitoring and learning from action: {action}")
        
        try:
            # Analyze actual vs predicted outcome
            outcome_analysis = await self._analyze_outcome_accuracy(
                predicted=predicted_outcome,
                actual=execution_result,
                context=context,
            )
            
            # Update decision models based on results
            learning_insights = await self._extract_learning_insights(
                action=action,
                context=context,
                execution_result=execution_result,
                outcome_analysis=outcome_analysis,
            )
            
            # Store learning data for future decisions
            await self.memory_service.store_learning_data(
                action=action,
                context=context,
                outcome=execution_result,
                insights=learning_insights,
                timestamp=datetime.utcnow(),
            )
            
            # Update success metrics
            await self._update_action_success_metrics(action, execution_result["success"])
            
            return {
                "learning_captured": True,
                "outcome_accuracy": outcome_analysis["accuracy_score"],
                "insights": learning_insights,
                "action_success_rate": outcome_analysis.get("action_success_rate"),
                "monitoring_timestamp": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Failed to monitor and learn: {str(e)}")
            return {
                "learning_captured": False,
                "error": str(e),
                "monitoring_timestamp": datetime.utcnow().isoformat(),
            }
    
    @activity.defn
    async def get_approval_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get approval status for a given token.
        
        Args:
            request: Approval token request
            
        Returns:
            Approval status
        """
        approval_token = request["approval_token"]
        
        logger.info(f"Checking approval status for token: {approval_token[:8]}...")
        
        try:
            approval_status = await self.approval_service.get_approval_status(approval_token)
            return approval_status
        
        except Exception as e:
            logger.error(f"Failed to get approval status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
            }
    
    @activity.defn
    async def personalize_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Personalize content for a specific user.
        
        Args:
            request: Personalization request
            
        Returns:
            Personalized content
        """
        user_id = request["user_id"]
        content = request["content"]
        user_preferences = request.get("user_preferences", {})
        
        logger.info(f"Personalizing content for user: {user_id}")
        
        try:
            # Get user context from memory
            user_context = await self.memory_service.get_user_context(user_id)
            
            # Build personalization prompt
            prompt = self._build_personalization_prompt(
                content=content,
                user_preferences=user_preferences,
                user_context=user_context,
            )
            
            # Generate personalized content
            personalized_result = await self.llm_service.generate(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=800,
                json_mode=True,
            )
            
            personalized_data = json.loads(personalized_result)
            
            return {
                "content": personalized_data.get("personalized_content", content),
                "personalization_applied": personalized_data.get("personalization_applied", []),
                "confidence": personalized_data.get("confidence", 0.8),
            }
        
        except Exception as e:
            logger.error(f"Failed to personalize content: {str(e)}")
            # Return original content on failure
            return {
                "content": content,
                "personalization_applied": [],
                "confidence": 0.0,
                "error": str(e),
            }
    
    def _build_decision_prompt(
        self,
        context: Dict[str, Any],
        available_actions: List[str],
        constraints: Dict[str, Any],
        historical_data: Dict[str, Any],
        memory_context: List[Dict[str, Any]],
    ) -> str:
        """Build a comprehensive prompt for decision analysis."""
        
        prompt = f"""
        You are an autonomous agent for the Voluntier platform, a community volunteer coordination system.
        Analyze the given context and make the best decision from available actions.
        
        CONTEXT:
        {json.dumps(context, indent=2)}
        
        AVAILABLE ACTIONS:
        {json.dumps(available_actions, indent=2)}
        
        CONSTRAINTS:
        {json.dumps(constraints, indent=2)}
        
        HISTORICAL DATA:
        {json.dumps(historical_data, indent=2)}
        
        RELEVANT MEMORY CONTEXT:
        {json.dumps(memory_context, indent=2)}
        
        Analyze this situation and provide your recommendation in the following JSON format:
        {{
            "recommended_action": "action_name",
            "confidence": 0.85,
            "reasoning": "Detailed explanation of why this action is recommended",
            "predicted_outcome": "Expected result of this action",
            "risk_assessment": {{
                "level": "low|medium|high",
                "factors": ["risk factor 1", "risk factor 2"],
                "mitigation": "How to mitigate risks"
            }},
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "alternative_actions": ["action2", "action3"]
        }}
        
        Consider:
        1. User safety and platform integrity
        2. Community benefit and engagement
        3. Resource efficiency
        4. Potential negative impacts
        5. Long-term consequences
        6. Historical success rates of similar actions
        """
        
        return prompt
    
    def _build_personalization_prompt(
        self,
        content: Dict[str, Any],
        user_preferences: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> str:
        """Build prompt for content personalization."""
        
        prompt = f"""
        Personalize the following content for a specific user based on their preferences and context.
        
        ORIGINAL CONTENT:
        {json.dumps(content, indent=2)}
        
        USER PREFERENCES:
        {json.dumps(user_preferences, indent=2)}
        
        USER CONTEXT:
        {json.dumps(user_context, indent=2)}
        
        Provide personalized content in the following JSON format:
        {{
            "personalized_content": {{
                "subject": "Personalized subject line",
                "message": "Personalized message content",
                "additional_fields": "as needed"
            }},
            "personalization_applied": ["tone_adjustment", "skill_relevance", "location_specific"],
            "confidence": 0.85
        }}
        
        Guidelines:
        1. Maintain the core message and important information
        2. Adjust tone based on user preferences
        3. Include relevant skills or interests when appropriate
        4. Use location-specific references if relevant
        5. Keep the content concise and engaging
        """
        
        return prompt
    
    async def _determine_approver(self, action: str, context: Dict[str, Any]) -> str:
        """Determine the appropriate approver for an action."""
        # Simplified approver determination logic
        if action in ["moderate_content", "update_user_profile"]:
            return "moderator"
        elif action in ["create_event", "send_notification"]:
            return "admin"
        elif context.get("financial_impact", 0) > 0:
            return "finance_admin"
        else:
            return "admin"
    
    def _get_approval_reason(self, action: str, context: Dict[str, Any], confidence: float) -> str:
        """Get reason why approval is required."""
        reasons = []
        
        if action in settings.agent.human_approval_required:
            reasons.append(f"Action '{action}' requires explicit approval")
        if confidence < 0.7:
            reasons.append(f"Low confidence score: {confidence}")
        if context.get("risk_level") == "high":
            reasons.append("High risk level")
        if context.get("financial_impact", 0) > 1000:
            reasons.append(f"High financial impact: ${context['financial_impact']}")
        if context.get("user_data_involved", False):
            reasons.append("User data is involved")
        
        return "; ".join(reasons) if reasons else "Standard approval required"
    
    async def _execute_notification_action(self, context: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification sending action."""
        # Implementation would integrate with notification service
        return {"notifications_sent": 1, "status": "success"}
    
    async def _execute_profile_update_action(self, context: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute profile update action."""
        # Implementation would integrate with user service
        return {"profiles_updated": 1, "status": "success"}
    
    async def _execute_event_creation_action(self, context: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute event creation action."""
        # Implementation would integrate with event service
        return {"events_created": 1, "status": "success"}
    
    async def _execute_content_moderation_action(self, context: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content moderation action."""
        # Implementation would integrate with moderation service
        return {"content_moderated": 1, "status": "success"}
    
    async def _execute_matching_optimization_action(self, context: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute matching optimization action."""
        # Implementation would integrate with matching service
        return {"matches_optimized": 1, "status": "success"}
    
    async def _execute_report_generation_action(self, context: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation action."""
        # Implementation would integrate with reporting service
        return {"reports_generated": 1, "status": "success"}
    
    async def _analyze_outcome_accuracy(
        self,
        predicted: Optional[str],
        actual: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze how accurate the predicted outcome was."""
        if not predicted:
            return {"accuracy_score": 0.5, "reason": "no_prediction"}
        
        # Simplified accuracy analysis
        success = actual.get("success", False)
        if "success" in predicted.lower() and success:
            return {"accuracy_score": 0.9, "reason": "prediction_accurate"}
        elif "fail" in predicted.lower() and not success:
            return {"accuracy_score": 0.9, "reason": "prediction_accurate"}
        else:
            return {"accuracy_score": 0.3, "reason": "prediction_inaccurate"}
    
    async def _extract_learning_insights(
        self,
        action: str,
        context: Dict[str, Any],
        execution_result: Dict[str, Any],
        outcome_analysis: Dict[str, Any],
    ) -> List[str]:
        """Extract learning insights from action execution."""
        insights = []
        
        if execution_result.get("success"):
            insights.append(f"Action '{action}' successful in similar context")
        else:
            insights.append(f"Action '{action}' failed - consider alternative approaches")
        
        if outcome_analysis["accuracy_score"] > 0.8:
            insights.append("Prediction accuracy high - decision model reliable")
        else:
            insights.append("Prediction accuracy low - decision model needs improvement")
        
        return insights
    
    async def _update_action_success_metrics(self, action: str, success: bool) -> None:
        """Update success metrics for action type."""
        # Implementation would update metrics in database or metrics service
        pass
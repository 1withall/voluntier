"""Authentication and document processing workflows."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

from .activities import (
    auth_activities,
    document_activities,
    notification_activities,
    security_activities,
)
from .schemas import (
    AuthenticationRequest,
    DocumentUploadRequest,
    BulkDocumentRequest,
    SessionValidationRequest,
    PrivilegeCheckRequest,
)


@workflow.defn
class AuthenticationWorkflow:
    """Workflow for user authentication and session management."""
    
    @workflow.run
    async def run(self, request: AuthenticationRequest) -> Dict[str, Any]:
        """
        Main authentication workflow.
        
        Args:
            request: Authentication request
            
        Returns:
            Authentication result
        """
        workflow.logger.info(f"Starting authentication for user: {request.email}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )
        
        try:
            # Step 1: Validate login attempt
            validation_result = await workflow.execute_activity(
                auth_activities.validate_login_attempt,
                {
                    "email": request.email,
                    "password": request.password,
                    "ip_address": request.ip_address,
                    "user_agent": request.user_agent,
                },
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            if not validation_result["valid"]:
                # Log failed validation
                await workflow.execute_activity(
                    security_activities.log_security_event,
                    {
                        "event_type": "authentication_validation_failed",
                        "details": validation_result,
                        "ip_address": request.ip_address,
                    },
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy,
                )
                
                return {
                    "authenticated": False,
                    "reason": "validation_failed",
                    "errors": validation_result["errors"],
                    "security_flags": validation_result["security_flags"],
                }
            
            # Step 2: Authenticate user credentials
            auth_result = await workflow.execute_activity(
                auth_activities.authenticate_user,
                {
                    "email": request.email,
                    "password": request.password,
                },
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            if not auth_result["authenticated"]:
                return {
                    "authenticated": False,
                    "reason": auth_result["reason"],
                    "user_id": auth_result.get("user_id"),
                    "attempts_remaining": auth_result.get("attempts_remaining"),
                }
            
            # Step 3: Create user session
            session_result = await workflow.execute_activity(
                auth_activities.create_user_session,
                {
                    "user_id": auth_result["user_id"],
                    "ip_address": request.ip_address,
                    "user_agent": request.user_agent,
                },
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            # Step 4: Send security notification if suspicious activity detected
            if validation_result.get("security_flags"):
                security_notification = {
                    "user_id": auth_result["user_id"],
                    "type": "security_alert",
                    "content": {
                        "subject": "Security Alert: Suspicious Login Activity",
                        "message": f"A login was detected with security flags: {', '.join(validation_result['security_flags'])}",
                        "security_flags": validation_result["security_flags"],
                        "ip_address": request.ip_address,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    "delivery_method": "email",
                }
                
                workflow.start_activity(
                    notification_activities.send_notification,
                    security_notification,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry_policy,
                )
            
            workflow.logger.info(f"Authentication successful for user: {auth_result['user_id']}")
            
            return {
                "authenticated": True,
                "user_id": auth_result["user_id"],
                "user_type": auth_result["user_type"],
                "user_data": auth_result["user_data"],
                "session": {
                    "session_id": session_result["session_id"],
                    "session_token": session_result["session_token"],
                    "expires_at": session_result["expires_at"],
                },
                "security_flags": validation_result.get("security_flags", []),
            }
            
        except Exception as e:
            workflow.logger.error(f"Authentication workflow failed: {str(e)}")
            return {
                "authenticated": False,
                "reason": "system_error",
                "error": str(e),
            }


@workflow.defn
class SessionManagementWorkflow:
    """Workflow for session validation and management."""
    
    @workflow.run
    async def run(self, request: SessionValidationRequest) -> Dict[str, Any]:
        """
        Session management workflow.
        
        Args:
            request: Session validation request
            
        Returns:
            Session validation result
        """
        workflow.logger.info(f"Validating session: {request.session_token[:10]}...")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=1.5,
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=2,
        )
        
        try:
            # Validate session
            validation_result = await workflow.execute_activity(
                auth_activities.validate_session,
                {
                    "session_token": request.session_token,
                    "ip_address": request.ip_address,
                },
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            if validation_result["valid"]:
                # Check for privilege escalation if requested
                if request.check_privileges:
                    privilege_result = await workflow.execute_activity(
                        auth_activities.check_user_privileges,
                        {
                            "user_id": validation_result["user_id"],
                            "privilege": request.required_privilege,
                            "level": request.required_level,
                        },
                        start_to_close_timeout=timedelta(minutes=1),
                        retry_policy=retry_policy,
                    )
                    
                    validation_result["privileges"] = privilege_result
            
            return validation_result
            
        except Exception as e:
            workflow.logger.error(f"Session validation workflow failed: {str(e)}")
            return {
                "valid": False,
                "reason": "system_error",
                "error": str(e),
            }


@workflow.defn
class DocumentProcessingWorkflow:
    """Workflow for secure document upload and verification."""
    
    @workflow.run
    async def run(self, request: DocumentUploadRequest) -> Dict[str, Any]:
        """
        Document processing workflow.
        
        Args:
            request: Document upload request
            
        Returns:
            Document processing result
        """
        workflow.logger.info(f"Processing document upload for user: {request.user_id}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )
        
        try:
            # Step 1: Validate upload
            validation_result = await workflow.execute_activity(
                document_activities.validate_document_upload,
                {
                    "user_id": request.user_id,
                    "document_type": request.document_type,
                    "file_data": request.file_data,
                    "filename": request.filename,
                    "file_size": len(request.file_data),
                    "mime_type": request.mime_type,
                },
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "reason": "validation_failed",
                    "errors": validation_result["errors"],
                }
            
            # Step 2: Security scan
            scan_result = await workflow.execute_activity(
                document_activities.scan_document_for_threats,
                {
                    "document_id": f"temp-{request.user_id}",
                    "file_data": request.file_data,
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            
            if not scan_result["safe"]:
                # Log security threat
                await workflow.execute_activity(
                    security_activities.log_security_event,
                    {
                        "event_type": "malicious_document_upload",
                        "details": scan_result,
                        "user_id": request.user_id,
                    },
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy,
                )
                
                return {
                    "success": False,
                    "reason": "security_threat_detected",
                    "threats": scan_result["threats_detected"],
                    "risk_score": scan_result["risk_score"],
                }
            
            # Step 3: Store document
            storage_result = await workflow.execute_activity(
                document_activities.store_document,
                {
                    "user_id": request.user_id,
                    "document_type": request.document_type,
                    "file_data": request.file_data,
                    "metadata": {
                        "filename": request.filename,
                        "mime_type": request.mime_type,
                        "file_hash": scan_result["file_hash"],
                        "upload_timestamp": datetime.utcnow().isoformat(),
                    },
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            
            document_id = storage_result["document_id"]
            
            # Step 4: Preprocess document
            preprocessing_result = await workflow.execute_activity(
                document_activities.preprocess_document,
                {"document_id": document_id},
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )
            
            # Step 5: ML verification (if preprocessing successful)
            if preprocessing_result["ready_for_verification"]:
                ml_verification_result = await workflow.execute_activity(
                    document_activities.verify_document_with_ml,
                    {"document_id": document_id},
                    start_to_close_timeout=timedelta(minutes=15),
                    retry_policy=retry_policy,
                )
                
                # Step 6: Schedule human review if needed
                if ml_verification_result["requires_human_review"]:
                    review_result = await workflow.execute_activity(
                        document_activities.schedule_human_review,
                        {
                            "document_id": document_id,
                            "priority": "normal" if ml_verification_result["confidence"] > 0.5 else "high",
                        },
                        start_to_close_timeout=timedelta(minutes=2),
                        retry_policy=retry_policy,
                    )
                    
                    ml_verification_result["human_review"] = review_result
            else:
                ml_verification_result = {"requires_human_review": True}
            
            # Step 7: Send status notification
            notification_data = {
                "user_id": request.user_id,
                "type": "document_processed",
                "content": {
                    "subject": "Document Upload Processed",
                    "message": f"Your {request.document_type} document has been processed.",
                    "document_id": document_id,
                    "verification_status": ml_verification_result.get("verification_status", "pending"),
                },
                "delivery_method": "email",
            }
            
            workflow.start_activity(
                notification_activities.send_notification,
                notification_data,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            workflow.logger.info(f"Document processing completed: {document_id}")
            
            return {
                "success": True,
                "document_id": document_id,
                "verification_status": ml_verification_result.get("verification_status", "pending"),
                "requires_human_review": ml_verification_result.get("requires_human_review", False),
                "confidence": ml_verification_result.get("confidence", 0.0),
                "processing_steps": {
                    "validation": validation_result["valid"],
                    "security_scan": scan_result["safe"],
                    "storage": storage_result["stored"],
                    "preprocessing": preprocessing_result["preprocessed"],
                    "ml_verification": ml_verification_result.get("verified", False),
                },
            }
            
        except Exception as e:
            workflow.logger.error(f"Document processing workflow failed: {str(e)}")
            return {
                "success": False,
                "reason": "processing_error",
                "error": str(e),
            }


@workflow.defn
class BulkDocumentProcessingWorkflow:
    """Workflow for processing multiple documents in bulk."""
    
    @workflow.run
    async def run(self, request: BulkDocumentRequest) -> Dict[str, Any]:
        """
        Bulk document processing workflow.
        
        Args:
            request: Bulk document request
            
        Returns:
            Bulk processing result
        """
        workflow.logger.info(f"Starting bulk processing for {len(request.documents)} documents")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=2),
            maximum_attempts=2,
        )
        
        try:
            # Process documents in parallel batches
            batch_size = 5  # Process 5 documents at a time
            all_results = []
            
            for i in range(0, len(request.documents), batch_size):
                batch = request.documents[i:i + batch_size]
                batch_results = []
                
                # Start parallel processing for this batch
                batch_tasks = []
                for doc_request in batch:
                    task = workflow.execute_activity(
                        self._process_single_document,
                        doc_request,
                        start_to_close_timeout=timedelta(minutes=20),
                        retry_policy=retry_policy,
                    )
                    batch_tasks.append(task)
                
                # Wait for batch completion
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        all_results.append({
                            "document_index": i + j,
                            "success": False,
                            "error": str(result),
                        })
                    else:
                        all_results.append({
                            "document_index": i + j,
                            "success": True,
                            "result": result,
                        })
                
                # Small delay between batches to prevent overload
                await asyncio.sleep(1)
            
            # Calculate summary statistics
            successful = sum(1 for r in all_results if r["success"])
            failed = len(all_results) - successful
            
            # Send completion notification
            notification_data = {
                "user_id": request.user_id,
                "type": "bulk_processing_complete",
                "content": {
                    "subject": "Bulk Document Processing Complete",
                    "message": f"Processed {len(request.documents)} documents. {successful} successful, {failed} failed.",
                    "total": len(request.documents),
                    "successful": successful,
                    "failed": failed,
                },
                "delivery_method": "email",
            }
            
            workflow.start_activity(
                notification_activities.send_notification,
                notification_data,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            
            return {
                "success": True,
                "total_documents": len(request.documents),
                "successful": successful,
                "failed": failed,
                "results": all_results,
            }
            
        except Exception as e:
            workflow.logger.error(f"Bulk document processing workflow failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _process_single_document(self, doc_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document within the bulk workflow."""
        # Create a DocumentUploadRequest and process through main workflow
        upload_request = DocumentUploadRequest(
            user_id=doc_request["user_id"],
            document_type=doc_request["document_type"],
            filename=doc_request["filename"],
            mime_type=doc_request["mime_type"],
            file_data=doc_request["file_data"],
        )
        
        # Start child workflow for document processing
        child_handle = await workflow.start_child_workflow(
            DocumentProcessingWorkflow.run,
            upload_request,
            id=f"doc-process-{doc_request.get('temp_id', 'unknown')}",
        )
        
        return await child_handle


@workflow.defn
class PrivilegeCheckWorkflow:
    """Workflow for checking user privileges."""
    
    @workflow.run
    async def run(self, request: PrivilegeCheckRequest) -> Dict[str, Any]:
        """
        Privilege check workflow.
        
        Args:
            request: Privilege check request
            
        Returns:
            Privilege check result
        """
        workflow.logger.info(f"Checking privileges for user: {request.user_id}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=1.5,
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=2,
        )
        
        try:
            # Check user privileges
            privilege_result = await workflow.execute_activity(
                auth_activities.check_user_privileges,
                {
                    "user_id": request.user_id,
                    "privilege": request.privilege,
                    "level": request.level,
                    "resource_id": request.resource_id,
                },
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            
            # Log privilege check if access denied
            if not privilege_result["has_privilege"]:
                await workflow.execute_activity(
                    security_activities.log_security_event,
                    {
                        "event_type": "privilege_check_denied",
                        "details": privilege_result,
                        "user_id": request.user_id,
                    },
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy,
                )
            
            return privilege_result
            
        except Exception as e:
            workflow.logger.error(f"Privilege check workflow failed: {str(e)}")
            return {
                "has_privilege": False,
                "reason": "system_error",
                "error": str(e),
            }
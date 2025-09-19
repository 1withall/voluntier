"""Document processing and verification activities."""

import asyncio
import uuid
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

from temporalio import activity
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from voluntier.database import get_db_session_context
from voluntier.models import Document, DocumentVerification, User
from voluntier.services.ml_verifier import MLDocumentVerifier
from voluntier.services.document_processor import DocumentProcessor
from voluntier.services.security import SecurityService
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentActivities:
    """Activities related to document processing and verification."""
    
    @activity.defn
    async def validate_document_upload(self, upload_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate document upload request.
        
        Args:
            upload_data: Document upload data
            
        Returns:
            Validation result
        """
        logger.info(f"Validating document upload for user: {upload_data.get('user_id')}")
        
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["user_id", "document_type", "file_data", "filename"]
        for field in required_fields:
            if not upload_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # File validation
        filename = upload_data.get("filename", "")
        file_size = upload_data.get("file_size", 0)
        mime_type = upload_data.get("mime_type", "")
        
        # File size limits (50MB max)
        max_size = 50 * 1024 * 1024
        if file_size > max_size:
            errors.append(f"File size exceeds limit of {max_size // (1024*1024)}MB")
        
        # MIME type validation
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/png", 
            "image/webp",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        if mime_type not in allowed_types:
            errors.append(f"File type {mime_type} not allowed")
        
        # Filename security validation
        if any(char in filename for char in ["../", "..\\", "/", "\\"]):
            errors.append("Invalid filename - path traversal detected")
        
        # Extension validation
        suspicious_extensions = [".exe", ".bat", ".cmd", ".scr", ".pif", ".com", ".cpl"]
        if any(filename.lower().endswith(ext) for ext in suspicious_extensions):
            errors.append("File extension not permitted for security reasons")
        
        # Document type validation
        valid_doc_types = [
            "government_id", "proof_of_address", "organization_registration",
            "business_license", "reference_letter", "tax_exemption",
            "insurance_certificate", "other"
        ]
        
        if upload_data.get("document_type") not in valid_doc_types:
            errors.append("Invalid document type")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "file_size": file_size,
                "mime_type": mime_type,
            },
        }
    
    @activity.defn
    async def scan_document_for_threats(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan document for security threats and malware.
        
        Args:
            scan_request: Document scan request
            
        Returns:
            Scan result
        """
        document_id = scan_request["document_id"]
        file_data = scan_request["file_data"]
        
        logger.info(f"Scanning document for threats: {document_id}")
        
        try:
            security_service = SecurityService()
            
            # Calculate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Virus scan (simplified - would integrate with actual AV service)
            virus_scan_result = await security_service.scan_for_viruses(file_data)
            
            # Check against known malicious hashes
            hash_reputation = await security_service.check_file_hash_reputation(file_hash)
            
            # Content analysis for embedded threats
            content_analysis = await security_service.analyze_document_content(file_data)
            
            threats_detected = []
            risk_score = 0.0
            
            if virus_scan_result["threats_detected"]:
                threats_detected.extend(virus_scan_result["threats"])
                risk_score += 1.0
            
            if hash_reputation["is_malicious"]:
                threats_detected.append("known_malicious_hash")
                risk_score += 1.0
            
            if content_analysis["suspicious_content"]:
                threats_detected.extend(content_analysis["suspicious_patterns"])
                risk_score += content_analysis["risk_score"]
            
            is_safe = risk_score < 0.5 and len(threats_detected) == 0
            
            return {
                "safe": is_safe,
                "risk_score": min(risk_score, 1.0),
                "threats_detected": threats_detected,
                "file_hash": file_hash,
                "scan_timestamp": datetime.utcnow().isoformat(),
                "scan_details": {
                    "virus_scan": virus_scan_result,
                    "hash_reputation": hash_reputation,
                    "content_analysis": content_analysis,
                },
            }
        
        except Exception as e:
            logger.error(f"Document threat scan failed: {str(e)}")
            raise
    
    @activity.defn
    async def store_document(self, storage_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store document securely in the database.
        
        Args:
            storage_request: Document storage request
            
        Returns:
            Storage result
        """
        user_id = storage_request["user_id"]
        document_type = storage_request["document_type"]
        file_data = storage_request["file_data"]
        metadata = storage_request.get("metadata", {})
        
        logger.info(f"Storing document for user: {user_id}")
        
        try:
            document_id = str(uuid.uuid4())
            
            # Encrypt file data (simplified - would use proper encryption service)
            security_service = SecurityService()
            encrypted_data = await security_service.encrypt_document(file_data)
            
            async with get_db_session_context() as session:
                # Create document record
                document = Document(
                    id=uuid.UUID(document_id),
                    user_id=uuid.UUID(user_id),
                    document_type=document_type,
                    filename=metadata.get("filename"),
                    mime_type=metadata.get("mime_type"),
                    file_size=len(file_data),
                    file_hash=metadata.get("file_hash"),
                    encrypted_data=encrypted_data["encrypted_data"],
                    encryption_key=encrypted_data["encryption_key"],
                    verification_status="pending",
                    uploaded_at=datetime.utcnow(),
                    metadata=metadata,
                )
                
                session.add(document)
                await session.commit()
                
                logger.info(f"Document stored successfully: {document_id}")
                
                return {
                    "document_id": document_id,
                    "stored": True,
                    "file_size": len(file_data),
                    "encrypted": True,
                    "verification_status": "pending",
                }
        
        except Exception as e:
            logger.error(f"Document storage failed: {str(e)}")
            raise
    
    @activity.defn
    async def preprocess_document(self, preprocessing_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess document for verification.
        
        Args:
            preprocessing_request: Document preprocessing request
            
        Returns:
            Preprocessing result
        """
        document_id = preprocessing_request["document_id"]
        
        logger.info(f"Preprocessing document: {document_id}")
        
        try:
            async with get_db_session_context() as session:
                # Get document
                stmt = select(Document).where(Document.id == uuid.UUID(document_id))
                result = await session.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    raise ValueError(f"Document not found: {document_id}")
                
                # Decrypt document data
                security_service = SecurityService()
                decrypted_data = await security_service.decrypt_document(
                    document.encrypted_data,
                    document.encryption_key
                )
                
                # Initialize document processor
                processor = DocumentProcessor()
                
                # Extract text content
                text_content = await processor.extract_text(decrypted_data, document.mime_type)
                
                # Extract metadata
                extracted_metadata = await processor.extract_metadata(decrypted_data, document.mime_type)
                
                # Detect document structure
                structure_analysis = await processor.analyze_document_structure(text_content)
                
                # Image preprocessing (if applicable)
                image_analysis = None
                if document.mime_type.startswith("image/"):
                    image_analysis = await processor.preprocess_image(decrypted_data)
                
                # Update document with preprocessing results
                preprocessing_results = {
                    "text_content": text_content,
                    "extracted_metadata": extracted_metadata,
                    "structure_analysis": structure_analysis,
                    "image_analysis": image_analysis,
                    "preprocessing_timestamp": datetime.utcnow().isoformat(),
                }
                
                # Store preprocessing results
                document.preprocessing_results = preprocessing_results
                document.preprocessing_completed = True
                await session.commit()
                
                return {
                    "preprocessed": True,
                    "document_id": document_id,
                    "text_extracted": len(text_content) > 0,
                    "metadata_extracted": len(extracted_metadata) > 0,
                    "image_processed": image_analysis is not None,
                    "ready_for_verification": True,
                }
        
        except Exception as e:
            logger.error(f"Document preprocessing failed: {str(e)}")
            raise
    
    @activity.defn
    async def verify_document_with_ml(self, verification_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify document using machine learning models.
        
        Args:
            verification_request: Document verification request
            
        Returns:
            ML verification result
        """
        document_id = verification_request["document_id"]
        
        logger.info(f"Running ML verification for document: {document_id}")
        
        try:
            async with get_db_session_context() as session:
                # Get document with preprocessing results
                stmt = select(Document).where(Document.id == uuid.UUID(document_id))
                result = await session.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    raise ValueError(f"Document not found: {document_id}")
                
                if not document.preprocessing_completed:
                    raise ValueError(f"Document preprocessing not completed: {document_id}")
                
                # Initialize ML verifier
                ml_verifier = MLDocumentVerifier()
                
                # Get preprocessing results
                preprocessing_results = document.preprocessing_results or {}
                text_content = preprocessing_results.get("text_content", "")
                image_analysis = preprocessing_results.get("image_analysis")
                
                # Run ML verification based on document type
                verification_result = await ml_verifier.verify_document(
                    document_type=document.document_type,
                    text_content=text_content,
                    image_analysis=image_analysis,
                    metadata=document.metadata
                )
                
                # Create verification record
                verification_record = DocumentVerification(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    verification_type="ml_automated",
                    verification_status=verification_result["status"],
                    confidence_score=verification_result["confidence"],
                    verification_notes=verification_result.get("notes"),
                    verification_metadata=verification_result,
                    verified_at=datetime.utcnow(),
                )
                
                session.add(verification_record)
                
                # Update document verification status
                if verification_result["confidence"] >= 0.8:
                    document.verification_status = "verified"
                elif verification_result["confidence"] >= 0.5:
                    document.verification_status = "review_required"
                else:
                    document.verification_status = "rejected"
                
                document.ml_verification_completed = True
                await session.commit()
                
                return {
                    "verified": True,
                    "document_id": document_id,
                    "verification_status": document.verification_status,
                    "confidence": verification_result["confidence"],
                    "requires_human_review": verification_result["confidence"] < 0.8,
                    "verification_notes": verification_result.get("notes"),
                }
        
        except Exception as e:
            logger.error(f"ML document verification failed: {str(e)}")
            raise
    
    @activity.defn
    async def schedule_human_review(self, review_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule document for human review.
        
        Args:
            review_request: Human review request
            
        Returns:
            Review scheduling result
        """
        document_id = review_request["document_id"]
        priority = review_request.get("priority", "normal")
        
        logger.info(f"Scheduling human review for document: {document_id}")
        
        try:
            async with get_db_session_context() as session:
                # Get document
                stmt = select(Document).where(Document.id == uuid.UUID(document_id))
                result = await session.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    raise ValueError(f"Document not found: {document_id}")
                
                # Update document status
                document.requires_human_review = True
                document.review_priority = priority
                document.review_scheduled_at = datetime.utcnow()
                
                await session.commit()
                
                # In a real system, this would integrate with a work queue system
                # For now, we'll create a simplified review task
                
                return {
                    "scheduled": True,
                    "document_id": document_id,
                    "priority": priority,
                    "estimated_review_time": "24-48 hours",
                    "review_queue_position": 1,  # Simplified
                }
        
        except Exception as e:
            logger.error(f"Human review scheduling failed: {str(e)}")
            raise
    
    @activity.defn
    async def get_document_status(self, status_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current document verification status.
        
        Args:
            status_request: Status request
            
        Returns:
            Document status
        """
        document_id = status_request["document_id"]
        
        logger.info(f"Getting status for document: {document_id}")
        
        try:
            async with get_db_session_context() as session:
                # Get document with verifications
                stmt = select(Document).where(Document.id == uuid.UUID(document_id))
                result = await session.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    return {
                        "found": False,
                        "error": "Document not found",
                    }
                
                # Get verification records
                verification_stmt = select(DocumentVerification).where(
                    DocumentVerification.document_id == document.id
                )
                verification_result = await session.execute(verification_stmt)
                verifications = verification_result.scalars().all()
                
                return {
                    "found": True,
                    "document_id": document_id,
                    "verification_status": document.verification_status,
                    "uploaded_at": document.uploaded_at.isoformat(),
                    "preprocessing_completed": document.preprocessing_completed,
                    "ml_verification_completed": document.ml_verification_completed,
                    "requires_human_review": document.requires_human_review,
                    "verification_count": len(verifications),
                    "latest_verification": verifications[-1].verification_status if verifications else None,
                }
        
        except Exception as e:
            logger.error(f"Document status check failed: {str(e)}")
            raise
    
    @activity.defn
    async def bulk_document_processing(self, bulk_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process multiple documents in bulk.
        
        Args:
            bulk_request: Bulk processing request
            
        Returns:
            Bulk processing result
        """
        document_ids = bulk_request["document_ids"]
        processing_type = bulk_request.get("processing_type", "verification")
        
        logger.info(f"Starting bulk processing for {len(document_ids)} documents")
        
        results = []
        successful = 0
        failed = 0
        
        for document_id in document_ids:
            try:
                if processing_type == "verification":
                    result = await self.verify_document_with_ml({"document_id": document_id})
                elif processing_type == "preprocessing":
                    result = await self.preprocess_document({"document_id": document_id})
                else:
                    raise ValueError(f"Unknown processing type: {processing_type}")
                
                results.append({
                    "document_id": document_id,
                    "success": True,
                    "result": result,
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "document_id": document_id,
                    "success": False,
                    "error": str(e),
                })
                failed += 1
                logger.error(f"Bulk processing failed for document {document_id}: {str(e)}")
        
        return {
            "total_processed": len(document_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
            "processing_type": processing_type,
        }


# Export activities instance
document_activities = DocumentActivities()
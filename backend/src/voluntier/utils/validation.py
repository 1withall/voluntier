"""Validation utilities."""

import re
from typing import Any, Dict, List, Optional


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip().lower()))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits_only) <= 15


def validate_password(password: str) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Validation result with strength score and feedback
    """
    if not password or not isinstance(password, str):
        return {
            "valid": False,
            "strength": 0,
            "errors": ["Password is required"],
            "suggestions": ["Provide a password"],
        }
    
    errors = []
    suggestions = []
    strength = 0
    
    # Length check
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
        suggestions.append("Use at least 8 characters")
    else:
        strength += 1
    
    # Character type checks
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain lowercase letters")
        suggestions.append("Add lowercase letters")
    else:
        strength += 1
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain uppercase letters")
        suggestions.append("Add uppercase letters")
    else:
        strength += 1
    
    if not re.search(r'\d', password):
        errors.append("Password must contain numbers")
        suggestions.append("Add numbers")
    else:
        strength += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain special characters")
        suggestions.append("Add special characters")
    else:
        strength += 1
    
    # Additional strength checks
    if len(password) >= 12:
        strength += 1
    
    # Common password patterns
    common_patterns = [
        r'123456',
        r'password',
        r'qwerty',
        r'abc123',
        r'admin',
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            errors.append("Password contains common patterns")
            suggestions.append("Avoid common patterns like '123456' or 'password'")
            strength = max(0, strength - 2)
            break
    
    return {
        "valid": len(errors) == 0,
        "strength": min(strength, 5),  # Cap at 5
        "errors": errors,
        "suggestions": suggestions,
    }


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that required fields are present and not empty.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of missing field errors
    """
    errors = []
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None or data[field] == "":
            errors.append(f"Field '{field}' cannot be empty")
        elif isinstance(data[field], str) and not data[field].strip():
            errors.append(f"Field '{field}' cannot be empty")
    
    return errors


def validate_string_length(
    value: str, 
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> List[str]:
    """
    Validate string length constraints.
    
    Args:
        value: String value to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if not isinstance(value, str):
        errors.append(f"{field_name} must be a string")
        return errors
    
    length = len(value.strip())
    
    if min_length is not None and length < min_length:
        errors.append(f"{field_name} must be at least {min_length} characters long")
    
    if max_length is not None and length > max_length:
        errors.append(f"{field_name} must be no more than {max_length} characters long")
    
    return errors


def validate_list_items(
    items: List[Any],
    field_name: str,
    max_items: Optional[int] = None,
    min_items: Optional[int] = None,
    item_validator: Optional[callable] = None,
) -> List[str]:
    """
    Validate list items.
    
    Args:
        items: List to validate
        field_name: Name of the field for error messages
        max_items: Maximum number of items allowed
        min_items: Minimum number of items required
        item_validator: Optional function to validate each item
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if not isinstance(items, list):
        errors.append(f"{field_name} must be a list")
        return errors
    
    if min_items is not None and len(items) < min_items:
        errors.append(f"{field_name} must contain at least {min_items} items")
    
    if max_items is not None and len(items) > max_items:
        errors.append(f"{field_name} must contain no more than {max_items} items")
    
    if item_validator:
        for i, item in enumerate(items):
            try:
                if not item_validator(item):
                    errors.append(f"{field_name}[{i}] is invalid")
            except Exception as e:
                errors.append(f"{field_name}[{i}] validation failed: {str(e)}")
    
    return errors


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input.
    
    Args:
        value: String to sanitize
        max_length: Maximum length to truncate to
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    
    # Strip whitespace
    sanitized = value.strip()
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Truncate if necessary
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized
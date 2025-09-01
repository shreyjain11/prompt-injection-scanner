"""
Example Python application with secure prompt handling patterns.
This demonstrates best practices for preventing prompt injection attacks.
"""

import openai
import re
from typing import List, Dict, Any

# Configuration
openai.api_key = "your-api-key-here"

def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove potentially dangerous characters and patterns
    sanitized = re.sub(r'[<>"\']', '', user_input)
    # Limit length
    return sanitized[:1000]

def secure_chat_completion(user_input: str) -> str:
    """✅ SECURE: Proper message structure with separated roles"""
    # Sanitize user input
    sanitized_input = sanitize_input(user_input)
    
    # Use proper message structure
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": sanitized_input}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def secure_system_prompt(user_context: str) -> str:
    """✅ SECURE: Separate system and user content"""
    # Sanitize context
    sanitized_context = sanitize_input(user_context)
    
    # Keep system prompt clean
    system_prompt = "You are a helpful assistant."
    
    # Put user context in user message
    user_message = f"Context: {sanitized_context}\nPlease help me with my question."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def secure_template_usage(user_name: str) -> str:
    """✅ SECURE: Safe template usage with sanitized input"""
    # Sanitize user input
    sanitized_name = sanitize_input(user_name)
    
    # Use safe template
    template = "Hello {name}, how can I help you today?"
    message = template.format(name=sanitized_name)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": message}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def secure_string_formatting(user_input: str) -> str:
    """✅ SECURE: Safe string formatting with validation"""
    # Validate and sanitize input
    if not user_input or len(user_input) > 1000:
        raise ValueError("Invalid input")
    
    sanitized_input = sanitize_input(user_input)
    
    # Use safe formatting
    prompt = "Please respond to the user's request."
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": sanitized_input}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def secure_parameterized_prompt(user_data: Dict[str, Any]) -> str:
    """✅ SECURE: Parameterized prompt with structured data"""
    # Validate input structure
    required_fields = ['name', 'question']
    for field in required_fields:
        if field not in user_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Sanitize each field
    sanitized_data = {
        key: sanitize_input(str(value)) 
        for key, value in user_data.items()
    }
    
    # Use structured prompt
    system_prompt = "You are a helpful assistant. Respond to user questions professionally."
    user_message = f"Name: {sanitized_data['name']}\nQuestion: {sanitized_data['question']}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def secure_validation(user_input: str) -> bool:
    """✅ SECURE: Input validation before processing"""
    # Check for potentially malicious patterns
    dangerous_patterns = [
        r'system:',
        r'user:',
        r'assistant:',
        r'role:',
        r'content:',
        r'ignore previous',
        r'forget everything',
        r'act as',
        r'you are now',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return False
    
    # Check length
    if len(user_input) > 1000:
        return False
    
    # Check for null bytes or other dangerous characters
    if '\x00' in user_input or '\x1a' in user_input:
        return False
    
    return True

def secure_chat_with_validation(user_input: str) -> str:
    """✅ SECURE: Complete secure chat with validation"""
    # Validate input
    if not secure_validation(user_input):
        raise ValueError("Input validation failed")
    
    # Sanitize input
    sanitized_input = sanitize_input(user_input)
    
    # Use secure prompt structure
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Always respond safely and appropriately."},
        {"role": "user", "content": sanitized_input}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=500,  # Limit response length
        temperature=0.7  # Control randomness
    )
    return response.choices[0].message.content

# Main function
def main():
    try:
        user_input = input("Enter your message: ")
        result = secure_chat_with_validation(user_input)
        print(f"Response: {result}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()




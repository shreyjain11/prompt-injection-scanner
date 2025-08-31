"""
Example Python application with intentional prompt injection vulnerabilities.
This file is used for testing the scanner - DO NOT use in production!
"""

import openai
from string import Template

# Configuration
openai.api_key = "your-api-key-here"

def vulnerable_chat_completion(user_input):
    """❌ VULNERABLE: Direct prompt injection"""
    prompt = "You are a helpful assistant. " + user_input
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def vulnerable_system_prompt(user_context):
    """❌ VULNERABLE: System prompt pollution"""
    system_prompt = f"You are a helpful assistant. User context: {user_context}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Hello"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def vulnerable_template_injection(user_name, user_role):
    """❌ VULNERABLE: Template injection"""
    template = "Hello {name}, you are {role}"
    message = template.format(name=user_name, role=user_role)
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

def vulnerable_string_formatting(user_input):
    """❌ VULNERABLE: Unsafe string formatting"""
    prompt = "Tell me about %s" % user_input
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def vulnerable_f_string(user_input):
    """❌ VULNERABLE: F-string with user input"""
    prompt = f"You are a helpful assistant. User says: {user_input}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def vulnerable_eval(user_expression):
    """❌ VULNERABLE: Eval with user input"""
    result = eval(user_expression)
    return result

def vulnerable_dynamic_import(module_name):
    """❌ VULNERABLE: Dynamic import with user input"""
    module = __import__(module_name)
    return module

def vulnerable_hardcoded_prompt():
    """❌ VULNERABLE: Hardcoded prompt with user placeholder"""
    prompt = "You are a helpful assistant. Please help {user} with their question."
    return prompt

# Main function
def main():
    user_input = input("Enter your message: ")
    
    # This would trigger multiple vulnerabilities
    result = vulnerable_chat_completion(user_input)
    print(f"Response: {result}")

if __name__ == "__main__":
    main()






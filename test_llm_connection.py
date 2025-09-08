#!/usr/bin/env python3
"""
Quick test to see if LLM client is working
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv("config/.env")
except ImportError:
    env_path = "config/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')

from backend.utils import load_config

def test_llm_connection():
    """Test if LLM client can parse time correctly"""
    
    print("=" * 50)
    print("LLM CONNECTION TEST")
    print("=" * 50)
    
    # Check environment variables
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"OpenRouter Key: {'✓ Set' if openrouter_key else '✗ Missing'}")
    print(f"OpenAI Key: {'✓ Set' if openai_key else '✗ Missing'}")
    
    if openrouter_key:
        print(f"OpenRouter Key Preview: {openrouter_key[:15]}...{openrouter_key[-6:]}")
    
    # Load config
    try:
        config = load_config("config/config.yaml")
        provider = config.get('llm', {}).get('provider', 'openai')
        model = config.get('llm', {}).get('model', 'gpt-4')
        
        print(f"LLM Provider: {provider}")
        print(f"LLM Model: {model}")
        
    except Exception as e:
        print(f"Config error: {e}")
        return False
    
    # Test LLM client
    try:
        from openai import OpenAI
        
        if provider == 'openrouter':
            client = OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            client = OpenAI(api_key=openai_key)
        
        # Simple test
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Just respond with: 'LLM working correctly'"}
            ],
            temperature=0.1
        )
        
        result = response.choices[0].message.content
        print(f"LLM Response: {result}")
        
        if "working" in result.lower():
            print("✓ LLM client is working!")
            return True
        else:
            print("✗ LLM client responded but incorrectly")
            return False
            
    except Exception as e:
        print(f"✗ LLM client failed: {e}")
        return False

def test_time_parsing():
    """Test if LLM can parse time correctly"""
    
    if not test_llm_connection():
        return
    
    print("\n" + "=" * 50)
    print("TIME PARSING TEST")
    print("=" * 50)
    
    try:
        from openai import OpenAI
        
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        client = OpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        test_descriptions = [
            "Team meeting tomorrow at 2 PM for 1 hour",
            "Doctor appointment on August 28th at 10:30 AM"
        ]
        
        for desc in test_descriptions:
            print(f"\nTesting: '{desc}'")
            
            prompt = f"""
            Parse this calendar event request and extract the details in JSON format:
            "{desc}"
            
            Extract and return a JSON object with these fields:
            - summary: Event title/name
            - start_time: ISO format datetime (e.g., "2025-08-25T14:00:00")
            - end_time: ISO format datetime
            
            For dates, assume current year 2025. Use 24-hour format.
            Return only the JSON object, no other text.
            """
            
            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct",
                messages=[
                    {"role": "system", "content": "You are a calendar parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            print(f"LLM Response: {result}")
            
            try:
                from backend.utils import parse_llm_json
                parsed = parse_llm_json(result)
                print(f"✓ Parsed successfully: {parsed.get('summary')} at {parsed.get('start_time')}")
            except Exception as parse_error:
                print(f"✗ Failed to parse JSON: {parse_error}")
                
    except Exception as e:
        print(f"Time parsing test failed: {e}")

if __name__ == "__main__":
    test_time_parsing()

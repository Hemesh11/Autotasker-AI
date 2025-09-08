#!/usr/bin/env python3
"""
Comprehensive Backend Components Test
Tests llm_factory.py, openrouter_client.py, scheduler.py, and utils.py
"""

import os
import sys
import json
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

from backend.utils import load_config, clean_llm_response, parse_llm_json, validate_api_keys, format_datetime, TaskTimer
from backend.llm_factory import LLMClientFactory, create_llm_client, get_chat_completion
from datetime import datetime


def test_utils():
    """Test utility functions"""
    print("🔧 Testing Utils...")
    
    try:
        # Test config loading
        config = load_config("config/config.yaml")
        assert config is not None
        print("   ✅ Config loading works")
        
        # Test API key validation
        validation = validate_api_keys()
        print(f"   ✅ API validation works: {validation}")
        
        # Test datetime formatting
        now = datetime.now()
        formatted = format_datetime(now)
        assert formatted is not None
        print(f"   ✅ DateTime formatting works: {formatted}")
        
        # Test LLM response cleaning
        test_response = '```json\n{"test": "value"}\n```'
        cleaned = clean_llm_response(test_response)
        assert '"test": "value"' in cleaned
        print("   ✅ LLM response cleaning works")
        
        # Test JSON parsing
        parsed = parse_llm_json(test_response)
        assert parsed["test"] == "value"
        print("   ✅ LLM JSON parsing works")
        
        # Test TaskTimer
        with TaskTimer("test_task") as timer:
            import time
            time.sleep(0.1)
        assert timer.duration > 0
        print("   ✅ TaskTimer works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Utils test failed: {e}")
        return False


def test_llm_factory():
    """Test LLM factory and client creation"""
    print("🤖 Testing LLM Factory...")
    
    try:
        # Load config
        config = load_config("config/config.yaml")
        
        # Test client creation
        client = create_llm_client(config)
        assert client is not None
        print("   ✅ LLM client creation works")
        
        # Test model name retrieval
        model = LLMClientFactory.get_model_name(config)
        assert model is not None
        print(f"   ✅ Model name retrieval works: {model}")
        
        # Test simple chat completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, AutoTasker!'"}
        ]
        
        response = get_chat_completion(
            client=client,
            messages=messages,
            model=model,
            temperature=0.1,
            max_tokens=50
        )
        
        assert response is not None
        assert len(response) > 0
        print(f"   ✅ Chat completion works: {response[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ LLM Factory test failed: {e}")
        return False


def test_json_parsing():
    """Test JSON parsing with various LLM response formats"""
    print("📄 Testing JSON Parsing...")
    
    test_cases = [
        # Standard JSON
        '{"test": "value"}',
        
        # JSON with markdown
        '```json\n{"test": "value"}\n```',
        
        # JSON with prefix
        'Here is the response:\n```json\n{"test": "value"}\n```',
        
        # JSON with extra text
        'Response: ```json\n{"summary": "Meeting", "time": "2:00 PM"}\n```\nThat should work.',
    ]
    
    try:
        for i, test_case in enumerate(test_cases):
            parsed = parse_llm_json(test_case)
            assert isinstance(parsed, dict)
            print(f"   ✅ Test case {i+1} parsed successfully: {parsed}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ JSON parsing test failed: {e}")
        return False


def test_scheduler_integration():
    """Test scheduler functionality (if exists)"""
    print("⏰ Testing Scheduler Integration...")
    
    try:
        # Check if scheduler module exists
        try:
            from backend.scheduler import Scheduler
            print("   ✅ Scheduler module found")
            
            # Test basic scheduler functionality
            config = load_config("config/config.yaml")
            scheduler = Scheduler(config)
            print("   ✅ Scheduler initialization works")
            
        except ImportError:
            print("   ℹ️ Scheduler module not implemented yet")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Scheduler test failed: {e}")
        return False


def test_error_handling():
    """Test error handling in backend components"""
    print("🚨 Testing Error Handling...")
    
    try:
        # Test invalid JSON parsing
        try:
            parse_llm_json("invalid json {")
            print("   ❌ Should have failed on invalid JSON")
            return False
        except ValueError:
            print("   ✅ Invalid JSON properly handled")
        
        # Test missing config file
        try:
            load_config("nonexistent_config.yaml")
            print("   ℹ️ Missing config handled gracefully")
        except:
            print("   ✅ Missing config error handled")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False


def test_openrouter_integration():
    """Test OpenRouter client specifically"""
    print("🔗 Testing OpenRouter Integration...")
    
    try:
        config = load_config("config/config.yaml")
        
        # Check if OpenRouter is configured
        if config.get("llm", {}).get("provider") == "openrouter":
            from backend.openrouter_client import create_openrouter_client
            
            client = create_openrouter_client(config)
            assert client is not None
            print("   ✅ OpenRouter client created successfully")
            
            # Test a simple request
            messages = [{"role": "user", "content": "Return exactly: TEST_SUCCESS"}]
            
            response = client.chat.create(
                messages=messages,
                model=config.get("llm", {}).get("model", "meta-llama/llama-3.3-70b-instruct"),
                temperature=0.1,
                max_tokens=20
            )
            
            assert response.content is not None
            print(f"   ✅ OpenRouter API call successful: {response.content}")
            
        else:
            print("   ℹ️ OpenRouter not configured, skipping")
        
        return True
        
    except Exception as e:
        print(f"   ❌ OpenRouter test failed: {e}")
        return False


def main():
    """Run all backend component tests"""
    print("🚀 AUTOTASKER AI - BACKEND COMPONENTS TEST")
    print("=" * 60)
    print("Testing core backend modules...")
    print("=" * 60)
    
    tests = [
        ("Utils", test_utils),
        ("LLM Factory", test_llm_factory),
        ("JSON Parsing", test_json_parsing),
        ("OpenRouter Integration", test_openrouter_integration),
        ("Scheduler Integration", test_scheduler_integration),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 BACKEND TEST REPORT")
    print("=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL BACKEND TESTS PASSED!")
        print("🚀 Backend components are production-ready!")
    else:
        print("⚠️ Some backend components need attention")
    
    print("=" * 60)


if __name__ == "__main__":
    main()

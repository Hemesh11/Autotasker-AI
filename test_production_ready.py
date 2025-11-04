"""
AutoTasker AI - Complete Production Test Suite
Tests all components for production readiness
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_environment():
    """Test basic environment setup"""
    print("🔍 Testing Environment Setup...")
    
    # Test Python version
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 9:
        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python version too old: {python_version.major}.{python_version.minor}.{python_version.micro}")
        return False
    
    # Test required directories
    required_dirs = [
        'backend', 'agents', 'config', 'frontend', 
        'google_auth', 'data', 'memory', 'aws'
    ]
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ Directory exists: {dir_name}")
        else:
            print(f"❌ Missing directory: {dir_name}")
            return False
    
    return True

def test_dependencies():
    """Test all required Python packages"""
    print("\n📦 Testing Dependencies...")
    
    required_packages = [
        'streamlit', 'langchain', 'langgraph', 'openai',
        'google.auth', 'google.oauth2', 'google_auth_oauthlib',
        'googleapiclient', 'boto3', 'pandas', 'numpy',
        'dotenv', 'yaml', 'apscheduler', 'plotly'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            if package == 'yaml':
                import yaml
            elif package == 'dotenv':
                import dotenv
            elif package == 'google.auth':
                import google.auth
            elif package == 'google.oauth2':
                import google.oauth2
            elif package == 'google_auth_oauthlib':
                import google_auth_oauthlib
            elif package == 'googleapiclient':
                import googleapiclient
            elif package == 'apscheduler':
                import apscheduler
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {str(e)}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    return True

def test_configuration():
    """Test configuration files"""
    print("\n⚙️ Testing Configuration...")
    
    # Test config.yaml
    config_path = 'config/config.yaml'
    if os.path.exists(config_path):
        try:
            from backend.utils import load_config
            config = load_config(config_path)
            print("✅ config.yaml loaded successfully")
            
            # Check essential sections
            required_sections = ['app', 'llm', 'agents']
            for section in required_sections:
                if section in config:
                    print(f"✅ Config section: {section}")
                else:
                    print(f"❌ Missing config section: {section}")
                    return False
                    
        except Exception as e:
            print(f"❌ config.yaml error: {str(e)}")
            return False
    else:
        print(f"❌ Missing: {config_path}")
        return False
    
    # Test .env file
    env_path = '.env'
    if os.path.exists(env_path):
        print("✅ .env file exists")
        
        # Load and check environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        env_vars = [
            'OPENAI_API_KEY', 'OPENROUTER_API_KEY', 
            'GITHUB_TOKEN', 'GMAIL_SENDER_EMAIL'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value and not value.startswith('your_'):
                print(f"✅ Environment variable: {var}")
            else:
                print(f"⚠️ Environment variable not set: {var}")
    else:
        print(f"⚠️ Missing: {env_path} (create from template)")
    
    return True

def test_agents():
    """Test individual agents"""
    print("\n🤖 Testing Agents...")
    
    agents_to_test = [
        ('planner_agent', 'PlannerAgent'),
        ('gmail_agent', 'GmailAgent'),
        ('github_agent', 'GitHubAgent'),
        ('leetcode_agent', 'LeetCodeAgent'),
        ('summarizer_agent', 'SummarizerAgent'),
        ('logger_agent', 'LoggerAgent'),
        ('memory_agent', 'MemoryAgent'),
        ('retry_agent', 'RetryAgent'),
        ('tool_selector', 'ToolSelector')
    ]
    
    failed_agents = []
    
    for module_name, class_name in agents_to_test:
        try:
            module = __import__(f'agents.{module_name}', fromlist=[class_name])
            agent_class = getattr(module, class_name)
            print(f"✅ Agent: {class_name}")
        except Exception as e:
            print(f"❌ Agent {class_name}: {str(e)}")
            failed_agents.append(class_name)
    
    if failed_agents:
        print(f"\n❌ Failed agents: {', '.join(failed_agents)}")
        return False
    
    return True

def test_backend():
    """Test backend components"""
    print("\n🔧 Testing Backend...")
    
    backend_modules = [
        ('langgraph_runner', 'AutoTaskerRunner'),
        ('utils', None),
        ('llm_factory', 'LLMClientFactory'),
        ('scheduler', None)
    ]
    
    failed_modules = []
    
    for module_name, class_name in backend_modules:
        try:
            if class_name:
                module = __import__(f'backend.{module_name}', fromlist=[class_name])
                component_class = getattr(module, class_name)
                print(f"✅ Backend: {class_name}")
            else:
                module = __import__(f'backend.{module_name}')
                print(f"✅ Backend: {module_name}")
        except Exception as e:
            print(f"❌ Backend {module_name}: {str(e)}")
            failed_modules.append(module_name)
    
    if failed_modules:
        print(f"\n❌ Failed backend modules: {', '.join(failed_modules)}")
        return False
    
    return True

def test_llm_connection():
    """Test LLM connection"""
    print("\n🧠 Testing LLM Connection...")
    
    try:
        from backend.llm_factory import LLMClientFactory, get_chat_completion
        from backend.utils import load_config
        
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        config = load_config(config_path)
        llm_client = LLMClientFactory.create_client(config)
        
        # Simple test prompt
        response = get_chat_completion(
            client=llm_client,
            messages=[{"role": "user", "content": "Hello! Respond with 'LLM connection successful'"}],
            model="gpt-3.5-turbo",
            max_tokens=50
        )
        print(f"✅ LLM Response: {response[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ LLM Connection: {str(e)}")
        print("⚠️ This may be due to missing API keys")
        return False

def test_frontend():
    """Test frontend components"""
    print("\n🌐 Testing Frontend...")
    
    frontend_files = [
        'frontend/streamlit_app.py',
        'frontend/streamlit_app_enhanced.py'
    ]
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"✅ Frontend file: {file_path}")
            
            # Basic syntax check
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    compile(content, file_path, 'exec')
                print(f"✅ Syntax check passed: {file_path}")
            except SyntaxError as e:
                print(f"❌ Syntax error in {file_path}: {str(e)}")
                return False
        else:
            print(f"❌ Missing file: {file_path}")
            return False
    
    return True

def test_aws_components():
    """Test AWS deployment components"""
    print("\n☁️ Testing AWS Components...")
    
    aws_files = [
        'aws/lambda_handler.py',
        'aws/deployment.py',
        'aws/cloudformation.py'
    ]
    
    for file_path in aws_files:
        if os.path.exists(file_path):
            print(f"✅ AWS file: {file_path}")
        else:
            print(f"⚠️ AWS file missing: {file_path}")
    
    # Test boto3 import
    try:
        import boto3
        print("✅ boto3 available for AWS deployment")
    except ImportError:
        print("❌ boto3 not available")
        return False
    
    return True

def run_comprehensive_test():
    """Run all tests and generate report"""
    print("🚀 AutoTasker AI - Production Readiness Test")
    print("=" * 50)
    
    test_results = {}
    start_time = time.time()
    
    # Run all tests
    tests = [
        ("Environment", test_environment),
        ("Dependencies", test_dependencies),
        ("Configuration", test_configuration),
        ("Agents", test_agents),
        ("Backend", test_backend),
        ("LLM Connection", test_llm_connection),
        ("Frontend", test_frontend),
        ("AWS Components", test_aws_components)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            test_results[test_name] = False
    
    # Generate report
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Test Duration: {time.time()-start_time:.2f} seconds")
    
    if passed == total:
        print("\n🎉 All tests passed! AutoTasker AI is production ready.")
        print("Run: streamlit run frontend/streamlit_app_enhanced.py")
    else:
        print(f"\n⚠️ {total-passed} tests failed. Please fix issues before production.")
        print("Check the conda setup guide: docs/CONDA_SETUP_GUIDE.md")
    
    # Save test report
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": test_results,
        "summary": {
            "passed": passed,
            "total": total,
            "success_rate": (passed/total)*100,
            "duration": time.time()-start_time
        }
    }
    
    os.makedirs('data/logs', exist_ok=True)
    with open('data/logs/production_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nTest report saved: data/logs/production_test_report.json")

if __name__ == "__main__":
    run_comprehensive_test()

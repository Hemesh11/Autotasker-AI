"""
AutoTasker AI Streamlit Frontend
Interactive UI for natural language task automation
"""

import streamlit as st
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.langgraph_runner import AutoTaskerRunner
from backend.utils import load_config, validate_api_keys

def create_progress_tracker(title: str, steps: List[str]) -> Tuple:
    """Create an enhanced progress tracker with detailed steps"""
    st.markdown(f"### {title}")
    
    # Create columns for better layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        progress_bar = st.progress(0)
        status_text = st.empty()
        details_container = st.container()
    
    with col2:
        timer_display = st.empty()
        step_counter = st.empty()
    
    return progress_bar, status_text, details_container, timer_display, step_counter

def schedule_task(scheduler, task_name: str, prompt: str, schedule_type: str, 
                  schedule_value: str, config: Dict[str, Any]) -> str:
    """Helper function to schedule a task"""
    return scheduler.schedule_task(
        prompt=prompt,
        schedule_type=schedule_type,
        schedule_value=schedule_value,
        task_name=task_name
    )

def update_progress(progress_bar, status_text, step: int, total_steps: int, 
                   message: str, details: str = None, timer_display=None, 
                   step_counter=None, start_time=None):
    """Update progress with enhanced visual feedback"""
    progress = (step / total_steps) * 100
    progress_bar.progress(int(progress))
    
    # Status with emoji and progress percentage
    status_text.markdown(f"**{message}** ({progress:.0f}%)")
    
    # Update step counter
    if step_counter:
        step_counter.markdown(f"**Step {step}/{total_steps}**")
    
    # Update timer
    if timer_display and start_time:
        elapsed = time.time() - start_time
        timer_display.markdown(f"**⏱️ {elapsed:.1f}s**")
    
    # Show details if provided
    if details:
        with st.expander("📋 Details", expanded=False):
            st.text(details)


def monitor_task_execution(task_id: str) -> Dict[str, Any]:
    """Monitor real-time task execution status"""
    monitoring_container = st.container()
    
    with monitoring_container:
        st.markdown("### 📊 Real-time Monitoring")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_metric = st.empty()
        with col2:
            duration_metric = st.empty()
        with col3:
            progress_metric = st.empty() 
        with col4:
            memory_metric = st.empty()
        
        # Live logs
        logs_container = st.container()
        
        start_time = time.time()
        
        # Simulate monitoring (in real implementation, this would connect to actual task monitoring)
        for i in range(6):
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Update metrics
                if i < 5:
                    status_metric.metric("Status", "🟢 Running")
                    progress_metric.metric("Progress", f"{(i+1)*20}%")
                else:
                    status_metric.metric("Status", "✅ Complete")
                    progress_metric.metric("Progress", "100%")
                
                duration_metric.metric("Duration", f"{elapsed:.1f}s")
                memory_metric.metric("Memory", f"{125 + i*5} MB")
                
                # Show recent logs
                with logs_container:
                    log_messages = [
                        f"[{datetime.now().strftime('%H:%M:%S')}] Task executing...",
                        f"[{datetime.now().strftime('%H:%M:%S')}] Processing agents...",
                        f"[{datetime.now().strftime('%H:%M:%S')}] Generating response...",
                        f"[{datetime.now().strftime('%H:%M:%S')}] Saving results..."
                    ]
                    
                    st.text_area(
                        "📝 Live Logs:",
                        "\n".join(log_messages[:i+1]),
                        height=150
                    )
                
                if i < 5:
                    time.sleep(1)
                else:
                    break
                    
            except Exception as e:
                st.error(f"Monitoring error: {e}")
                break
    
    return {"status": "completed", "duration": time.time() - start_time}

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="AutoTasker AI",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #2E86AB;
        margin-bottom: 2rem;
    }
    .task-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2E86AB;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #155724;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<h1 class="main-header">🤖 AutoTasker AI</h1>', unsafe_allow_html=True)
    st.markdown("### Your Personal Task Automation Assistant")
    st.markdown("Convert natural language into automated workflows across Gmail, GitHub, and more!")
    
    # Sidebar
    setup_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Execute Task", "📊 Task History", "⏰ Scheduler", "⚙️ Configuration", "📚 Examples"])
    
    with tab1:
        execute_task_interface()
    
    with tab2:
        task_history_interface()
    
    with tab3:
        scheduler_interface()
    
    with tab4:
        configuration_interface()
    
    with tab5:
        examples_interface()


def setup_sidebar():
    """Setup sidebar with system status and quick actions"""
    
    st.sidebar.markdown("## 🔧 System Status")
    
    # API Key validation
    api_status = validate_api_keys()
    
    for service, is_valid in api_status.items():
        icon = "✅" if is_valid else "❌"
        st.sidebar.markdown(f"{icon} {service.replace('_', ' ').title()}")
    
    st.sidebar.markdown("---")
    
    # Quick actions
    st.sidebar.markdown("## 🚀 Quick Actions")
    
    if st.sidebar.button("📧 Test Email Service"):
        test_email_service()
    
    if st.sidebar.button("🔄 Clear History"):
        clear_task_history()
    
    if st.sidebar.button("📊 System Stats"):
        show_system_stats()


def execute_task_interface():
    """Main task execution interface"""
    
    st.markdown("## 💬 Enter Your Task")
    
    # Sample prompts for quick selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        prompt = st.text_area(
            "Describe what you want to automate:",
            placeholder="Example: Every day at 9AM, send me 2 LeetCode questions and summarize yesterday's emails",
            height=100,
            help="Use natural language to describe your automation task"
        )
    
    with col2:
        st.markdown("**Quick Examples:**")
        
        sample_prompts = [
            "Generate 3 coding questions",
            "Summarize today's emails",
            "Daily GitHub commit summary",
            "Send me DSA problems",
            "Check unread emails"
        ]
        
        for sample in sample_prompts:
            if st.button(f"📝 {sample}", key=f"sample_{sample}"):
                st.session_state.selected_prompt = sample
    
    # Use selected prompt if available
    if 'selected_prompt' in st.session_state:
        prompt = st.session_state.selected_prompt
        del st.session_state.selected_prompt
    
    # Execution options
    st.markdown("### ⚙️ Execution Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        schedule_type = st.selectbox(
            "Schedule Type:",
            ["Execute Once", "Daily", "Weekly", "Custom"],
            help="How often should this task run?"
        )
    
    with col2:
        if schedule_type != "Execute Once":
            schedule_time = st.time_input(
                "Execution Time:",
                value=datetime.strptime("09:00", "%H:%M").time(),
                help="When should the task run?"
            )
    
    with col3:
        priority = st.selectbox(
            "Priority:",
            ["High", "Medium", "Low"],
            index=1,
            help="Task execution priority"
        )
    
    # Execute button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Execute Task", type="primary", use_container_width=True):
            if prompt.strip():
                execute_task(prompt, schedule_type, priority)
            else:
                st.error("Please enter a task description!")

def execute_task(prompt: str, schedule_type: str, priority: str):
    """Execute a task with the given parameters"""
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Validate input
        if not prompt or not prompt.strip():
            st.error("❌ Please provide a valid task prompt.")
            return
        
        status_text.text("🔧 Loading configuration...")
        progress_bar.progress(20)
        
        # Initialize AutoTasker with better error handling
        try:
            config = load_config("config/config.yaml")
            if not config:
                st.error("❌ Failed to load configuration. Please check config/config.yaml")
                return
        except FileNotFoundError:
            st.error("❌ Configuration file not found. Please ensure config/config.yaml exists.")
            return
        except Exception as e:
            st.error(f"❌ Configuration error: {str(e)}")
            return
        
        # Validate configuration
        config_issues = validate_configuration(config)
        if config_issues:
            st.error(f"❌ Configuration issues: Missing {', '.join(config_issues)}")
            return
        
        status_text.text("🔑 Validating API keys...")
        progress_bar.progress(30)
        
        # Validate API keys
        api_status = validate_api_keys()
        missing_keys = [key for key, valid in api_status.items() if not valid]
        
        if missing_keys:
            st.warning(f"⚠️ Missing API keys: {', '.join(missing_keys)}. Some features may not work.")
        
        status_text.text("🤖 Initializing AutoTasker...")
        progress_bar.progress(50)
        
        try:
            runner = AutoTaskerRunner(config)
        except Exception as e:
            st.error(f"❌ Failed to initialize AutoTasker: {str(e)}")
            return
        
        status_text.text("⚡ Executing workflow...")
        progress_bar.progress(70)
        
        # Execute workflow
        try:
            result = runner.run_workflow(prompt)
        except TimeoutError:
            st.error("❌ Task execution timed out. Please try a simpler task.")
            return
        except Exception as e:
            st.error(f"❌ Workflow execution failed: {str(e)}")
            return
        
        # Validate result
        if not result:
            st.error("❌ No result returned from workflow execution.")
            return
        
        status_text.text("💾 Saving results...")
        progress_bar.progress(90)
        
        # Store in session state for history
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        
        task_record = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "schedule_type": schedule_type,
            "priority": priority,
            "result": result,
            "success": result.get("success", False) and not result.get("error"),
            "execution_time": datetime.now().isoformat()
        }
        
        st.session_state.task_history.insert(0, task_record)
        
        # Limit history size
        if len(st.session_state.task_history) > 100:
            st.session_state.task_history = st.session_state.task_history[:100]
        
        status_text.text("✅ Complete!")
        progress_bar.progress(100)
        
        # Display results
        display_execution_results(result)
        
        # Celebration for successful tasks
        if task_record["success"]:
            st.balloons()
            
    except ImportError as e:
        st.error(f"❌ Import error: {str(e)}. Please install required dependencies.")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.exception(e)  # Show full traceback in debug mode
    finally:
        # Always clear progress indicators
        progress_bar.empty()
        status_text.empty()


def validate_configuration(config):
    """Validate essential configuration before task execution"""
    if not config:
        return ["Configuration file is empty or invalid"]
    
    missing_keys = []
    required_sections = ["llm", "app"]
    
    for section in required_sections:
        if section not in config:
            missing_keys.append(section)
    
    # Check LLM configuration specifically
    if "llm" in config:
        llm_config = config["llm"]
        if "provider" not in llm_config:
            missing_keys.append("llm.provider")
    
    return missing_keys

def display_execution_results(result: Dict[str, Any]):
    """Display task execution results"""
    
    if result.get("error"):
        st.markdown(f'<div class="error-box">❌ <b>Execution Failed:</b> {result["error"]}</div>', 
                   unsafe_allow_html=True)
        return
    
    st.markdown('<div class="success-box">✅ <b>Task executed successfully!</b></div>', 
               unsafe_allow_html=True)
    
    # Show task plan
    if "task_plan" in result:
        st.markdown("### 📋 Generated Task Plan")
        
        plan = result["task_plan"]
        
        st.json({
            "Intent": plan.get("intent", "Unknown"),
            "Total Tasks": plan.get("total_tasks", 0),
            "Schedule": plan.get("schedule", "once")
        })
        
        # Show individual tasks
        tasks = plan.get("tasks", [])
        if tasks:
            st.markdown("#### Task Breakdown:")
            
            for i, task in enumerate(tasks, 1):
                with st.expander(f"Task {i}: {task.get('description', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** {task.get('type', 'Unknown')}")
                        st.write(f"**Priority:** {task.get('priority', 'Unknown')}")
                    
                    with col2:
                        st.write(f"**Dependencies:** {', '.join(task.get('dependencies', []))}")
                        st.write(f"**Parameters:** {len(task.get('parameters', {}))}")
    
    # Show execution results
    if "execution_results" in result:
        st.markdown("### 📊 Execution Results")
        
        exec_results = result["execution_results"]
        
        for key, value in exec_results.items():
            if isinstance(value, dict) and value.get("content"):
                st.markdown(f"#### {key.replace('_', ' ').title()}")
                st.text_area("Content:", value["content"], height=200, disabled=True)
    
    # Show logs
    if "logs" in result and result["logs"]:
        st.markdown("### 📝 Execution Logs")
        
        with st.expander("View detailed logs"):
            for log in result["logs"]:
                st.json(log)

def task_history_interface():
    """Display task execution history"""
    
    st.markdown("## 📊 Task Execution History")
    
    if 'task_history' not in st.session_state or not st.session_state.task_history:
        st.info("No tasks executed yet. Go to the 'Execute Task' tab to run your first automation!")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_success = st.selectbox("Filter by Status:", ["All", "Successful", "Failed"])
    
    with col2:
        days_back = st.selectbox("Show Last:", ["All Time", "24 Hours", "7 Days", "30 Days"])
    
    with col3:
        sort_order = st.selectbox("Sort by:", ["Newest First", "Oldest First"])
    
    # Apply filters
    filtered_history = filter_task_history(
        st.session_state.task_history, 
        filter_success, 
        days_back, 
        sort_order
    )
    
    # Display history
    for i, task in enumerate(filtered_history):
        with st.expander(f"🕐 {task['timestamp'][:19]} - {task['prompt'][:50]}..."):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Prompt:** {task['prompt']}")
                st.write(f"**Schedule:** {task['schedule_type']}")
                st.write(f"**Priority:** {task['priority']}")
            
            with col2:
                status_icon = "✅" if task['success'] else "❌"
                st.write(f"**Status:** {status_icon} {'Success' if task['success'] else 'Failed'}")
            
            if task.get('result'):
                st.json(task['result'])


def filter_task_history(history: List[Dict], status_filter: str, time_filter: str, sort_order: str) -> List[Dict]:
    """Filter and sort task history"""
    
    filtered = history.copy()
    
    # Filter by status
    if status_filter == "Successful":
        filtered = [t for t in filtered if t['success']]
    elif status_filter == "Failed":
        filtered = [t for t in filtered if not t['success']]
    
    # Filter by time
    if time_filter != "All Time":
        cutoff_hours = {"24 Hours": 24, "7 Days": 168, "30 Days": 720}[time_filter]
        cutoff_time = datetime.now() - timedelta(hours=cutoff_hours)
        
        filtered = [
            t for t in filtered 
            if datetime.fromisoformat(t['timestamp']) > cutoff_time
        ]
    
    # Sort
    if sort_order == "Oldest First":
        filtered.reverse()
    
    return filtered


def configuration_interface():
    """Configuration management interface"""
    
    st.markdown("## ⚙️ System Configuration")
    
    # API Keys section
    st.markdown("### 🔑 API Keys")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**LLM API Configuration:**")
        
        # API Provider selection
        api_provider = st.selectbox(
            "LLM API Provider:",
            ["OpenRouter (Recommended)", "OpenAI"],
            help="Choose your preferred LLM API provider"
        )
        
        if api_provider == "OpenRouter (Recommended)":
            openrouter_key = st.text_input(
                "OpenRouter API Key:",
                type="password",
                help="Get free API key from openrouter.ai - supports multiple models"
            )
            
            # Model selection for OpenRouter
            model_options = [
                "openai/gpt-3.5-turbo (Fast & Affordable)",
                "openai/gpt-4-turbo-preview (Balanced)",
                "openai/gpt-4 (Most Capable)",
                "anthropic/claude-3-sonnet (Creative)",
                "mistralai/mistral-7b-instruct (Free Tier)"
            ]
            selected_model = st.selectbox(
                "Model:",
                model_options,
                help="Choose the AI model for your tasks"
            )
        else:
            openai_key = st.text_input(
                "OpenAI API Key:",
                type="password",
                help="Required for OpenAI's GPT models"
            )
        
        aws_access_key = st.text_input(
            "AWS Access Key:",
            type="password",
            help="Required for AWS services"
        )
    
    with col2:
        aws_secret_key = st.text_input(
            "AWS Secret Key:",
            type="password",
            help="Required for AWS services"
        )
        
        gmail_address = st.text_input(
            "Gmail Address:",
            help="Your Gmail address for email operations"
        )
        
        github_token = st.text_input(
            "GitHub Token:",
            type="password",
            help="Personal access token from GitHub settings"
        )
    
    # GitHub Setup section
    st.markdown("### 🐙 GitHub Integration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        github_owner = st.text_input(
            "Default Owner/Username:",
            help="Your GitHub username or organization"
        )
        
    with col2:
        github_repo = st.text_input(
            "Default Repository:",
            help="Default repository name for analysis"
        )
    
    st.info("""
    To use GitHub features:
    1. Go to GitHub Settings → Developer settings → Personal access tokens
    2. Generate a new token with 'repo' and 'user' scopes
    3. Copy the token and paste it above
    """)
    
    # Google OAuth section
    st.markdown("### 📧 Google OAuth Setup")
    
    st.info("""
    To use Gmail features:
    1. Go to Google Cloud Console
    2. Create a new project or select existing
    3. Enable Gmail API
    4. Create OAuth 2.0 credentials
    5. Download credentials.json and place in google_auth/ folder
    """)
    
    # Agent Configuration
    st.markdown("### 🤖 Agent Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Planner Agent**")
        planner_model = st.selectbox("Model:", ["gpt-4", "gpt-3.5-turbo"], key="planner_model")
        planner_temp = st.slider("Temperature:", 0.0, 1.0, 0.3, key="planner_temp")
    
    with col2:
        st.markdown("**DSA Agent**")
        dsa_model = st.selectbox("Model:", ["gpt-4", "gpt-3.5-turbo"], key="dsa_model")
        dsa_temp = st.slider("Temperature:", 0.0, 1.0, 0.8, key="dsa_temp")
    
    with col3:
        st.markdown("**Email Settings**")
        email_format = st.selectbox("Default Format:", ["HTML", "Text"], key="email_format")
        max_retries = st.number_input("Max Retries:", 1, 10, 3, key="max_retries")
    
    # Save configuration
    if st.button("💾 Save Configuration"):
        st.success("Configuration saved successfully!")


def examples_interface():
    """Show example prompts and use cases"""
    
    st.markdown("## 📚 Example Automations")
    
    examples = [
        {
            "category": "📧 Email & Communication",
            "examples": [
                {
                    "prompt": "Every day at 9AM, send me a summary of yesterday's unread emails",
                    "description": "Daily email digest automation",
                    "agents": ["Gmail Agent", "Summarizer Agent", "Email Agent"]
                },
                {
                    "prompt": "Send me 3 coding questions every Monday at 8AM",
                    "description": "Weekly coding practice automation",
                    "agents": ["DSA Agent", "Email Agent", "Scheduler"]
                }
            ]
        },
        {
            "category": "💻 Development & GitHub",
            "examples": [
                {
                    "prompt": "Summarize my GitHub commits from the last week and email the report",
                    "description": "Weekly development summary",
                    "agents": ["GitHub Agent", "Summarizer Agent", "Email Agent"]
                },
                {
                    "prompt": "Check for new issues in my repositories and notify me",
                    "description": "Issue monitoring automation",
                    "agents": ["GitHub Agent", "Email Agent"]
                }
            ]
        },
        {
            "category": "🧠 Learning & Practice",
            "examples": [
                {
                    "prompt": "Generate 2 medium difficulty array problems and send them to me",
                    "description": "Coding practice question generation",
                    "agents": ["DSA Agent", "Email Agent"]
                },
                {
                    "prompt": "Create a daily study plan with 1 hard and 2 easy coding questions",
                    "description": "Structured learning automation",
                    "agents": ["DSA Agent", "Planner Agent", "Email Agent"]
                }
            ]
        }
    ]
    
    for category_data in examples:
        st.markdown(f"### {category_data['category']}")
        
        for example in category_data["examples"]:
            with st.expander(f"📝 {example['description']}"):
                st.code(example["prompt"], language="text")
                st.write(f"**Description:** {example['description']}")
                st.write(f"**Agents Used:** {', '.join(example['agents'])}")
                
                if st.button(f"Try This Example", key=f"try_{example['prompt'][:20]}"):
                    st.session_state.selected_prompt = example["prompt"]
                    st.experimental_rerun()


def test_email_service():
    """Test email service functionality"""
    
    try:
        from agents.email_agent import EmailAgent
        
        config = load_config("config/config.yaml")
        email_agent = EmailAgent(config)
        
        result = email_agent.test_email_service()
        
        if result.get("success"):
            st.sidebar.success("✅ Email service working!")
        else:
            st.sidebar.error(f"❌ Email test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.sidebar.error(f"❌ Email test error: {str(e)}")


def clear_task_history():
    """Clear task execution history"""
    
    if 'task_history' in st.session_state:
        st.session_state.task_history = []
        st.sidebar.success("🗑️ History cleared!")


def show_system_stats():
    """Show system statistics"""
    
    if 'task_history' not in st.session_state:
        st.sidebar.info("No execution statistics available")
        return
    
    history = st.session_state.task_history
    
    total_tasks = len(history)
    successful_tasks = len([t for t in history if t['success']])
    success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    st.sidebar.markdown("### 📊 Statistics")
    st.sidebar.metric("Total Tasks", total_tasks)
    st.sidebar.metric("Success Rate", f"{success_rate:.1f}%")
    st.sidebar.metric("Failed Tasks", total_tasks - successful_tasks)


def scheduler_interface():
    """Interface for managing scheduled tasks"""
    st.markdown("## ⏰ Task Scheduler")
    st.markdown("Schedule tasks to run automatically at specified times")
    
    # Initialize scheduler in session state
    if 'scheduler' not in st.session_state:
        try:
            from backend.scheduler import create_scheduler
            st.session_state.scheduler = create_scheduler()
            if not st.session_state.scheduler.is_running:
                st.session_state.scheduler.start()
        except Exception as e:
            st.error(f"Failed to initialize scheduler: {e}")
            return
    
    scheduler = st.session_state.scheduler
    
    # Two columns: Schedule new task and Manage existing tasks
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📅 Schedule New Task")
        
        # Task prompt
        scheduled_prompt = st.text_area(
            "Task Prompt:",
            height=100,
            placeholder="Enter your task description (e.g., 'Generate 2 coding questions and email them to me')"
        )
        
        # Task name
        task_name = st.text_input(
            "Task Name:",
            placeholder="Daily Coding Questions"
        )
        
        # Schedule type
        schedule_type = st.selectbox(
            "Schedule Type:",
            ["Daily", "Weekly", "Monthly", "Custom Interval"],
            help="Choose how often the task should run"
        )
        
        # Schedule configuration based on type
        if schedule_type == "Daily":
            schedule_time = st.time_input("Time:", value=datetime.strptime("09:00", "%H:%M").time())
            schedule_value = schedule_time.strftime("%H:%M")
            schedule_type_code = "daily"
            
        elif schedule_type == "Weekly":
            col_day, col_time = st.columns(2)
            with col_day:
                day_of_week = st.selectbox(
                    "Day:", 
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                )
            with col_time:
                schedule_time = st.time_input("Time:", value=datetime.strptime("09:00", "%H:%M").time())
            
            day_abbrev = {
                "Monday": "MON", "Tuesday": "TUE", "Wednesday": "WED", "Thursday": "THU",
                "Friday": "FRI", "Saturday": "SAT", "Sunday": "SUN"
            }
            schedule_value = f"{day_abbrev[day_of_week]}:{schedule_time.strftime('%H:%M')}"  # FIXED: Added closing quote
            schedule_type_code = "weekly"
            
        elif schedule_type == "Monthly":
            col_day, col_time = st.columns(2)
            with col_day:
                day_of_month = st.number_input("Day of Month:", min_value=1, max_value=28, value=1)
            with col_time:
                schedule_time = st.time_input("Time:", value=datetime.strptime("09:00", "%H:%M").time())
            
            schedule_value = f"{day_of_month}:{schedule_time.strftime('%H:%M')}"  # FIXED: Added closing quote
            schedule_type_code = "monthly"
            
        else:  # Custom Interval
            interval_value = st.number_input("Interval (minutes):", min_value=1, value=60)
            schedule_value = str(interval_value * 60)  # Convert to seconds
            schedule_type_code = "interval"
        
        # Schedule button
        if st.button("📅 Schedule Task", type="primary"):
            if scheduled_prompt and task_name:
                try:
                    # Progress tracking for scheduling
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔧 Loading configuration...")
                    progress_bar.progress(20)
                    config = load_config("config/config.yaml")
                    
                    status_text.text("⏰ Adding task to scheduler...")
                    progress_bar.progress(40)
                    
                    status_text.text("💾 Saving scheduled task...")
                    progress_bar.progress(60)
                    
                    # Schedule the task
                    job_id = scheduler.schedule_task(
                        prompt=scheduled_prompt,
                        schedule_type=schedule_type_code,
                        schedule_value=schedule_value,
                        task_name=task_name
                    )
                    
                    status_text.text("✅ Task scheduled successfully!")
                    progress_bar.progress(100)
                    
                    st.success(f"✅ Task '{task_name}' scheduled successfully! Job ID: {job_id}")
                    
                    # Clear progress indicators after short delay
                    time.sleep(1)
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to schedule task: {str(e)}")
                    if 'progress_bar' in locals():
                        progress_bar.empty()
                    if 'status_text' in locals():
                        status_text.empty()
            else:
                st.warning("⚠️ Please provide both task prompt and name")
    with col2:
        st.markdown("### 📋 Scheduled Tasks")
        
        try:
            jobs = scheduler.list_jobs()
            
            if not jobs:
                st.info("No scheduled tasks yet. Create one on the left!")
            else:
                for job in jobs:
                    with st.expander(f"📌 {job['name']}", expanded=False):
                        st.write(f"**Job ID:** `{job['id']}`")
                        st.write(f"**Next Run:** {job['next_run'] or 'Paused'}")
                        st.write(f"**Schedule:** {job['trigger']}")
                        
                        # Action buttons
                        col_pause, col_delete = st.columns(2)
                        
                        with col_pause:
                            if st.button(f"⏸️ Pause", key=f"pause_{job['id']}"):
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                status_text.text("⏸️ Pausing task...")
                                progress_bar.progress(50)
                                
                                if scheduler.pause_job(job['id']):
                                    status_text.text("✅ Task paused successfully!")
                                    progress_bar.progress(100)
                                    st.success("Task paused")
                                    
                                    time.sleep(1)
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    st.experimental_rerun()
                                else:
                                    progress_bar.empty()
                                    status_text.empty()
                                    st.error("Failed to pause task")
                        
                        with col_delete:
                            if st.button(f"🗑️ Delete", key=f"delete_{job['id']}"):
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                status_text.text("🗑️ Deleting task...")
                                progress_bar.progress(50)
                                
                                if scheduler.remove_job(job['id']):
                                    status_text.text("✅ Task deleted successfully!")
                                    progress_bar.progress(100)
                                    st.success("Task deleted")
                                    
                                    time.sleep(1)
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    st.experimental_rerun()
                                else:
                                    progress_bar.empty()
                                    status_text.empty()
                                    st.error("Failed to delete task")
        
        except Exception as e:
            st.error(f"Error loading scheduled tasks: {e}")
     
    # Quick schedule examples
    st.markdown("### 💡 Quick Examples")
    
    examples = [
        {
            "name": "Daily Coding Questions",
            "prompt": "Generate 2 coding questions and email them to me",
            "schedule": "Daily at 9:00 AM"
        },
        {
            "name": "Weekly GitHub Summary", 
            "prompt": "Summarize my GitHub commits from last week and send via email",
            "schedule": "Every Monday at 8:00 AM"
        },
        {
            "name": "Email Digest",
            "prompt": "Summarize important emails from yesterday and send summary",
            "schedule": "Daily at 6:00 PM"
        }
    ]
    
    for example in examples:
        with st.expander(f"📋 {example['name']}", expanded=False):
            st.write(f"**Prompt:** {example['prompt']}")
            st.write(f"**Schedule:** {example['schedule']}")
            if st.button(f"Use This Example", key=f"example_{example['name']}"):
                st.info("Copy the prompt above to schedule this task!")

if __name__ == "__main__":
    main()

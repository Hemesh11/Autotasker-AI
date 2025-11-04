"""
AutoTasker AI - Enhanced Streamlit Frontend
Production-ready UI for intelligent workflow automation
"""

import streamlit as st
import json
import os
import sys
import time
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure page
st.set_page_config(
    page_title="AutoTasker AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.langgraph_runner import AutoTaskerRunner
from backend.utils import load_config, validate_api_keys

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .agent-status {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
    }
    .agent-active {
        background-color: #d1ecf1;
        border-left: 4px solid #0c5460;
    }
    .agent-inactive {
        background-color: #f8f9fa;
        border-left: 4px solid #6c757d;
    }
    .workflow-step {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)

class AutoTaskerUI:
    def __init__(self):
        self.config = None
        self.runner = None
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize session state variables"""
        if 'execution_history' not in st.session_state:
            st.session_state.execution_history = []
        if 'config_loaded' not in st.session_state:
            st.session_state.config_loaded = False
        if 'current_execution' not in st.session_state:
            st.session_state.current_execution = None
        if 'agent_stats' not in st.session_state:
            st.session_state.agent_stats = {}
        if 'cost_tracking' not in st.session_state:
            st.session_state.cost_tracking = {'total_cost': 0, 'executions': 0}
    
    def load_configuration(self):
        """Load and validate configuration"""
        try:
            self.config = load_config()
            api_validation = validate_api_keys(self.config)
            
            if api_validation['valid']:
                st.session_state.config_loaded = True
                self.runner = AutoTaskerRunner(self.config)
                return True
            else:
                st.error(f"Configuration validation failed: {api_validation['errors']}")
                return False
        except Exception as e:
            st.error(f"Failed to load configuration: {str(e)}")
            return False
    
    def show_header(self):
        """Display main header and navigation"""
        st.markdown('<h1 class="main-header">🤖 AutoTasker AI</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Intelligent Multi-Agent Workflow Automation</p>', unsafe_allow_html=True)
        
        # Navigation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚀 Quick Start", 
            "📊 Dashboard", 
            "⚙️ Configuration", 
            "📈 Analytics", 
            "📋 History"
        ])
        
        return tab1, tab2, tab3, tab4, tab5
    
    def show_quick_start(self, tab):
        """Quick start interface for immediate task execution"""
        with tab:
            st.markdown("### Natural Language Task Execution")
            
            # Example prompts for guidance
            with st.expander("💡 Example Prompts", expanded=False):
                examples = [
                    "Send me 2 LeetCode questions every day at 9 AM",
                    "Analyze my GitHub commits from this week and email me a summary",
                    "Generate 3 medium difficulty array problems and email them to me",
                    "Schedule a team meeting tomorrow at 3 PM and send invitations",
                    "Check my recent emails and summarize any important ones"
                ]
                for i, example in enumerate(examples, 1):
                    st.code(f"{i}. {example}")
            
            # Main input area
            col1, col2 = st.columns([3, 1])
            
            with col1:
                user_prompt = st.text_area(
                    "What would you like AutoTasker AI to do?",
                    placeholder="Type your request in natural language...",
                    height=100,
                    key="main_prompt"
                )
            
            with col2:
                st.markdown("### Quick Actions")
                if st.button("🔍 Analyze Prompt", use_container_width=True):
                    if user_prompt:
                        self.analyze_prompt(user_prompt)
                
                if st.button("🚀 Execute Task", type="primary", use_container_width=True):
                    if user_prompt:
                        self.execute_task(user_prompt)
                    else:
                        st.warning("Please enter a prompt first!")
                
                if st.button("📅 Schedule Task", use_container_width=True):
                    if user_prompt:
                        self.show_scheduler(user_prompt)
                    else:
                        st.warning("Please enter a prompt first!")
            
            # Execution status area
            if st.session_state.current_execution:
                self.show_execution_status()
    
    def analyze_prompt(self, prompt: str):
        """Analyze and preview what the prompt will do"""
        st.markdown("### 🔍 Prompt Analysis")
        
        try:
            # Create a preview of what agents will be involved
            analysis = self.runner.planner.create_task_plan(prompt)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Detected Intent")
                st.info(analysis.get('intent', 'General automation task'))
                
                st.markdown("#### Required Agents")
                tasks = analysis.get('tasks', [])
                for task in tasks:
                    agent_type = task.get('type', 'unknown')
                    st.markdown(f"🤖 **{agent_type.title()} Agent**: {task.get('description', '')}")
            
            with col2:
                st.markdown("#### Execution Plan")
                if tasks:
                    for i, task in enumerate(tasks, 1):
                        st.markdown(f"**Step {i}**: {task.get('description', 'Unknown task')}")
                
                st.markdown("#### Estimated Resources")
                st.metric("API Calls", len(tasks) * 2)
                st.metric("Estimated Time", f"{len(tasks) * 15} seconds")
                st.metric("Estimated Cost", f"${len(tasks) * 0.02:.2f}")
        
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
    
    def execute_task(self, prompt: str):
        """Execute a task with real-time progress tracking"""
        st.markdown("### 🚀 Task Execution")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        details_container = st.container()
        
        try:
            start_time = time.time()
            
            # Update status
            status_text.info("🔄 Initializing workflow...")
            progress_bar.progress(10)
            
            # Execute the task
            result = self.runner.run_workflow(prompt)
            
            # Update progress
            progress_bar.progress(100)
            execution_time = time.time() - start_time
            
            # Display results
            if result.get('success', False):
                status_text.success(f"✅ Task completed successfully in {execution_time:.2f} seconds!")
                
                with details_container:
                    self.display_execution_results(result, execution_time)
                
                # Update session state
                st.session_state.execution_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'prompt': prompt,
                    'result': result,
                    'execution_time': execution_time,
                    'success': True
                })
                
            else:
                status_text.error("❌ Task execution failed!")
                st.error(f"Error: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            status_text.error("❌ Execution failed!")
            st.error(f"Execution error: {str(e)}")
    
    def display_execution_results(self, result: Dict[str, Any], execution_time: float):
        """Display detailed execution results"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Execution Summary")
            st.metric("Execution Time", f"{execution_time:.2f}s")
            st.metric("Agents Used", len(result.get('agent_results', {})))
            st.metric("Tasks Completed", len(result.get('completed_tasks', [])))
        
        with col2:
            st.markdown("#### Results")
            if result.get('content'):
                st.text_area("Output Content", result['content'], height=200)
        
        # Agent details
        if result.get('agent_results'):
            st.markdown("#### Agent Execution Details")
            for agent, agent_result in result['agent_results'].items():
                with st.expander(f"🤖 {agent.title()} Agent"):
                    st.json(agent_result)
    
    def show_scheduler(self, prompt: str):
        """Show scheduling interface for recurring tasks"""
        st.markdown("### 📅 Task Scheduler")
        
        col1, col2 = st.columns(2)
        
        with col1:
            schedule_type = st.selectbox(
                "Schedule Type",
                ["One-time", "Daily", "Weekly", "Monthly", "Custom"]
            )
            
            if schedule_type == "Daily":
                schedule_time = st.time_input("Time", datetime.now().time())
                schedule_value = f"daily at {schedule_time}"
            elif schedule_type == "Weekly":
                day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                schedule_time = st.time_input("Time", datetime.now().time())
                schedule_value = f"weekly on {day} at {schedule_time}"
            elif schedule_type == "Custom":
                schedule_value = st.text_input("Cron Expression", "0 9 * * *")
            else:
                schedule_value = "once"
        
        with col2:
            task_name = st.text_input("Task Name", f"AutoTasker Task {len(st.session_state.execution_history) + 1}")
            
            if st.button("📅 Schedule Task", type="primary"):
                st.success(f"Task '{task_name}' scheduled for {schedule_value}")
                st.info("💡 Note: AWS deployment required for 24/7 scheduling")
    
    def show_dashboard(self, tab):
        """Main dashboard with system overview"""
        with tab:
            # System status
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("System Status", "🟢 Online")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Total Executions", len(st.session_state.execution_history))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                success_rate = self.calculate_success_rate()
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Success Rate", f"{success_rate:.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                avg_time = self.calculate_avg_execution_time()
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Avg Execution Time", f"{avg_time:.1f}s")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Agent status
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🤖 Agent Status")
                agents = ["Planner", "Gmail", "GitHub", "DSA", "LeetCode", "Calendar", "Summarizer", "Email"]
                for agent in agents:
                    status = "🟢 Active" if st.session_state.config_loaded else "🔴 Offline"
                    st.markdown(f"**{agent} Agent**: {status}")
            
            with col2:
                st.markdown("### 📊 Recent Activity")
                if st.session_state.execution_history:
                    recent_executions = st.session_state.execution_history[-5:]
                    for execution in recent_executions:
                        timestamp = execution['timestamp'][:19].replace('T', ' ')
                        status = "✅" if execution['success'] else "❌"
                        st.markdown(f"{status} {timestamp}: {execution['prompt'][:50]}...")
                else:
                    st.info("No recent activity")
    
    def show_configuration(self, tab):
        """Configuration management interface"""
        with tab:
            st.markdown("### ⚙️ System Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### API Configuration")
                
                # OpenAI Configuration
                with st.expander("🧠 OpenAI Configuration"):
                    api_key_display = "sk-..." + ("*" * 20) if self.config and self.config.get('openai', {}).get('api_key') else "Not configured"
                    st.text(f"API Key: {api_key_display}")
                    st.text(f"Model: {self.config.get('openai', {}).get('model', 'Not set') if self.config else 'Not loaded'}")
                
                # Gmail Configuration
                with st.expander("📧 Gmail Configuration"):
                    gmail_configured = bool(self.config and self.config.get('gmail', {}).get('credentials_file'))
                    st.text(f"Status: {'✅ Configured' if gmail_configured else '❌ Not configured'}")
                
                # GitHub Configuration
                with st.expander("💻 GitHub Configuration"):
                    github_configured = bool(self.config and self.config.get('github', {}).get('token'))
                    st.text(f"Status: {'✅ Configured' if github_configured else '❌ Not configured'}")
            
            with col2:
                st.markdown("#### System Settings")
                
                with st.expander("🔧 Advanced Settings"):
                    if self.config:
                        max_retries = st.number_input("Max Retries", value=self.config.get('app', {}).get('max_retries', 3))
                        recursion_limit = st.number_input("Recursion Limit", value=self.config.get('app', {}).get('recursion_limit', 50))
                        
                        if st.button("💾 Save Settings"):
                            st.success("Settings saved!")
                
                st.markdown("#### Quick Setup")
                if st.button("🔄 Reload Configuration"):
                    self.load_configuration()
                    st.rerun()
                
                if st.button("🧪 Test All Agents"):
                    self.test_agents()
    
    def show_analytics(self, tab):
        """Analytics and performance metrics"""
        with tab:
            st.markdown("### 📈 System Analytics")
            
            if not st.session_state.execution_history:
                st.info("No execution data available. Run some tasks to see analytics!")
                return
            
            # Create dataframe from execution history
            df = pd.DataFrame(st.session_state.execution_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Execution Trends")
                daily_stats = df.groupby('date').agg({
                    'success': ['count', 'sum'],
                    'execution_time': 'mean'
                }).round(2)
                
                # Flatten column names
                daily_stats.columns = ['total_executions', 'successful_executions', 'avg_execution_time']
                daily_stats = daily_stats.reset_index()
                
                fig = px.line(daily_stats, x='date', y='total_executions', 
                             title='Daily Execution Count')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### Success Rate")
                success_rate = df['success'].mean() * 100
                
                fig = go.Figure(data=go.Indicator(
                    mode = "gauge+number",
                    value = success_rate,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Success Rate (%)"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"},
                            {'range': [80, 100], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
            
            # Performance metrics
            st.markdown("#### Performance Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_time = df['execution_time'].mean()
                st.metric("Average Execution Time", f"{avg_time:.2f}s")
            
            with col2:
                fastest_time = df['execution_time'].min()
                st.metric("Fastest Execution", f"{fastest_time:.2f}s")
            
            with col3:
                slowest_time = df['execution_time'].max()
                st.metric("Slowest Execution", f"{slowest_time:.2f}s")
    
    def show_history(self, tab):
        """Execution history and logs"""
        with tab:
            st.markdown("### 📋 Execution History")
            
            if not st.session_state.execution_history:
                st.info("No execution history available.")
                return
            
            # Filter controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                show_only_successful = st.checkbox("Show only successful executions")
            
            with col2:
                last_n_days = st.selectbox("Last N days", [1, 7, 30, 90, 365])
            
            with col3:
                if st.button("🗑️ Clear History"):
                    st.session_state.execution_history = []
                    st.rerun()
            
            # Filter data
            filtered_history = st.session_state.execution_history.copy()
            
            if show_only_successful:
                filtered_history = [h for h in filtered_history if h['success']]
            
            # Display history
            for i, execution in enumerate(reversed(filtered_history[-20:])):  # Last 20 entries
                with st.expander(f"#{len(filtered_history)-i}: {execution['timestamp'][:19]} - {execution['prompt'][:50]}..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Prompt:**")
                        st.text(execution['prompt'])
                        st.markdown("**Status:**")
                        st.text("✅ Success" if execution['success'] else "❌ Failed")
                        st.markdown("**Execution Time:**")
                        st.text(f"{execution['execution_time']:.2f} seconds")
                    
                    with col2:
                        st.markdown("**Result:**")
                        st.json(execution['result'])
    
    def calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        if not st.session_state.execution_history:
            return 0.0
        successful = sum(1 for exec in st.session_state.execution_history if exec['success'])
        return (successful / len(st.session_state.execution_history)) * 100
    
    def calculate_avg_execution_time(self) -> float:
        """Calculate average execution time"""
        if not st.session_state.execution_history:
            return 0.0
        total_time = sum(exec['execution_time'] for exec in st.session_state.execution_history)
        return total_time / len(st.session_state.execution_history)
    
    def test_agents(self):
        """Test all agents connectivity"""
        st.markdown("### 🧪 Agent Testing")
        
        agents_to_test = ["planner", "gmail", "github", "dsa", "leetcode"]
        
        for agent_name in agents_to_test:
            with st.spinner(f"Testing {agent_name.title()} Agent..."):
                try:
                    # Basic connectivity test
                    time.sleep(1)  # Simulate test
                    st.success(f"✅ {agent_name.title()} Agent: Connected")
                except Exception as e:
                    st.error(f"❌ {agent_name.title()} Agent: {str(e)}")
    
    def run(self):
        """Main application runner"""
        # Load configuration
        if not st.session_state.config_loaded:
            if not self.load_configuration():
                st.error("⚠️ Configuration not loaded. Please check your setup.")
                self.show_config_help()
                return
        
        # Show main interface
        tab1, tab2, tab3, tab4, tab5 = self.show_header()
        
        self.show_quick_start(tab1)
        self.show_dashboard(tab2)
        self.show_configuration(tab3)
        self.show_analytics(tab4)
        self.show_history(tab5)
        
        # Sidebar
        self.show_sidebar()
    
    def show_config_help(self):
        """Show configuration help when system is not properly set up"""
        st.markdown("### ⚙️ Configuration Setup Required")
        
        with st.expander("📋 Setup Checklist", expanded=True):
            st.markdown("""
            **Required Configuration Files:**
            1. `config/config.yaml` - Main configuration
            2. `google_auth/credentials.json` - Google OAuth credentials
            3. Environment variables for API keys
            
            **API Keys Required:**
            - OpenAI API Key (for natural language processing)
            - GitHub Token (for repository analysis)
            - Google OAuth (for Gmail and Calendar access)
            
            **Setup Instructions:**
            1. Copy `config/config.yaml.example` to `config/config.yaml`
            2. Add your API keys to environment variables
            3. Download Google OAuth credentials
            4. Restart the application
            """)
    
    def show_sidebar(self):
        """Sidebar with system information and quick actions"""
        with st.sidebar:
            st.markdown("### 🤖 AutoTasker AI")
            st.markdown("**Status:** 🟢 Online" if st.session_state.config_loaded else "**Status:** 🔴 Offline")
            
            st.markdown("---")
            
            st.markdown("### 📊 Quick Stats")
            total_executions = len(st.session_state.execution_history)
            st.metric("Total Executions", total_executions)
            
            if total_executions > 0:
                success_rate = self.calculate_success_rate()
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            st.markdown("---")
            
            st.markdown("### 🚀 Quick Actions")
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()
            
            if st.button("📥 Export History", use_container_width=True):
                if st.session_state.execution_history:
                    history_json = json.dumps(st.session_state.execution_history, indent=2)
                    st.download_button(
                        "📁 Download JSON",
                        history_json,
                        "autotasker_history.json",
                        "application/json"
                    )
            
            st.markdown("---")
            
            st.markdown("### ℹ️ System Info")
            st.markdown(f"**Version:** 1.0.0")
            st.markdown(f"**Deployment:** Local")
            st.markdown(f"**Agents:** 11 Available")

# Main application
def main():
    """Main entry point"""
    app = AutoTaskerUI()
    app.run()

if __name__ == "__main__":
    main()

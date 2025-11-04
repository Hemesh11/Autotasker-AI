"""
Performance Monitoring for AutoTasker AI
Tracks execution time, metrics, and provides performance insights
"""

import time
import logging
import functools
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class PerformanceMetric:
    """Single performance metric"""
    operation: str
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark operation as complete"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "operation": self.operation,
            "duration_ms": round(self.duration * 1000, 2),
            "duration_seconds": round(self.duration, 2),
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


class PerformanceMonitor:
    """Monitors and tracks performance metrics"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.current_operation: Optional[PerformanceMetric] = None
        self.logger = logging.getLogger(__name__)
        self.workflow_start_time: float = 0.0
        self.workflow_end_time: float = 0.0
    
    def start_workflow(self):
        """Mark workflow start"""
        self.workflow_start_time = time.time()
        self.metrics = []  # Reset metrics for new workflow
    
    def end_workflow(self):
        """Mark workflow end"""
        self.workflow_end_time = time.time()
    
    def start_operation(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetric:
        """Start tracking an operation"""
        metric = PerformanceMetric(
            operation=operation,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self.metrics.append(metric)
        self.current_operation = metric
        return metric
    
    def end_operation(self, success: bool = True, error: Optional[str] = None):
        """End current operation"""
        if self.current_operation:
            self.current_operation.complete(success, error)
            self.current_operation = None
    
    def get_total_duration(self) -> float:
        """Get total workflow duration"""
        if self.workflow_start_time and self.workflow_end_time:
            return self.workflow_end_time - self.workflow_start_time
        elif self.workflow_start_time:
            return time.time() - self.workflow_start_time
        return 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        total_duration = self.get_total_duration()
        
        # Calculate per-operation statistics
        operation_stats = {}
        for metric in self.metrics:
            op = metric.operation
            if op not in operation_stats:
                operation_stats[op] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "min_duration": float('inf'),
                    "max_duration": 0.0,
                    "success_count": 0,
                    "failure_count": 0
                }
            
            stats = operation_stats[op]
            stats["count"] += 1
            stats["total_duration"] += metric.duration
            stats["min_duration"] = min(stats["min_duration"], metric.duration)
            stats["max_duration"] = max(stats["max_duration"], metric.duration)
            
            if metric.success:
                stats["success_count"] += 1
            else:
                stats["failure_count"] += 1
        
        # Calculate averages
        for op, stats in operation_stats.items():
            stats["avg_duration"] = stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0
            stats["success_rate"] = (stats["success_count"] / stats["count"] * 100) if stats["count"] > 0 else 0
        
        return {
            "total_duration_seconds": round(total_duration, 2),
            "total_duration_ms": round(total_duration * 1000, 2),
            "total_operations": len(self.metrics),
            "successful_operations": len([m for m in self.metrics if m.success]),
            "failed_operations": len([m for m in self.metrics if not m.success]),
            "operation_stats": operation_stats,
            "detailed_metrics": [m.to_dict() for m in self.metrics]
        }
    
    def get_formatted_report(self) -> str:
        """Get human-readable performance report"""
        summary = self.get_summary()
        
        lines = [
            "=" * 60,
            "PERFORMANCE REPORT",
            "=" * 60,
            f"Total Duration: {summary['total_duration_seconds']:.2f}s ({summary['total_duration_ms']:.0f}ms)",
            f"Total Operations: {summary['total_operations']}",
            f"✅ Successful: {summary['successful_operations']}",
            f"❌ Failed: {summary['failed_operations']}",
            "",
            "OPERATION BREAKDOWN:",
            "-" * 60
        ]
        
        # Sort operations by total duration (descending)
        sorted_ops = sorted(
            summary['operation_stats'].items(),
            key=lambda x: x[1]['total_duration'],
            reverse=True
        )
        
        for op_name, stats in sorted_ops:
            lines.append(f"\n📊 {op_name}")
            lines.append(f"   Count: {stats['count']}")
            lines.append(f"   Total: {stats['total_duration']:.2f}s")
            lines.append(f"   Avg: {stats['avg_duration']:.2f}s")
            lines.append(f"   Min: {stats['min_duration']:.2f}s")
            lines.append(f"   Max: {stats['max_duration']:.2f}s")
            lines.append(f"   Success Rate: {stats['success_rate']:.1f}%")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)


def time_operation(operation_name: str = None):
    """
    Decorator to automatically time function execution
    
    Usage:
        @time_operation("planner_agent.create_plan")
        def create_task_plan(self, prompt):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get operation name (use provided or generate from function)
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Try to get monitor from first arg (self)
            monitor = None
            if args and hasattr(args[0], '_performance_monitor'):
                monitor = args[0]._performance_monitor
            elif args and hasattr(args[0], 'performance_monitor'):
                monitor = args[0].performance_monitor
            
            # Start tracking if monitor exists
            if monitor:
                metric = monitor.start_operation(op_name, {
                    "function": func.__name__,
                    "module": func.__module__
                })
            
            start_time = time.time()
            error = None
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                
                # End tracking if monitor exists
                if monitor:
                    monitor.end_operation(success, error)
                
                # Log performance
                logger = logging.getLogger(func.__module__)
                if success:
                    logger.debug(f"{op_name} completed in {duration:.2f}s")
                else:
                    logger.warning(f"{op_name} failed after {duration:.2f}s: {error}")
        
        return wrapper
    return decorator


# Global performance monitor for workflow tracking
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def reset_global_monitor():
    """Reset global monitor"""
    global _global_monitor
    _global_monitor = PerformanceMonitor()


if __name__ == "__main__":
    # Test the performance monitor
    monitor = PerformanceMonitor()
    monitor.start_workflow()
    
    # Simulate operations
    metric1 = monitor.start_operation("test_operation_1")
    time.sleep(0.1)
    monitor.end_operation(success=True)
    
    metric2 = monitor.start_operation("test_operation_2")
    time.sleep(0.2)
    monitor.end_operation(success=True)
    
    metric3 = monitor.start_operation("test_operation_1")
    time.sleep(0.15)
    monitor.end_operation(success=False, error="Test error")
    
    monitor.end_workflow()
    
    print(monitor.get_formatted_report())

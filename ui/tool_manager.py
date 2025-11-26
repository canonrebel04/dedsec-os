"""
DedSecOS Tool Registration System

Provides dynamic tool loading and management for the DedSec cyberdeck application.

This module implements a registry pattern for security tools, enabling:
- Dynamic tool registration and discovery
- Tool metadata management (name, category, icon, description)
- Lazy loading for performance
- Dependency injection for tool callbacks
- Category-based organization
- Tool state tracking and validation

Architecture:
    ToolManager (Singleton)
    ├── Tool Registry (Dict[str, ToolMetadata])
    ├── Category Index (Dict[str, List[str]])
    ├── Lazy Loaders (Dict[str, Callable])
    └── Active Tools (Set[str])

Tool Categories:
    WIFI: WiFi scanning, deauth, handshake capture
    NETWORK: Port scanning, ARP spoofing, packet capture
    BLUETOOTH: BLE scanning, device enumeration
    SYSTEM: System info, diagnostics, configuration
    EXPLOIT: Exploitation frameworks, payloads
    RECON: Reconnaissance, OSINT, information gathering

Usage:
    from ui.tool_manager import ToolManager, ToolMetadata, ToolCategory
    
    # Get singleton instance
    manager = ToolManager.get_instance()
    
    # Register a tool
    tool = ToolMetadata(
        id="wifi_scan",
        name="WiFi Scanner",
        category=ToolCategory.WIFI,
        icon="📡",
        description="Scan for wireless networks",
        callback=lambda: scan_wifi()
    )
    manager.register_tool(tool)
    
    # Get tools by category
    wifi_tools = manager.get_tools_by_category(ToolCategory.WIFI)
    
    # Execute a tool
    manager.execute_tool("wifi_scan")
"""

import enum
import inspect
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from pathlib import Path

# Import logging
try:
    from core.logging import get_logger, log_error, audit_log, error_boundary
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    def error_boundary(fallback_value=None, **kwargs):
        def decorator(func):
            return func
        return decorator
    def audit_log(*args, **kwargs):
        pass


class ToolCategory(enum.Enum):
    """Tool categories for organization."""
    WIFI = "wifi"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"
    SYSTEM = "system"
    EXPLOIT = "exploit"
    RECON = "recon"
    CUSTOM = "custom"


class ToolStatus(enum.Enum):
    """Tool execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class ToolMetadata:
    """
    Metadata for a registered tool.
    
    Attributes:
        id: Unique tool identifier (e.g., "wifi_scan")
        name: Display name (e.g., "WiFi Scanner")
        category: Tool category (ToolCategory enum)
        icon: Icon/emoji for UI display
        description: Brief description of tool functionality
        callback: Function to execute when tool is activated
        requires_root: Whether tool requires root privileges
        requires_network: Whether tool requires network access
        requires_dependencies: List of required external commands
        version: Tool version string
        author: Tool author/maintainer
        enabled: Whether tool is currently enabled
    """
    id: str
    name: str
    category: ToolCategory
    icon: str
    description: str
    callback: Callable[[], Any]
    requires_root: bool = False
    requires_network: bool = False
    requires_dependencies: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "DedSec Team"
    enabled: bool = True
    
    def __post_init__(self):
        """Validate tool metadata after initialization."""
        if not self.id:
            raise ValueError("Tool ID cannot be empty")
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not callable(self.callback):
            raise ValueError("Tool callback must be callable")
        if not self.icon:
            self.icon = "🔧"  # Default icon


@dataclass
class ToolExecutionContext:
    """
    Context information for tool execution.
    
    Attributes:
        tool_id: ID of the tool being executed
        status: Current execution status
        result: Result of tool execution
        error: Error message if execution failed
        start_time: Execution start timestamp
        end_time: Execution end timestamp
        metadata: Additional execution metadata
    """
    tool_id: str
    status: ToolStatus = ToolStatus.IDLE
    result: Any = None
    error: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolManager:
    """
    Singleton tool registration and management system.
    
    Manages the lifecycle of security tools including registration,
    discovery, validation, and execution.
    
    Example:
        manager = ToolManager.get_instance()
        manager.register_tool(tool_metadata)
        wifi_tools = manager.get_tools_by_category(ToolCategory.WIFI)
        manager.execute_tool("wifi_scan")
    """
    
    _instance: Optional['ToolManager'] = None
    
    def __init__(self):
        """Initialize the tool manager."""
        if ToolManager._instance is not None:
            raise RuntimeError("ToolManager is a singleton. Use get_instance()")
        
        self._registry: Dict[str, ToolMetadata] = {}
        self._category_index: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        self._active_tools: Set[str] = set()
        self._execution_contexts: Dict[str, ToolExecutionContext] = {}
        self._lazy_loaders: Dict[str, Callable[[], ToolMetadata]] = {}
        
        logger.info("ToolManager initialized")
    
    @classmethod
    def get_instance(cls) -> 'ToolManager':
        """
        Get the singleton ToolManager instance.
        
        Returns:
            ToolManager singleton instance
        
        Example:
            manager = ToolManager.get_instance()
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None
    
    def register_tool(self, tool: ToolMetadata) -> bool:
        """
        Register a tool with the manager.
        
        Args:
            tool: ToolMetadata instance
        
        Returns:
            True if registration successful, False otherwise
        
        Example:
            tool = ToolMetadata(
                id="wifi_scan",
                name="WiFi Scanner",
                category=ToolCategory.WIFI,
                icon="📡",
                description="Scan networks",
                callback=scan_wifi
            )
            manager.register_tool(tool)
        """
        try:
            # Validate tool
            if tool.id in self._registry:
                logger.warning(f"Tool {tool.id} already registered, updating")
            
            # Check dependencies if specified
            if tool.requires_dependencies:
                missing = self._check_dependencies(tool.requires_dependencies)
                if missing:
                    logger.warning(
                        f"Tool {tool.id} missing dependencies: {missing}"
                    )
                    tool.enabled = False
            
            # Register tool
            self._registry[tool.id] = tool
            
            # Update category index
            if tool.id not in self._category_index[tool.category]:
                self._category_index[tool.category].append(tool.id)
            
            # Audit log
            audit_log(
                "TOOL_REGISTERED",
                tool_id=tool.id,
                category=tool.category.value,
                enabled=tool.enabled
            )
            
            logger.info(f"Registered tool: {tool.id} ({tool.name})")
            return True
            
        except Exception as e:
            log_error(
                f"Failed to register tool {tool.id}",
                exc_info=True,
                context={"tool_id": tool.id, "error": str(e)}
            )
            return False
    
    def register_lazy_tool(self, 
                          tool_id: str, 
                          loader: Callable[[], ToolMetadata]) -> bool:
        """
        Register a tool with lazy loading.
        
        Tool metadata is loaded only when first accessed, improving startup time.
        
        Args:
            tool_id: Unique tool identifier
            loader: Function that returns ToolMetadata when called
        
        Returns:
            True if registration successful
        
        Example:
            def load_wifi_tool():
                return ToolMetadata(id="wifi_scan", ...)
            
            manager.register_lazy_tool("wifi_scan", load_wifi_tool)
        """
        if not callable(loader):
            logger.error(f"Lazy loader for {tool_id} is not callable")
            return False
        
        self._lazy_loaders[tool_id] = loader
        logger.debug(f"Registered lazy loader for tool: {tool_id}")
        return True
    
    def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool from the manager.
        
        Args:
            tool_id: ID of tool to unregister
        
        Returns:
            True if unregistration successful
        """
        if tool_id not in self._registry:
            logger.warning(f"Tool {tool_id} not registered")
            return False
        
        tool = self._registry[tool_id]
        
        # Remove from category index
        if tool_id in self._category_index[tool.category]:
            self._category_index[tool.category].remove(tool_id)
        
        # Remove from registry
        del self._registry[tool_id]
        
        # Remove from active tools if present
        self._active_tools.discard(tool_id)
        
        audit_log("TOOL_UNREGISTERED", tool_id=tool_id)
        logger.info(f"Unregistered tool: {tool_id}")
        return True
    
    def get_tool(self, tool_id: str) -> Optional[ToolMetadata]:
        """
        Get tool metadata by ID.
        
        Args:
            tool_id: Tool identifier
        
        Returns:
            ToolMetadata if found, None otherwise
        
        Example:
            tool = manager.get_tool("wifi_scan")
            if tool:
                print(tool.name)
        """
        # Check if tool is already loaded
        if tool_id in self._registry:
            return self._registry[tool_id]
        
        # Check if tool has lazy loader
        if tool_id in self._lazy_loaders:
            try:
                tool = self._lazy_loaders[tool_id]()
                self.register_tool(tool)
                del self._lazy_loaders[tool_id]  # Remove loader after loading
                return tool
            except Exception as e:
                log_error(
                    f"Failed to load lazy tool {tool_id}",
                    exc_info=True,
                    context={"tool_id": tool_id}
                )
                return None
        
        return None
    
    def get_all_tools(self) -> List[ToolMetadata]:
        """
        Get all registered tools.
        
        Returns:
            List of all ToolMetadata instances
        
        Example:
            tools = manager.get_all_tools()
            for tool in tools:
                print(f"{tool.icon} {tool.name}")
        """
        # Load any lazy tools
        for tool_id in list(self._lazy_loaders.keys()):
            self.get_tool(tool_id)
        
        return list(self._registry.values())
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """
        Get all tools in a specific category.
        
        Args:
            category: ToolCategory enum value
        
        Returns:
            List of ToolMetadata instances in the category
        
        Example:
            wifi_tools = manager.get_tools_by_category(ToolCategory.WIFI)
        """
        tool_ids = self._category_index.get(category, [])
        tools = []
        
        for tool_id in tool_ids:
            tool = self.get_tool(tool_id)
            if tool:
                tools.append(tool)
        
        return tools
    
    def get_enabled_tools(self) -> List[ToolMetadata]:
        """
        Get all enabled tools.
        
        Returns:
            List of enabled ToolMetadata instances
        """
        return [tool for tool in self.get_all_tools() if tool.enabled]
    
    def get_categories(self) -> List[ToolCategory]:
        """
        Get all categories that have registered tools.
        
        Returns:
            List of ToolCategory values with at least one tool
        """
        return [
            category for category, tools in self._category_index.items()
            if len(tools) > 0
        ]
    
    @error_boundary(fallback_value=None, log_traceback=True)
    def execute_tool(self, tool_id: str, **kwargs: Any) -> Any:
        """
        Execute a registered tool.
        
        Args:
            tool_id: ID of tool to execute
            **kwargs: Additional arguments to pass to tool callback
        
        Returns:
            Tool execution result, or None if execution failed
        
        Example:
            result = manager.execute_tool("wifi_scan", interface="wlan0")
        """
        import time
        
        tool = self.get_tool(tool_id)
        if not tool:
            logger.error(f"Tool {tool_id} not found")
            return None
        
        if not tool.enabled:
            logger.warning(f"Tool {tool_id} is disabled")
            return None
        
        # Create execution context
        context = ToolExecutionContext(
            tool_id=tool_id,
            status=ToolStatus.RUNNING,
            start_time=time.time()
        )
        self._execution_contexts[tool_id] = context
        self._active_tools.add(tool_id)
        
        # Audit log
        audit_log("TOOL_EXECUTE_START", tool_id=tool_id)
        
        try:
            logger.info(f"Executing tool: {tool_id}")
            
            # Execute callback
            if inspect.signature(tool.callback).parameters:
                result = tool.callback(**kwargs)
            else:
                result = tool.callback()
            
            # Update context
            context.status = ToolStatus.COMPLETED
            context.result = result
            context.end_time = time.time()
            
            # Audit log
            audit_log(
                "TOOL_EXECUTE_SUCCESS",
                tool_id=tool_id,
                duration_ms=(context.end_time - context.start_time) * 1000
            )
            
            logger.info(f"Tool {tool_id} completed successfully")
            return result
            
        except Exception as e:
            # Update context
            context.status = ToolStatus.FAILED
            context.error = str(e)
            context.end_time = time.time()
            
            # Log error
            log_error(
                f"Tool {tool_id} execution failed",
                exc_info=True,
                context={"tool_id": tool_id, "error": str(e)}
            )
            
            # Audit log
            audit_log(
                "TOOL_EXECUTE_FAILURE",
                tool_id=tool_id,
                error=str(e)
            )
            
            return None
            
        finally:
            self._active_tools.discard(tool_id)
    
    def get_execution_context(self, tool_id: str) -> Optional[ToolExecutionContext]:
        """
        Get execution context for a tool.
        
        Args:
            tool_id: Tool identifier
        
        Returns:
            ToolExecutionContext if available, None otherwise
        """
        return self._execution_contexts.get(tool_id)
    
    def is_tool_active(self, tool_id: str) -> bool:
        """
        Check if a tool is currently executing.
        
        Args:
            tool_id: Tool identifier
        
        Returns:
            True if tool is running, False otherwise
        """
        return tool_id in self._active_tools
    
    def enable_tool(self, tool_id: str) -> bool:
        """
        Enable a disabled tool.
        
        Args:
            tool_id: Tool identifier
        
        Returns:
            True if successful
        """
        tool = self.get_tool(tool_id)
        if not tool:
            return False
        
        tool.enabled = True
        audit_log("TOOL_ENABLED", tool_id=tool_id)
        logger.info(f"Enabled tool: {tool_id}")
        return True
    
    def disable_tool(self, tool_id: str) -> bool:
        """
        Disable a tool.
        
        Args:
            tool_id: Tool identifier
        
        Returns:
            True if successful
        """
        tool = self.get_tool(tool_id)
        if not tool:
            return False
        
        tool.enabled = False
        audit_log("TOOL_DISABLED", tool_id=tool_id)
        logger.info(f"Disabled tool: {tool_id}")
        return True
    
    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """
        Check if system has required dependencies.
        
        Args:
            dependencies: List of command names to check
        
        Returns:
            List of missing dependencies
        """
        import shutil
        
        missing = []
        for dep in dependencies:
            if not shutil.which(dep):
                missing.append(dep)
        
        return missing
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get tool manager statistics.
        
        Returns:
            Dictionary with statistics
        
        Example:
            stats = manager.get_statistics()
            print(f"Total tools: {stats['total_tools']}")
        """
        return {
            'total_tools': len(self._registry),
            'enabled_tools': len(self.get_enabled_tools()),
            'active_tools': len(self._active_tools),
            'categories': len(self.get_categories()),
            'lazy_loaders': len(self._lazy_loaders),
            'tools_by_category': {
                cat.value: len(tools)
                for cat, tools in self._category_index.items()
                if len(tools) > 0
            }
        }


# Convenience function for getting manager instance
def get_tool_manager() -> ToolManager:
    """
    Get the singleton ToolManager instance.
    
    Returns:
        ToolManager instance
    
    Example:
        from ui.tool_manager import get_tool_manager
        manager = get_tool_manager()
    """
    return ToolManager.get_instance()

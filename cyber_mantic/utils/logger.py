"""
日志系统 - 基于loguru的结构化日志

安全特性：
- 敏感数据自动脱敏（API密钥、个人信息等）
- 支持多级别日志输出
- 性能监控和告警
"""
import sys
import re
from pathlib import Path
from typing import Optional, Dict, Any, Union
from loguru import logger
from datetime import datetime


# 敏感数据关键字列表
SENSITIVE_KEYS = {
    'api_key', 'apikey', 'api-key',
    'claude_api_key', 'gemini_api_key', 'deepseek_api_key', 'kimi_api_key',
    'token', 'access_token', 'refresh_token',
    'password', 'passwd', 'secret',
    'birth_date', 'birth_year', 'birth_month', 'birth_day',
    'ssn', 'id_number', 'phone', 'email',
    'authorization', 'auth'
}

# API密钥正则模式
API_KEY_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',  # Anthropic/OpenAI style
    r'AIza[a-zA-Z0-9_-]{35}',  # Google API key
    r'[a-f0-9]{32,64}',  # Generic hex keys
]


def mask_sensitive_data(data: Any, depth: int = 0) -> Any:
    """
    递归脱敏敏感数据

    Args:
        data: 要脱敏的数据（支持dict, list, str等）
        depth: 递归深度（防止无限递归）

    Returns:
        脱敏后的数据
    """
    if depth > 10:  # 防止无限递归
        return data

    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_lower = key.lower().replace('-', '_')
            if key_lower in SENSITIVE_KEYS:
                masked[key] = '***MASKED***'
            else:
                masked[key] = mask_sensitive_data(value, depth + 1)
        return masked

    elif isinstance(data, (list, tuple)):
        return [mask_sensitive_data(item, depth + 1) for item in data]

    elif isinstance(data, str):
        # 脱敏字符串中的API密钥模式
        result = data
        for pattern in API_KEY_PATTERNS:
            result = re.sub(pattern, '***MASKED***', result)
        return result

    else:
        return data


def mask_log_message(message: str) -> str:
    """
    脱敏日志消息中的敏感信息

    Args:
        message: 原始日志消息

    Returns:
        脱敏后的消息
    """
    result = message
    for pattern in API_KEY_PATTERNS:
        result = re.sub(pattern, '***MASKED***', result)
    return result


class LoggerManager:
    """日志管理器"""

    def __init__(self):
        self._initialized = False
        self._log_dir = None

    def setup_logger(
        self,
        level: str = "INFO",
        log_to_file: bool = True,
        log_dir: str = "logs",
        max_file_size: str = "10MB",
        backup_count: int = 5,
        log_calculations: bool = True
    ):
        """
        设置日志系统

        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: 是否输出到文件
            log_dir: 日志目录
            max_file_size: 单个日志文件最大大小
            backup_count: 保留的日志文件数量
            log_calculations: 是否记录计算过程
        """
        if self._initialized:
            logger.warning("日志系统已初始化，跳过重复初始化")
            return

        # 移除默认handler
        logger.remove()

        # 控制台输出配置
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        # 添加控制台输出
        logger.add(
            sys.stderr,
            format=console_format,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )

        # 文件输出配置
        if log_to_file:
            self._log_dir = Path(log_dir)
            self._log_dir.mkdir(parents=True, exist_ok=True)

            # 详细日志格式
            file_format = (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            )

            # 主日志文件（所有级别）
            logger.add(
                self._log_dir / "cyber_mantic_{time:YYYY-MM-DD}.log",
                format=file_format,
                level=level,
                rotation=max_file_size,
                retention=f"{backup_count} days",
                compression="zip",
                encoding="utf-8",
                backtrace=True,
                diagnose=True
            )

            # 错误日志文件（仅ERROR及以上）
            logger.add(
                self._log_dir / "error_{time:YYYY-MM-DD}.log",
                format=file_format,
                level="ERROR",
                rotation=max_file_size,
                retention=f"{backup_count * 2} days",  # 错误日志保留更久
                compression="zip",
                encoding="utf-8",
                backtrace=True,
                diagnose=True
            )

            # 计算日志文件（如果启用）
            if log_calculations:
                logger.add(
                    self._log_dir / "calculations_{time:YYYY-MM-DD}.log",
                    format=file_format,
                    level="DEBUG",
                    rotation=max_file_size,
                    retention=f"{backup_count} days",
                    compression="zip",
                    encoding="utf-8",
                    filter=lambda record: "calculation" in record["extra"]
                )

        self._initialized = True
        logger.info("日志系统初始化完成")
        logger.debug(f"日志级别: {level}")
        if log_to_file:
            logger.debug(f"日志目录: {self._log_dir}")

    def log_calculation(
        self,
        theory_name: str,
        calculation_type: str,
        input_data: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        记录计算过程

        Args:
            theory_name: 理论名称
            calculation_type: 计算类型
            input_data: 输入数据
            result: 计算结果
            error: 错误信息
        """
        log_data = {
            "theory": theory_name,
            "type": calculation_type,
            "input": input_data,
            "timestamp": datetime.now().isoformat()
        }

        if result:
            log_data["result"] = result
            logger.bind(calculation=True).debug(
                f"[计算] {theory_name} - {calculation_type}: 成功",
                **log_data
            )
        elif error:
            log_data["error"] = error
            logger.bind(calculation=True).error(
                f"[计算] {theory_name} - {calculation_type}: 失败 - {error}",
                **log_data
            )

    def log_api_call(
        self,
        api_name: str,
        endpoint: str,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None
    ):
        """
        记录API调用（自动脱敏敏感信息）

        Args:
            api_name: API名称
            endpoint: 端点
            request_data: 请求数据
            response_data: 响应数据
            error: 错误信息
            duration: 耗时（秒）
        """
        log_data = {
            "api": api_name,
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat()
        }

        if duration:
            log_data["duration"] = f"{duration:.2f}s"

        # 脱敏请求和响应数据
        if request_data:
            log_data["request"] = mask_sensitive_data(request_data)

        if response_data:
            log_data["response"] = mask_sensitive_data(response_data)
            logger.info(
                f"[API] {api_name} - {endpoint}: 成功 ({log_data.get('duration', 'N/A')})",
                **log_data
            )
        elif error:
            log_data["error"] = mask_log_message(str(error))
            logger.error(
                f"[API] {api_name} - {endpoint}: 失败 - {mask_log_message(str(error))}",
                **log_data
            )

    def log_user_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录用户操作（自动脱敏敏感信息）

        Args:
            action: 操作类型
            user_id: 用户ID
            details: 详细信息
        """
        log_data = {
            "action": action,
            "timestamp": datetime.now().isoformat()
        }

        if user_id:
            log_data["user_id"] = user_id

        # 脱敏详细信息
        if details:
            log_data["details"] = mask_sensitive_data(details)

        logger.info(f"[用户操作] {action}", **log_data)

    def log_conflict_resolution(
        self,
        conflicts: list,
        resolution: Dict[str, Any]
    ):
        """
        记录冲突解决过程

        Args:
            conflicts: 冲突列表
            resolution: 解决方案
        """
        log_data = {
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "resolution": resolution,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(
            f"[冲突解决] 检测到{len(conflicts)}个冲突，策略: {resolution.get('总体策略', 'N/A')}",
            **log_data
        )

    def log_performance(
        self,
        operation: str,
        duration: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录性能指标

        Args:
            operation: 操作名称
            duration: 耗时（秒）
            details: 详细信息
        """
        log_data = {
            "operation": operation,
            "duration": f"{duration:.3f}s",
            "timestamp": datetime.now().isoformat()
        }

        if details:
            log_data["details"] = details

        # 根据耗时选择日志级别
        if duration > 10:
            logger.warning(f"[性能] {operation} 耗时较长: {duration:.2f}s", **log_data)
        elif duration > 5:
            logger.info(f"[性能] {operation}: {duration:.2f}s", **log_data)
        else:
            logger.debug(f"[性能] {operation}: {duration:.2f}s", **log_data)

    def get_log_files(self) -> list:
        """
        获取日志文件列表

        Returns:
            日志文件路径列表
        """
        if not self._log_dir or not self._log_dir.exists():
            return []

        return sorted(self._log_dir.glob("*.log"), reverse=True)

    def get_latest_errors(self, count: int = 10) -> list:
        """
        获取最新的错误日志

        Args:
            count: 返回的错误数量

        Returns:
            错误日志列表
        """
        if not self._log_dir:
            return []

        error_files = sorted(self._log_dir.glob("error_*.log"), reverse=True)
        if not error_files:
            return []

        errors = []
        for error_file in error_files:
            try:
                with open(error_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    errors.extend(lines[-count:])
                    if len(errors) >= count:
                        break
            except Exception as e:
                logger.error(f"读取错误日志失败: {e}")

        return errors[:count]


# 全局日志管理器实例
_logger_manager = LoggerManager()


def setup_logger(**kwargs):
    """
    设置日志系统（便捷函数）

    Args:
        **kwargs: 传递给LoggerManager.setup_logger的参数
    """
    _logger_manager.setup_logger(**kwargs)


def get_logger(name: Optional[str] = None):
    """
    获取logger实例

    Args:
        name: 可选的logger名称（兼容参数，loguru会自动记录模块信息）

    Returns:
        logger实例
    """
    if name:
        # 使用bind绑定额外的上下文信息
        return logger.bind(module=name)
    return logger


def log_calculation(**kwargs):
    """记录计算过程（便捷函数）"""
    _logger_manager.log_calculation(**kwargs)


def log_api_call(**kwargs):
    """记录API调用（便捷函数）"""
    _logger_manager.log_api_call(**kwargs)


def log_user_action(**kwargs):
    """记录用户操作（便捷函数）"""
    _logger_manager.log_user_action(**kwargs)


def log_conflict_resolution(**kwargs):
    """记录冲突解决（便捷函数）"""
    _logger_manager.log_conflict_resolution(**kwargs)


def log_performance(**kwargs):
    """记录性能指标（便捷函数）"""
    _logger_manager.log_performance(**kwargs)


# 装饰器：自动记录函数执行时间
def log_execution_time(operation_name: Optional[str] = None):
    """
    装饰器：记录函数执行时间

    Args:
        operation_name: 操作名称（默认使用函数名）
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance(
                    operation=operation_name or func.__name__,
                    duration=duration
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"函数 {func.__name__} 执行失败（耗时{duration:.2f}s）: {e}"
                )
                raise
        return wrapper
    return decorator

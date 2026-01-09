"""
自定义异常类体系

提供项目特定的异常类型，便于精确的错误处理和调试。
"""
from typing import Optional


class CyberManticError(Exception):
    """赛博玄数基础异常类"""
    pass


class TheoryCalculationError(CyberManticError):
    """理论计算错误

    当术数理论计算失败时抛出（如八字、紫微排盘错误）
    """
    def __init__(self, theory_name: str, message: str):
        self.theory_name = theory_name
        self.message = message
        super().__init__(f"{theory_name} 计算失败: {message}")


class APIError(CyberManticError):
    """API调用错误

    当调用外部API（Claude/Gemini/Deepseek/Kimi）失败时抛出
    """
    def __init__(self, api_name: str, message: str, status_code: Optional[int] = None):
        self.api_name = api_name
        self.message = message
        self.status_code = status_code
        super().__init__(f"{api_name} API错误: {message}")


class APITimeoutError(APIError):
    """API超时错误"""
    def __init__(self, api_name: str, timeout: float):
        self.timeout = timeout
        super().__init__(api_name, f"请求超时（{timeout}秒）")


class APIRateLimitError(APIError):
    """API限流错误"""
    def __init__(self, api_name: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        message = "请求过于频繁"
        if retry_after:
            message += f"，请在{retry_after}秒后重试"
        super().__init__(api_name, message, status_code=429)


class ValidationError(CyberManticError):
    """输入验证错误

    当用户输入不符合要求时抛出
    """
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"验证失败 [{field}]: {message}")


class DataParsingError(CyberManticError):
    """数据解析错误

    当解析用户输入、API响应等数据失败时抛出
    """
    def __init__(self, data_type: str, message: str):
        self.data_type = data_type
        self.message = message
        super().__init__(f"{data_type} 解析失败: {message}")


class ConflictResolutionError(CyberManticError):
    """冲突解决错误

    当多理论结果冲突无法解决时抛出
    """
    def __init__(self, theories: list, message: str):
        self.theories = theories
        self.message = message
        super().__init__(f"冲突解决失败 [{', '.join(theories)}]: {message}")


class ConfigurationError(CyberManticError):
    """配置错误

    当配置文件缺失、格式错误或值无效时抛出
    """
    def __init__(self, config_key: str, message: str):
        self.config_key = config_key
        self.message = message
        super().__init__(f"配置错误 [{config_key}]: {message}")


class ResourceNotFoundError(CyberManticError):
    """资源未找到错误

    当请求的资源（文件、模板、数据）不存在时抛出
    """
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} 未找到: {resource_id}")

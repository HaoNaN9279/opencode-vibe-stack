"""vibe-stack — 管理项目中AI智能体特定领域的工具链配置。"""

__version__ = "0.1.0"


class VibeStackError(Exception):
    """所有 vibe-stack 自定义异常的基类。"""


class RegistryError(VibeStackError):
    """注册表缺失或格式错误时抛出。"""


class DomainNotFoundError(VibeStackError):
    """领域不存在时抛出。"""

"""
API Key加密存储

使用Fernet对称加密保护API密钥

设计参考：docs/design/07_AI接口设计.md
"""
import os
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception


class APIKeyManager:
    """
    API Key加密管理器

    使用Fernet对称加密保护API密钥
    密钥文件存储在 ~/.cyber_mantic/.keyfile
    """

    def __init__(self, key_path: Optional[str] = None):
        """
        初始化API Key管理器

        Args:
            key_path: 密钥文件路径，默认 ~/.cyber_mantic/.keyfile
        """
        self.logger = get_logger(__name__)

        if key_path is None:
            app_dir = Path.home() / ".cyber_mantic"
            app_dir.mkdir(exist_ok=True)
            key_path = str(app_dir / ".keyfile")

        self._key_path = key_path
        self._cipher = None

        if CRYPTO_AVAILABLE:
            self._init_cipher()
        else:
            self.logger.warning("cryptography库未安装，API Key将以明文存储")

    def _init_cipher(self):
        """初始化加密器"""
        try:
            key = self._get_or_create_key()
            self._cipher = Fernet(key)
        except Exception as e:
            self.logger.error(f"初始化加密器失败: {e}")
            self._cipher = None

    def _get_or_create_key(self) -> bytes:
        """获取或创建加密密钥"""
        key_path = Path(self._key_path)

        if key_path.exists():
            with open(key_path, "rb") as f:
                return f.read()
        else:
            # 生成新密钥
            key = Fernet.generate_key()

            # 确保目录存在
            key_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入密钥文件
            with open(key_path, "wb") as f:
                f.write(key)

            # 设置权限（仅所有者可读写）
            try:
                os.chmod(key_path, 0o600)
            except Exception as e:
                self.logger.warning(f"设置密钥文件权限失败: {e}")

            self.logger.info(f"已创建新的加密密钥: {key_path}")
            return key

    def encrypt(self, api_key: str) -> str:
        """
        加密API Key

        Args:
            api_key: 原始API Key

        Returns:
            加密后的字符串（Base64编码）
        """
        if not api_key:
            return ""

        if self._cipher is None:
            # 加密不可用，返回原文（警告已在初始化时输出）
            return api_key

        try:
            encrypted = self._cipher.encrypt(api_key.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as e:
            self.logger.error(f"加密API Key失败: {e}")
            return api_key

    def decrypt(self, encrypted_key: str) -> str:
        """
        解密API Key

        Args:
            encrypted_key: 加密的API Key

        Returns:
            原始API Key
        """
        if not encrypted_key:
            return ""

        if self._cipher is None:
            # 加密不可用，假设是明文
            return encrypted_key

        try:
            decrypted = self._cipher.decrypt(encrypted_key.encode("utf-8"))
            return decrypted.decode("utf-8")
        except InvalidToken:
            # 可能是明文存储的旧数据
            self.logger.warning("解密失败，可能是明文存储的旧数据")
            return encrypted_key
        except Exception as e:
            self.logger.error(f"解密API Key失败: {e}")
            return encrypted_key

    def is_encrypted(self, value: str) -> bool:
        """
        检查值是否已加密

        Args:
            value: 要检查的值

        Returns:
            是否已加密
        """
        if not value or self._cipher is None:
            return False

        try:
            # 尝试解密，如果成功则是加密的
            self._cipher.decrypt(value.encode("utf-8"))
            return True
        except Exception:
            return False

    def rotate_key(self) -> bool:
        """
        轮换加密密钥

        Returns:
            是否成功
        """
        if not CRYPTO_AVAILABLE:
            return False

        try:
            # 生成新密钥
            new_key = Fernet.generate_key()
            new_cipher = Fernet(new_key)

            # 备份旧密钥
            old_key_path = Path(self._key_path)
            backup_path = old_key_path.with_suffix(".keyfile.bak")
            if old_key_path.exists():
                old_key_path.rename(backup_path)

            # 写入新密钥
            with open(self._key_path, "wb") as f:
                f.write(new_key)
            os.chmod(self._key_path, 0o600)

            # 更新cipher
            self._cipher = new_cipher

            self.logger.info("密钥轮换成功")
            return True

        except Exception as e:
            self.logger.error(f"密钥轮换失败: {e}")
            # 恢复备份
            backup_path = Path(self._key_path).with_suffix(".keyfile.bak")
            if backup_path.exists():
                backup_path.rename(self._key_path)
            return False


# 全局单例
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """获取全局APIKeyManager实例"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def encrypt_api_key(api_key: str) -> str:
    """便捷函数：加密API Key"""
    return get_api_key_manager().encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """便捷函数：解密API Key"""
    return get_api_key_manager().decrypt(encrypted_key)

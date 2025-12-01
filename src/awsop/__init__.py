"""awsop - 1Password連携によるAWS認証情報管理ツール"""

from importlib.metadata import version, PackageNotFoundError

from awsop.logging import setup_logging

try:
    __version__ = version("awsop")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["setup_logging", "__version__"]

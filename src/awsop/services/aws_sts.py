"""AWS STS APIとの統合"""

from typing import Optional
from datetime import datetime


class STSClient:
    """AWS STSクライアント"""

    def assume_role(
        self,
        role_arn: str,
        role_session_name: str,
        duration_seconds: int = 3600,
        external_id: Optional[str] = None,
    ) -> dict:
        """AssumeRoleを実行"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()

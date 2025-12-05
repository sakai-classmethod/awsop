"""コンソール起動管理"""

import logging
import webbrowser
from typing import Optional

from awsop.app.credentials_manager import Credentials
from awsop.services.console_service import ConsoleService

logger = logging.getLogger(__name__)


class ConsoleManager:
    """コンソール起動管理クラス"""

    def __init__(
        self,
        console_service: Optional[ConsoleService] = None,
    ):
        """
        コンソールマネージャーを初期化

        Args:
            console_service: コンソールサービス（テスト用）
        """
        self.console_service = console_service or ConsoleService()

    def open_console(
        self,
        credentials: Credentials,
        service: str = "console",
        open_browser: bool = True,
    ) -> str:
        """
        AWSコンソールを開く

        Args:
            credentials: AWS認証情報
            service: サービス名（デフォルト: "console"）
            open_browser: ブラウザを開くかどうか

        Returns:
            str: 生成されたコンソールURL

        Raises:
            RuntimeError: URL生成またはブラウザ起動に失敗した場合
        """
        logger.info(
            f"コンソールを開きます: service={service}, region={credentials.region}"
        )

        try:
            # Amazonドメインを取得
            amazon_domain = self.console_service.get_amazon_domain(credentials.region)
            logger.debug(f"Amazonドメイン: {amazon_domain}")

            # サインイントークンを取得
            signin_token = self.console_service.get_signin_token(
                access_key_id=credentials.access_key_id,
                secret_access_key=credentials.secret_access_key,
                session_token=credentials.session_token,
                amazon_domain=amazon_domain,
            )

            # デスティネーションURLを構築
            destination_url = self.console_service.build_destination_url(
                service=service,
                region=credentials.region,
                amazon_domain=amazon_domain,
            )
            logger.debug(f"デスティネーションURL: {destination_url}")

            # コンソールURLを生成
            console_url = self.console_service.generate_console_url(
                signin_token=signin_token,
                destination_url=destination_url,
                amazon_domain=amazon_domain,
            )

            # ブラウザを開く
            if open_browser:
                logger.info("ブラウザを起動します...")
                try:
                    webbrowser.open(console_url)
                    logger.info("ブラウザの起動に成功しました")
                except Exception as e:
                    # ブラウザ起動に失敗した場合でもURLは返す
                    logger.error(f"ブラウザの起動に失敗しました: {str(e)}")
                    raise RuntimeError(
                        f"ブラウザの起動に失敗しました: {str(e)}\n"
                        f"以下のURLを手動で開いてください:\n{console_url}"
                    ) from e

            return console_url

        except RuntimeError:
            # ConsoleServiceからのRuntimeErrorはそのまま再送出
            raise
        except Exception as e:
            logger.error(f"コンソールURLの生成に失敗しました: {str(e)}")
            raise RuntimeError(f"コンソールURLの生成に失敗しました: {str(e)}") from e

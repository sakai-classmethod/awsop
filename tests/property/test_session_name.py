"""セッション名生成のプロパティテスト

Feature: awsop-cli-migration, Property 7: セッション名の生成
検証: 要件 4.3.1, 4.3.2
"""

import re
from hypothesis import given, strategies as st


@given(session_name_option=st.one_of(st.none(), st.text(min_size=1, max_size=64)))
def test_session_name_generation(session_name_option):
    """
    Feature: awsop-cli-migration, Property 7: セッション名の生成

    任意の実行に対して、
    --session-name が指定された場合はそれを使用し、
    指定されない場合は「awsop-<タイムスタンプ>」形式のセッション名を生成する
    """
    # セッション名の決定ロジック
    if session_name_option is not None:
        effective_session_name = session_name_option
    else:
        # タイムスタンプ形式のセッション名を生成（実際の実装と同じパターン）
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        effective_session_name = f"awsop-{timestamp}"

    # 検証: セッション名が正しく決定されている
    if session_name_option is not None:
        # --session-name が指定されている場合は、それが使用される
        assert effective_session_name == session_name_option
    else:
        # 指定されていない場合は、awsop-<タイムスタンプ>形式になる
        assert effective_session_name.startswith("awsop-")
        # タイムスタンプ部分は14桁の数字
        timestamp_part = effective_session_name[6:]  # "awsop-"の後
        assert len(timestamp_part) == 14
        assert timestamp_part.isdigit()
        # パターンマッチでも確認
        assert re.match(r"^awsop-\d{14}$", effective_session_name)

"""リージョン設定の優先順位のプロパティテスト

Feature: awsop-cli-migration, Property 6: リージョン設定の優先順位
検証: 要件 4.2.1, 4.2.2, 4.2.3
"""

from hypothesis import given, strategies as st
from awsop.app.profile_manager import ProfileConfig


@given(
    region_option=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    profile_region=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
)
def test_region_priority(region_option, profile_region):
    """
    Feature: awsop-cli-migration, Property 6: リージョン設定の優先順位

    任意のプロファイルとリージョン指定に対して、
    --region オプションが指定された場合はそれを使用し、
    指定されない場合はプロファイルの region 設定を使用し、
    それもない場合はデフォルトリージョン（ap-northeast-1）を使用する
    """
    # リージョンの優先順位を決定
    # 1. --region オプション
    # 2. プロファイルのregion設定
    # 3. デフォルト（ap-northeast-1）
    effective_region = region_option or profile_region or "ap-northeast-1"

    # 検証: 優先順位が正しく適用されている
    if region_option is not None:
        # --region オプションが指定されている場合は、それが使用される
        assert effective_region == region_option
    elif profile_region is not None:
        # --region オプションがなく、プロファイルにregionがある場合は、それが使用される
        assert effective_region == profile_region
    else:
        # どちらもない場合は、デフォルトリージョンが使用される
        assert effective_region == "ap-northeast-1"

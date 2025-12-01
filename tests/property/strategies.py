"""Hypothesisストラテジー定義"""

from hypothesis import strategies as st
from datetime import datetime, timedelta


# 基本的なストラテジー
# ハイフンで始まるプロファイル名はCLIオプションと解釈されるため除外
profile_names = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
    ),
    min_size=1,
    max_size=50,
).filter(lambda x: not x.startswith("-"))

role_arns = st.builds(
    lambda account, role: f"arn:aws:iam::{account}:role/{role}",
    account=st.integers(min_value=100000000000, max_value=999999999999),
    role=st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
        ),
        min_size=1,
        max_size=50,
    ),
)

regions = st.sampled_from(
    [
        "us-east-1",
        "us-west-2",
        "eu-west-1",
        "ap-northeast-1",
        "ap-southeast-1",
        "ap-southeast-2",
    ]
)

session_names = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
    ),
    min_size=1,
    max_size=64,
)

role_durations = st.integers(min_value=900, max_value=43200)

access_keys = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Nd")), min_size=20, max_size=20
)

secret_keys = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="+/"
    ),
    min_size=40,
    max_size=40,
)

# ConfigParserは改行文字を値に含めることができないため、除外する
# また、サロゲート文字も除外する（UTF-8エンコードできないため）
session_tokens = st.text(
    alphabet=st.characters(
        blacklist_characters="\r\n",
        blacklist_categories=("Cs",),  # サロゲート文字を除外
    ),
    min_size=100,
    max_size=500,
)

expirations = st.datetimes(
    min_value=datetime.now(), max_value=datetime.now() + timedelta(hours=12)
)

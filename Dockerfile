FROM python:slim AS rye

# Pythonがpycファイルを書き込まないようにします。
ENV PYTHONDONTWRITEBYTECODE=1

# Pythonがstdoutとstderrをバッファリングしないようにします。これにより、
# バッファリングによりログが発生せずにアプリケーションがクラッシュする状況を避けることができます。
ENV PYTHONUNBUFFERED=1
RUN \
  --mount=type=cache,target=/var/lib/apt/lists \
  --mount=type=cache,target=/var/cache/apt/archives \
  apt-get update \
  && apt-get install -y --no-install-recommends build-essential curl git

ARG UID=10001
WORKDIR /workspace
ENV PYTHONPATH="/workspace:$PYTHONPATH"
ENV RYE_HOME="/workspace/.rye"
ENV PATH="${RYE_HOME}/shims:${PATH}"

# RYE_INSTALL_OPTIONはビルドに必要です。
# 参照: https://github.com/mitsuhiko/rye/issues/246
RUN curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash

# Dockerのキャッシュを利用するために、依存関係のダウンロードを別のステップとして行います。
# バインドマウントを利用して一部のファイルをこのレイヤーにコピーすることを避けます。
RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=requirements.lock,target=requirements.lock \
    --mount=type=bind,source=requirements-dev.lock,target=requirements-dev.lock \
    --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=README.md,target=README.md \
    rye sync --no-lock

RUN . .venv/bin/activate

FROM rye AS test

ENV IS_TESTING_ENVIRONMENT=1

COPY . .

RUN rye sync --no-lock 
# 自作のモジュールをインストールする。

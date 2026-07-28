# 検証用環境のため、apt/npm のバージョン固定は行わない
# hadolint global ignore=DL3008,DL3016
FROM python:3.15-rc-slim

# パイプを含む RUN で失敗を確実に検知するため pipefail を有効化 (hadolint DL4006)
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /ssg

# 必要なパッケージのインストール
# - curl: NodeSource / uv のインストールスクリプト取得用
# - ca-certificates: HTTPS 通信用
# - git: Claude Code / 開発用
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  ca-certificates \
  git \
  && rm -rf /var/lib/apt/lists/*

# Node.js 24.x (Claude Code 用)
# debian 標準の nodejs は古いため NodeSource から導入
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
  && apt-get install -y --no-install-recommends nodejs \
  && rm -rf /var/lib/apt/lists/*

# Claude Code のインストール
RUN npm install -g @anthropic-ai/claude-code

# uv のインストール (公式インストーラ)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# zensical ラッパーの配置。
# `zensical serve` / `zensical build` の前に docs/sitemap.md から nav を自動再生成する
# ため、本物の zensical (.venv/bin) より PATH 前方の /usr/local/bin にラッパーを置く。
# 呼び出し側（執筆者・CI・DevContainer）はコマンドを変えず `zensical ...` のままでよい。
# scripts/ はバインドマウントで /ssg/scripts に来る想定だが、ラッパー自体はイメージに
# 焼いておくことで PATH 解決を安定させる。
COPY scripts/zensical /usr/local/bin/zensical
RUN chmod +x /usr/local/bin/zensical

ENV SHELL=/bin/bash

# ベースイメージのENTRYPOINTを上書き
ENTRYPOINT []

# bashを起動（tty: trueがあれば起動し続ける）
CMD ["/bin/bash"]

# -------------------------------------------------------------
# 1. ベースイメージ: Python 3.11 Slim
# -------------------------------------------------------------
FROM python:3.12-slim-bookworm AS base

# タイムゾーン設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# -------------------------------------------------------------
# 2. ビルドステージ: 依存関係のインストール
# -------------------------------------------------------------
FROM base AS builder

# 必要なパッケージをインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre \
    wget \
    unzip \
    procps \
    gosu \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# GumTree のインストール
WORKDIR /opt
RUN wget "https://github.com/GumTreeDiff/gumtree/releases/download/v4.0.0-beta2/gumtree-4.0.0-beta2.zip" \
    && unzip "gumtree-4.0.0-beta2.zip" \
    && mv "gumtree-4.0.0-beta2" "gumtree" \
    && rm "gumtree-4.0.0-beta2.zip"

# requirements.txtのみを先にコピーしてキャッシュ活用
WORKDIR /work
COPY requirements.txt ./
COPY dist ./dist/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------
# 3. 実行ステージ: 最終イメージの作成
# -------------------------------------------------------------
FROM base

# 実行に必要なパッケージのみインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre \
    procps \
    gosu \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# セキュリティ: 非rootユーザーの作成
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# ビルドステージから必要なファイルをコピー
COPY --from=builder /opt/gumtree /opt/gumtree
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# エントリーポイントスクリプトのコピー
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 環境変数設定 - ビルド時に固定される設定
ENV PATH="/opt/gumtree/bin:$PATH"
ENV PYTHONPATH=/work/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリ設定
WORKDIR /work

# アプリケーションコードをコピー
COPY . /work/

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]

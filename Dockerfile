# -------------------------------------------------------------
# 1. ベースイメージ: Debian Bookworm Slim
# -------------------------------------------------------------
FROM debian:bookworm-slim

# -------------------------------------------------------------
# 2. 必要パッケージをインストール
#    - openjdk-17-jre: Java17 実行環境 (JRE)
#    - python3, python3-venv, python3-pip: Python3 + venv + Pip
#    - wget, unzip: GumTree ダウンロード・解凍
#    - bash: 対話シェル (必要に応じて)
# -------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre \
    python3 \
    python3-venv \
    python3-pip \
    wget \
    unzip \
    procps \
    bash \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------
# 3. GumTree のインストール
# -------------------------------------------------------------
WORKDIR /opt
RUN wget "https://github.com/GumTreeDiff/gumtree/releases/download/v4.0.0-beta2/gumtree-4.0.0-beta2.zip" \
    && unzip "gumtree-4.0.0-beta2.zip" \
    && mv "gumtree-4.0.0-beta2" "gumtree" \
    && rm "gumtree-4.0.0-beta2.zip"

# GumTree コマンド (gumtree, gtdiff) を PATH に追加
ENV PATH="$PATH:/opt/gumtree/bin"

# -------------------------------------------------------------
# 4. Python 仮想環境の作成
# -------------------------------------------------------------
# venv を /venv に作成しておき、そこを PATH に追加
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH=/work/src:$PYTHONPATH

# -------------------------------------------------------------
# 5. Python パッケージをインストール
#    - requirements.txt があるならコピーしてインストール
# -------------------------------------------------------------
WORKDIR /work
COPY requirements.txt /work/requirements.txt
COPY dist /work/dist

# 仮想環境上で pip install
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------
# 6. ソースコードをコピー（必要に応じて）
# -------------------------------------------------------------
COPY . /work/

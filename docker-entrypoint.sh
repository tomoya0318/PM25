#!/bin/bash
# docker-entrypoint.sh

# HOST_UIDとHOST_GIDが設定されている場合、ユーザーIDとグループIDを変更
if [ ! -z "${HOST_UID}" ] && [ ! -z "${HOST_GID}" ]; then
    echo "Setting user appuser to UID ${HOST_UID} and GID ${HOST_GID}"

    # グループIDを変更
    groupmod -o -g ${HOST_GID} appuser

    # ユーザーIDを変更
    usermod -o -u ${HOST_UID} appuser

    # /workディレクトリの所有権を変更
    chown -R appuser:appuser /work
fi

# 引数がない場合はbashを実行
if [ $# -eq 0 ]; then
    exec gosu appuser bash
else
    # 指定されたコマンドをappuserとして実行
    exec gosu appuser "$@"
fi

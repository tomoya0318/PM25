import os
import requests

from dotenv import load_dotenv


def send_discord_notification(message: str):
    """
    Discord Webhookを使ってメッセージを送信する関数。
    """
    # Webhook URLを設定
    load_dotenv()
    webhook_url = os.getenv("WEBHOOK_URL")
    user_id = os.getenv("DISCORD_USER_ID")

    if webhook_url and user_id:
        data = {
            "content": f" <@{user_id}> {message}",  # 送信するメッセージ
            "allowed_mentions": {
                "parse": ["users", "roles", "everyone"]  # メンションを許可する種類を指定
            }
        }

        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            print("Discord通知が成功しました！")
        else:
            print(f"通知失敗: {response.status_code} {response.text}")


if __name__ == "__main__":
    # 通知するメッセージ
    send_discord_notification(f"処理が完了しました！🎉")

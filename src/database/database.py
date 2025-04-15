# モデルのインポートは明示的にcreate_db_and_tables関数内で行い、循環参照を避ける
import os

from constants import path

from sqlmodel import Session, SQLModel, create_engine

# データベースのURLを設定
DATABASE_DIR = path.DATA/ "database"
DATABASE_FILE = DATABASE_DIR / "pm25.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# データベースディレクトリが存在しない場合は作成
os.makedirs(DATABASE_DIR, exist_ok=True)

# エンジンの作成
engine = create_engine(DATABASE_URL, echo=False)  # echo=Trueでデバッグ出力を有効化


def create_db_and_tables():
    """データベースとテーブルを作成する"""
    # モデルをここでインポートして循環参照を回避
    from database.models import BaseMetadata, File, TargetMetadata
    
    # テーブルを作成
    SQLModel.metadata.create_all(engine)


def get_session():
    """データベースのセッションを取得する"""
    with Session(engine) as session:
        yield session

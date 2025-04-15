# models.py
from datetime import datetime
from typing import Optional, List, ForwardRef

from sqlmodel import Field, Relationship, SQLModel

# ファイルデータモデル - テーブル名は「files」になります
class File(SQLModel, table=True):
    __tablename__ = "files"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    change_id: str = Field(index=True)
    branch: str
    file_name: str
    merged_at: datetime

    # リレーションシップは後で設定します
    base_metadata: Optional["BaseMetadata"] = Relationship(back_populates="file")
    target_metadata: Optional["TargetMetadata"] = Relationship(back_populates="file")


# 基本的なメタデータを定義する抽象クラス
class MetadataBase(SQLModel):
    hash: str
    committer: str
    subject: str
    commit_message: str
    file_path: str


# ベースメタデータモデル
class BaseMetadata(MetadataBase, table=True):
    __tablename__ = "base_metadata"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: Optional[int] = Field(default=None, foreign_key="files.id")
    file: Optional[File] = Relationship(back_populates="base_metadata")


# ターゲットメタデータモデル
class TargetMetadata(MetadataBase, table=True):
    __tablename__ = "target_metadata"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: Optional[int] = Field(default=None, foreign_key="files.id")
    file: Optional[File] = Relationship(back_populates="target_metadata")

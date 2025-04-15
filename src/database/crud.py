from typing import List, Optional, Sequence

from sqlmodel import Session, select

from database.models import BaseMetadata, File, TargetMetadata
from models.gerrit import FileData as GerritFileData


def create_file_data(db: Session, file_data: GerritFileData) -> File:
    """
    Gerritから取得したFileDataオブジェクトをデータベースに保存する
    """
    # GerritのFileDataからSQLModelのFileDataへ変換
    db_file_data = File(
        change_id=file_data.change_id,
        branch=file_data.branch,
        file_name=file_data.file_name,
        merged_at=file_data.merged_at
    )

    # Baseメタデータの作成
    db_base = BaseMetadata(
        hash=file_data.base.hash,
        committer=file_data.base.committer,
        subject=file_data.base.subject,
        commit_message=file_data.base.commit_message,
        file_path=file_data.base.file_path,
        file=db_file_data
    )

    # Targetメタデータの作成
    db_target = TargetMetadata(
        hash=file_data.target.hash,
        committer=file_data.target.committer,
        subject=file_data.target.subject,
        commit_message=file_data.target.commit_message,
        file_path=file_data.target.file_path,
        file=db_file_data
    )

    # データベースに保存
    db.add(db_file_data)
    db.add(db_base)
    db.add(db_target)
    db.commit()
    db.refresh(db_file_data)

    return db_file_data


def get_file_data_by_id(db: Session, file_data_id: int) -> Optional[File]:
    """指定されたIDのFileDataを取得する"""
    return db.get(File, file_data_id)


def get_file_data_by_change_id(db: Session, change_id: str) -> Sequence[File]:
    """指定されたchange_idを持つFileDataのリストを取得する"""
    statement = select(File).where(File.change_id == change_id)
    return db.exec(statement).all()


def get_all_file_data(db: Session, skip: int = 0, limit: int = 100) -> Sequence[File]:
    """すべてのFileDataをページング取得する"""
    statement = select(File).offset(skip).limit(limit)
    return db.exec(statement).all()


def update_file_data(db: Session, file_data_id: int, update_data: dict) -> Optional[File]:
    """指定されたIDのFileDataを更新する"""
    db_file_data = get_file_data_by_id(db, file_data_id)
    if not db_file_data:
        return None

    # 更新するフィールドを設定
    for key, value in update_data.items():
        if hasattr(db_file_data, key):
            setattr(db_file_data, key, value)

    db.add(db_file_data)
    db.commit()
    db.refresh(db_file_data)
    return db_file_data


def delete_file_data(db: Session, file_data_id: int) -> bool:
    """指定されたIDのFileDataを削除する"""
    db_file_data = get_file_data_by_id(db, file_data_id)
    if not db_file_data:
        return False

    db.delete(db_file_data)
    db.commit()
    return True

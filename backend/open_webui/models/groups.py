import json
import logging
import time
from typing import Optional
import uuid

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS

from open_webui.models.files import FileMetadataResponse


from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, JSON, func


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# UserGroup DB Schema
####################


class Group(Base):
    __tablename__ = "group"

    id = Column(Text, unique=True, primary_key=True)
    user_id = Column(Text)

    parent_id = Column(Text, nullable=True)

    name = Column(Text)
    description = Column(Text)

    data = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)

    permissions = Column(JSON, nullable=True)
    user_ids = Column(JSON, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class GroupModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str

    parent_id: Optional[str] = None

    name: str
    description: str

    data: Optional[dict] = None
    meta: Optional[dict] = None

    permissions: Optional[dict] = None
    user_ids: list[str] = []

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


####################
# Forms
####################


class GroupResponse(BaseModel):
    id: str
    user_id: str
    parent_id: Optional[str] = None
    name: str
    description: str
    permissions: Optional[dict] = None
    data: Optional[dict] = None
    meta: Optional[dict] = None
    user_ids: list[str] = []
    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


class GroupForm(BaseModel):
    name: str
    description: str
    permissions: Optional[dict] = None
    parent_id: Optional[str] = None


class GroupUpdateForm(GroupForm):
    user_ids: Optional[list[str]] = None


class GroupTable:
    def insert_new_group(
        self, user_id: str, form_data: GroupForm
    ) -> Optional[GroupModel]:
        with get_db() as db:
            group = GroupModel(
                **{
                    **form_data.model_dump(exclude_none=True),
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = Group(**group.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return GroupModel.model_validate(result)
                else:
                    return None

            except Exception:
                return None

    def get_groups(self) -> list[GroupModel]:
        with get_db() as db:
            return [
                GroupModel.model_validate(group)
                for group in db.query(Group).order_by(Group.updated_at.desc()).all()
            ]

    def get_groups_by_member_id(self, user_id: str) -> list[GroupModel]:
        with get_db() as db:
            return [
                GroupModel.model_validate(group)
                for group in db.query(Group)
                .filter(
                    func.json_array_length(Group.user_ids) > 0
                )  # Ensure array exists
                .filter(
                    Group.user_ids.cast(String).like(f'%"{user_id}"%')
                )  # String-based check
                .order_by(Group.updated_at.desc())
                .all()
            ]

    def get_child_groups(self, parent_id: str) -> list[GroupModel]:
        with get_db() as db:
            return [
                GroupModel.model_validate(group)
                for group in db.query(Group)
                .filter_by(parent_id=parent_id)
                .order_by(Group.updated_at.desc())
                .all()
            ]

    def get_group_ids_with_descendants(self, ids: list[str]) -> list[str]:
        """给定一组权限组 id，返回这些组及其全部后代组的 id 列表（去重）。

        用于权限继承：父组被授权时，其所有子组的成员也应视为被授权。
        """
        if not ids:
            return []
        with get_db() as db:
            # 一次查出全部组，在内存中构建树，避免逐层查库
            all_groups = db.query(Group).all()
        children_map: dict[str, list[str]] = {}
        for group in all_groups:
            if group.parent_id:
                children_map.setdefault(group.parent_id, []).append(group.id)

        result: list[str] = []
        visited: set[str] = set()

        def collect(group_id: str) -> None:
            if group_id in visited:
                return
            visited.add(group_id)
            result.append(group_id)
            for child_id in children_map.get(group_id, []):
                collect(child_id)

        for group_id in ids:
            collect(group_id)
        return result

    def has_children(self, id: str) -> bool:
        with get_db() as db:
            return db.query(Group).filter_by(parent_id=id).first() is not None

    def would_create_cycle(self, id: str, new_parent_id: Optional[str]) -> bool:
        # 将 id 挂到 new_parent_id 下是否会形成环：
        # 若 new_parent_id 是 id 自身，或 id 的某个后代，则形成环。
        if not new_parent_id:
            return False
        if new_parent_id == id:
            return True

        # 从 new_parent_id 向上回溯祖先链，若遇到 id 则成环。
        visited = set()
        current_id = new_parent_id
        while current_id:
            if current_id == id:
                return True
            if current_id in visited:
                # 数据已存在环，直接判定，避免死循环。
                break
            visited.add(current_id)
            parent = self.get_group_by_id(current_id)
            current_id = parent.parent_id if parent else None
        return False

    def get_group_by_id(self, id: str) -> Optional[GroupModel]:
        try:
            with get_db() as db:
                group = db.query(Group).filter_by(id=id).first()
                return GroupModel.model_validate(group) if group else None
        except Exception:
            return None

    def get_group_user_ids_by_id(self, id: str) -> Optional[str]:
        group = self.get_group_by_id(id)
        if group:
            return group.user_ids
        else:
            return None

    def update_group_by_id(
        self, id: str, form_data: GroupUpdateForm, overwrite: bool = False
    ) -> Optional[GroupModel]:
        try:
            with get_db() as db:
                db.query(Group).filter_by(id=id).update(
                    {
                        **form_data.model_dump(exclude_none=True),
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_group_by_id(id=id)
        except Exception as e:
            log.exception(e)
            return None

    def delete_group_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                db.query(Group).filter_by(id=id).delete()
                db.commit()
                return True
        except Exception:
            return False

    def delete_all_groups(self) -> bool:
        with get_db() as db:
            try:
                db.query(Group).delete()
                db.commit()

                return True
            except Exception:
                return False

    def remove_user_from_all_groups(self, user_id: str) -> bool:
        with get_db() as db:
            try:
                groups = self.get_groups_by_member_id(user_id)

                for group in groups:
                    group.user_ids.remove(user_id)
                    db.query(Group).filter_by(id=group.id).update(
                        {
                            "user_ids": group.user_ids,
                            "updated_at": int(time.time()),
                        }
                    )
                    db.commit()

                return True
            except Exception:
                return False

    def get_group_by_name(self, names: list[str] | str) -> Optional[GroupModel]:
        if isinstance(names, str):
            names = [names]
        with get_db() as db:
            group = db.query(Group).filter(Group.name.in_(names)).first()
            return GroupModel.model_validate(group) if group else None

    def add_user_to_group(self, user_id: str, group_id: str) -> bool:
        try:
            with get_db() as db:
                group = db.query(Group).filter_by(id=group_id).first()
                if group:
                    if user_id not in group.user_ids:
                        group.user_ids.append(user_id)
                        db.query(Group).filter_by(id=group_id).update(
                            {
                                "user_ids": group.user_ids,
                                "updated_at": int(time.time()),
                            }
                        )
                        db.commit()
                        return True
                    else:
                        return False
                return False
        except Exception as e:
            log.error(f"添加用户到权限组失败: {e}")
            return False

Groups = GroupTable()

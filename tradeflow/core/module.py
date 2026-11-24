"""Mô tả một module chức năng để ứng dụng tự gắn vào (menu + đường dẫn)."""
from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint


@dataclass(frozen=True)
class ModuleInfo:
    key: str
    label: str  # tên hiển thị trên menu
    path: str  # trang chính của module
    blueprint: Blueprint

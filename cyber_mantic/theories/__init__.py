"""
赛博玄数 - 术数理论模块
"""
from .base import BaseTheory, TheoryRegistry
from .bazi import BaZiTheory
from .xiaoliu import XiaoLiuRenTheory
from .meihua import MeiHuaTheory
from .liuyao import LiuYaoTheory
from .qimen import QiMenTheory
from .ziwei import ZiWeiTheory
from .daliuren import DaLiuRenTheory
from .cezi import CeZiTheory

# 注册所有理论
def register_all_theories():
    """注册所有术数理论"""
    TheoryRegistry.register(BaZiTheory())
    TheoryRegistry.register(XiaoLiuRenTheory())
    TheoryRegistry.register(MeiHuaTheory())
    TheoryRegistry.register(LiuYaoTheory())
    TheoryRegistry.register(QiMenTheory())
    TheoryRegistry.register(ZiWeiTheory())
    TheoryRegistry.register(DaLiuRenTheory())
    TheoryRegistry.register(CeZiTheory())

# 自动注册
register_all_theories()

__all__ = ['BaseTheory', 'TheoryRegistry', 'BaZiTheory', 'XiaoLiuRenTheory', 'MeiHuaTheory', 'LiuYaoTheory', 'QiMenTheory', 'ZiWeiTheory', 'DaLiuRenTheory', 'CeZiTheory']

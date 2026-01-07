"""
档案管理器测试
"""
import pytest
import tempfile
import os
from models import PersonBirthInfo
from utils.profile_manager import ProfileManager


class TestProfileManager:
    """档案管理器测试"""

    def setup_method(self):
        """设置测试"""
        # 使用临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.manager = ProfileManager(db_path=self.temp_db.name)

    def teardown_method(self):
        """清理测试"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_save_and_load_profile(self):
        """测试保存和加载档案"""
        profile = PersonBirthInfo(
            label="测试人物",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            birth_minute=30,
            calendar_type="solar",
            birth_time_certainty="certain",
            gender="male",
            birth_place_lng=120.5,
            mbti_type="INTJ"
        )

        # 保存
        assert self.manager.save_profile(profile) is True

        # 加载
        loaded = self.manager.load_profile("测试人物")
        assert loaded is not None
        assert loaded.label == "测试人物"
        assert loaded.birth_year == 1990
        assert loaded.birth_month == 6
        assert loaded.birth_day == 15
        assert loaded.birth_hour == 10
        assert loaded.birth_minute == 30
        assert loaded.gender == "male"
        assert loaded.mbti_type == "INTJ"

    def test_update_profile(self):
        """测试更新档案"""
        profile1 = PersonBirthInfo(
            label="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15
        )

        # 保存第一次
        assert self.manager.save_profile(profile1) is True

        # 更新
        profile2 = PersonBirthInfo(
            label="测试",
            birth_year=1991,
            birth_month=7,
            birth_day=16,
            birth_hour=12,
            gender="female"
        )
        assert self.manager.save_profile(profile2) is True

        # 验证更新
        loaded = self.manager.load_profile("测试")
        assert loaded.birth_year == 1991
        assert loaded.birth_month == 7
        assert loaded.birth_day == 16
        assert loaded.birth_hour == 12
        assert loaded.gender == "female"

    def test_delete_profile(self):
        """测试删除档案"""
        profile = PersonBirthInfo(
            label="待删除",
            birth_year=1990,
            birth_month=1,
            birth_day=1
        )

        # 保存
        assert self.manager.save_profile(profile) is True
        assert self.manager.load_profile("待删除") is not None

        # 删除
        assert self.manager.delete_profile("待删除") is True
        assert self.manager.load_profile("待删除") is None

    def test_max_profiles_limit(self):
        """测试档案数量限制"""
        # 保存3个档案
        for i in range(3):
            profile = PersonBirthInfo(
                label=f"档案{i+1}",
                birth_year=1990,
                birth_month=1,
                birth_day=1
            )
            assert self.manager.save_profile(profile) is True

        # 尝试保存第4个
        profile4 = PersonBirthInfo(
            label="档案4",
            birth_year=1990,
            birth_month=1,
            birth_day=1
        )
        assert self.manager.save_profile(profile4) is False

        # 验证数量
        assert self.manager.get_profile_count() == 3
        assert self.manager.can_add_profile() is False

    def test_list_profiles(self):
        """测试列出所有档案"""
        # 保存3个档案
        for i in range(3):
            profile = PersonBirthInfo(
                label=f"档案{i+1}",
                birth_year=1990,
                birth_month=1,
                birth_day=1
            )
            self.manager.save_profile(profile)

        # 列出档案
        profiles = self.manager.list_profiles()
        assert len(profiles) == 3

        labels = [p['label'] for p in profiles]
        assert "档案1" in labels
        assert "档案2" in labels
        assert "档案3" in labels

    def test_load_nonexistent_profile(self):
        """测试加载不存在的档案"""
        result = self.manager.load_profile("不存在")
        assert result is None

    def test_delete_nonexistent_profile(self):
        """测试删除不存在的档案"""
        result = self.manager.delete_profile("不存在")
        assert result is False


class TestPersonBirthInfo:
    """PersonBirthInfo数据模型测试"""

    def test_to_dict(self):
        """测试序列化"""
        person = PersonBirthInfo(
            label="测试",
            birth_year=1990,
            birth_month=6,
            birth_day=15,
            birth_hour=10,
            gender="male"
        )

        data = person.to_dict()
        assert data['label'] == "测试"
        assert data['birth_year'] == 1990
        assert data['birth_month'] == 6
        assert data['birth_day'] == 15
        assert data['birth_hour'] == 10
        assert data['gender'] == "male"

    def test_from_dict(self):
        """测试反序列化"""
        data = {
            'label': '测试',
            'birth_year': 1990,
            'birth_month': 6,
            'birth_day': 15,
            'birth_hour': 10,
            'gender': 'female',
            'mbti_type': 'ENFP'
        }

        person = PersonBirthInfo.from_dict(data)
        assert person.label == "测试"
        assert person.birth_year == 1990
        assert person.birth_month == 6
        assert person.birth_day == 15
        assert person.birth_hour == 10
        assert person.gender == "female"
        assert person.mbti_type == "ENFP"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

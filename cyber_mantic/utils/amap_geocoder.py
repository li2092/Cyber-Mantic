"""
高德地图地理编码工具
用于根据地点名称获取经纬度坐标
"""
import os
import requests
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache


class AmapGeocoder:
    """高德地图地理编码器"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化地理编码器

        Args:
            api_key: 高德地图API密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("AMAP_API_KEY", "")
        self.base_url = "https://restapi.amap.com/v3/geocode/geo"
        self.timeout = 5  # 超时时间（秒）

    @lru_cache(maxsize=100)
    def geocode(
        self,
        address: str,
        city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        地理编码：地址 -> 经纬度

        Args:
            address: 地址（如"北京市朝阳区望京SOHO"）
            city: 城市名称（可选，用于提高精度）

        Returns:
            包含经纬度信息的字典，如果失败则返回None
            {
                'location': '116.123456,39.123456',  # 经度,纬度
                'longitude': 116.123456,
                'latitude': 39.123456,
                'formatted_address': '北京市朝阳区望京街道望京SOHO',
                'province': '北京市',
                'city': '北京市',
                'district': '朝阳区',
                'adcode': '110105'
            }
        """
        if not self.api_key:
            print("警告：未配置高德地图API密钥（AMAP_API_KEY）")
            return None

        if not address or not address.strip():
            return None

        try:
            # 构建请求参数
            params = {
                'key': self.api_key,
                'address': address.strip()
            }

            if city:
                params['city'] = city.strip()

            # 发送请求
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            # 解析响应
            data = response.json()

            if data.get('status') != '1':
                error_info = data.get('info', 'Unknown error')
                print(f"高德地图API错误: {error_info}")
                return None

            geocodes = data.get('geocodes', [])
            if not geocodes:
                print(f"未找到地址: {address}")
                return None

            # 取第一个结果
            result = geocodes[0]
            location = result.get('location', '')

            if not location:
                return None

            # 解析经纬度
            try:
                lng_str, lat_str = location.split(',')
                longitude = float(lng_str)
                latitude = float(lat_str)
            except (ValueError, IndexError):
                print(f"无法解析坐标: {location}")
                return None

            return {
                'location': location,
                'longitude': longitude,
                'latitude': latitude,
                'formatted_address': result.get('formatted_address', address),
                'province': result.get('province', ''),
                'city': result.get('city', ''),
                'district': result.get('district', ''),
                'adcode': result.get('adcode', '')
            }

        except requests.exceptions.Timeout:
            print(f"高德地图API请求超时（{self.timeout}秒）")
            return None
        except requests.exceptions.RequestException as e:
            print(f"高德地图API请求失败: {e}")
            return None
        except Exception as e:
            print(f"地理编码失败: {e}")
            return None

    def get_longitude(self, address: str, city: Optional[str] = None) -> Optional[float]:
        """
        获取地址的经度

        Args:
            address: 地址
            city: 城市（可选）

        Returns:
            经度（float），失败返回None
        """
        result = self.geocode(address, city)
        return result['longitude'] if result else None

    def get_coordinates(
        self,
        address: str,
        city: Optional[str] = None
    ) -> Optional[Tuple[float, float]]:
        """
        获取地址的经纬度坐标

        Args:
            address: 地址
            city: 城市（可选）

        Returns:
            (经度, 纬度) 元组，失败返回None
        """
        result = self.geocode(address, city)
        return (result['longitude'], result['latitude']) if result else None

    def clear_cache(self):
        """清除缓存"""
        self.geocode.cache_clear()


# 全局实例
_geocoder = None


def get_geocoder() -> AmapGeocoder:
    """获取全局地理编码器实例"""
    global _geocoder
    if _geocoder is None:
        _geocoder = AmapGeocoder()
    return _geocoder


def geocode_address(address: str, city: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    便捷函数：地理编码

    Args:
        address: 地址
        city: 城市（可选）

    Returns:
        地理编码结果
    """
    return get_geocoder().geocode(address, city)


def get_longitude_from_address(address: str, city: Optional[str] = None) -> Optional[float]:
    """
    便捷函数：获取经度

    Args:
        address: 地址
        city: 城市（可选）

    Returns:
        经度
    """
    return get_geocoder().get_longitude(address, city)


# 示例用法
if __name__ == "__main__":
    # 测试地理编码
    geocoder = AmapGeocoder()

    # 测试1：北京
    result = geocoder.geocode("天安门", "北京")
    if result:
        print(f"地址: {result['formatted_address']}")
        print(f"经度: {result['longitude']}")
        print(f"纬度: {result['latitude']}")
        print()

    # 测试2：上海
    result = geocoder.geocode("东方明珠", "上海")
    if result:
        print(f"地址: {result['formatted_address']}")
        print(f"经度: {result['longitude']}")
        print(f"纬度: {result['latitude']}")
        print()

    # 测试3：详细地址
    result = geocoder.geocode("浙江省杭州市西湖区文三路")
    if result:
        print(f"地址: {result['formatted_address']}")
        print(f"经度: {result['longitude']}")
        print(f"纬度: {result['latitude']}")

import requests
from typing import Dict, Optional


class AutoDLAPI:
    """
    AutoDL 弹性部署 API 客户端
    """
    def __init__(self, base_url: str, api_token: str):
        """
        初始化 AutoDLAPI 客户端
        :param base_url: API 基础 URL
        :param api_token: 认证 Token
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.server_obj = {}

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """
        内部方法：发送 HTTP 请求
        :param method: HTTP 方法（GET、POST、PUT、DELETE）
        :param endpoint: API 端点
        :param data: 请求数据
        :return: 响应的 JSON 数据，或 None
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def list_images(self, page_index: int = 1, page_size: int = 10) -> Optional[Dict]:
        """
        获取私有镜像列表
        :param page_index: 页码
        :param page_size: 每页条目数
        :return: 镜像列表的 JSON 数据，或 None
        """
        data = {
            "page_index": page_index,
            "page_size": page_size
        }
        return self._request("POST", "/api/v1/dev/image/private/list", data)

    def create_deployment(self, deployment_data: Dict) -> Optional[Dict]:
        """
        创建部署
        :param deployment_data: 部署配置数据
        :return: 创建结果的 JSON 数据，或 None
        """
        return self._request("POST", "/api/v1/dev/deployment", deployment_data)

    def list_deployments(self, page_index: int = 1, page_size: int = 10) -> Optional[Dict]:
        """
        获取部署列表
        :param page_index: 页码
        :param page_size: 每页条目数
        :return: 部署列表的 JSON 数据，或 None
        """
        data = {
            "page_index": page_index,
            "page_size": page_size
        }
        return self._request("POST", "/api/v1/dev/deployment/list", data)

    def get_container_events(self, deployment_uuid: str = "", page_index: int = 1, page_size: int = 10) -> Optional[Dict]:
        """
        获取容器事件列表
        :param deployment_uuid: 部署 UUID（可选）
        :param page_index: 页码
        :param page_size: 每页条目数
        :return: 容器事件列表的 JSON 数据，或 None
        """
        data = {
            "deployment_uuid": deployment_uuid,
            "page_index": page_index,
            "page_size": page_size
        }
        return self._request("POST", "/api/v1/dev/deployment/container/event/list", data)

    def stop_container(self, container_uuid: str, decrease_replica: bool = False) -> Optional[Dict]:
        """
        停止容器
        :param container_uuid: 容器 UUID
        :param decrease_replica: 是否减少副本数量
        :return: 操作结果的 JSON 数据，或 None
        """
        data = {
            "deployment_container_uuid": container_uuid,
            "decrease_replica": decrease_replica
        }
        return self._request("PUT", "/api/v1/dev/deployment/container/stop", data)

    def set_replica_num(self, deployment_uuid: str, replica_num: int) -> Optional[Dict]:
        """
        设置部署的副本数量
        :param deployment_uuid: 部署 UUID
        :param replica_num: 副本数量
        :return: 操作结果的 JSON 数据，或 None
        """
        data = {
            "deployment_uuid": deployment_uuid,
            "replica_num": replica_num
        }
        return self._request("PUT", "/api/v1/dev/deployment/replica", data)

    def stop_deployment(self, deployment_uuid: str) -> Optional[Dict]:
        """
        停止部署
        :param deployment_uuid: 部署 UUID
        :return: 操作结果的 JSON 数据，或 None
        """
        data = {
            "deployment_uuid": deployment_uuid,
            "operate": "stop"
        }
        return self._request("PUT", "/api/v1/dev/deployment/operate", data)

    def delete_deployment(self, deployment_uuid: str) -> Optional[Dict]:
        """
        删除部署
        :param deployment_uuid: 部署 UUID
        :return: 操作结果的 JSON 数据，或 None
        """
        data = {
            "deployment_uuid": deployment_uuid
        }
        return self._request("DELETE", "/api/v1/dev/deployment", data)

    def set_blacklist(self, container_uuid: str, comment: str = "") -> Optional[Dict]:
        """
        设置调度黑名单
        :param container_uuid: 容器 UUID
        :param comment: 备注信息
        :return: 操作结果的 JSON 数据，或 None
        """
        data = {
            "deployment_container_uuid": container_uuid,
            "comment": comment
        }
        return self._request("POST", "/api/v1/dev/deployment/blacklist", data)

    def get_gpu_stock(self) -> Optional[Dict]:
        """
        获取弹性部署 GPU 库存
        :return: GPU 库存信息的 JSON 数据，或 None
        """
        return self._request("GET", "/api/v1/dev/machine/gpu_stock")


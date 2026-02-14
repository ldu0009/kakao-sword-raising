import json
import os

class Database:
    """계보(Route)와 미분류(Unclassified)를 관리하는 고도화된 DB"""
    DB_PATH = "data/encyclopedia.json"

    @staticmethod
    def load_all():
        """초기화된 혹은 저장된 데이터를 로드합니다."""
        default = {"routes": {}, "unclassified": {}}
        if not os.path.exists(Database.DB_PATH):
            return default
        try:
            with open(Database.DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 데이터 정합성 체크 (필요 시)
                if "routes" not in data: return default
                return data
        except Exception:
            return default

    @staticmethod
    def save_all(data):
        """데이터 전체를 저장합니다."""
        os.makedirs(os.path.dirname(Database.DB_PATH), exist_ok=True)
        with open(Database.DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def get_route_by_weapon_name(data, name):
        """무기 이름을 통해 해당 무기가 속한 루트 정보를 반환"""
        for route_id, info in data["routes"].items():
            if name in info["levels"].values():
                return route_id, info
        return None, None

    @staticmethod
    def clear_database():
        """모든 데이터를 삭제하고 초기화합니다."""
        initial_data = {"routes": {}, "unclassified": {}}
        Database.save_all(initial_data)
        return initial_data

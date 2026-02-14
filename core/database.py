import json
import os

class Database:
    """도감, 미분류, 루트 정보를 영구 저장하는 고도화된 DB"""
    DB_PATH = "data/encyclopedia.json"

    @staticmethod
    def load_all():
        """모든 데이터를 로드합니다."""
        default = {"classified": {}, "unclassified": {}, "routes": []}
        if not os.path.exists(Database.DB_PATH):
            return default
        try:
            with open(Database.DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 하위 호환성 유지
                if "classified" not in data:
                    return {"classified": data, "unclassified": {}, "routes": []}
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
    def promote_weapon(name, grade):
        """미분류 무기를 정식 도감으로 승격시키고 미분류에서 삭제합니다."""
        data = Database.load_all()
        # 정식 도감 추가
        data["classified"][name] = {"grade": grade}
        # 미분류에서 삭제
        if name in data["unclassified"]:
            del data["unclassified"][name]
        
        Database.save_all(data)
        return data

import json
import os

class Database:
    DB_PATH = "data/encyclopedia.json"
    STATS_PATH = "data/analytics.json"
    CONFIG_PATH = "data/config.json" # [NEW] 설정 파일 경로

    @staticmethod
    def load_all():
        default = {"routes": {}, "unclassified": {}}
        if not os.path.exists(Database.DB_PATH): return default
        try:
            with open(Database.DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return default

    @staticmethod
    def save_all(data):
        os.makedirs("data", exist_ok=True)
        with open(Database.DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_stats():
        default = {"attempts": [], "spawn_counts": {"일반": 0, "희귀": 0}, "level_stats": {}}
        if not os.path.exists(Database.STATS_PATH): return default
        try:
            with open(Database.STATS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return default

    @staticmethod
    def save_stats(stats):
        os.makedirs("data", exist_ok=True)
        with open(Database.STATS_PATH, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)

    # --- [NEW] 설정값 저장/로드 관련 ---
    @staticmethod
    def load_config():
        """마지막 UI 설정값을 불러옵니다."""
        default = {
            "mode": 0,
            "target_gold": "1,000,000,000",
            "sale_threshold": 10,
            "start_fund": "50,000,000",
            "min_fund": "10,000,000",
            "target_grade": 0,
            "target_level": 10,
            "exclude_collection": False
        }
        if not os.path.exists(Database.CONFIG_PATH): return default
        try:
            with open(Database.CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return default

    @staticmethod
    def save_config(config_data):
        """UI 설정값을 파일에 저장합니다."""
        os.makedirs("data", exist_ok=True)
        with open(Database.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def record_attempt(grade, level, result, cost):
        stats = Database.load_stats()
        stats["attempts"].append({"g": grade, "l": level, "r": result, "c": cost})
        if grade not in stats["level_stats"]: stats["level_stats"][grade] = {}
        lv_str = str(level)
        if lv_str not in stats["level_stats"][grade]:
            stats["level_stats"][grade][lv_str] = {"success": 0, "maintain": 0, "destroy": 0, "cost": 0, "tries": 0}
        s = stats["level_stats"][grade][lv_str]
        s["tries"] += 1; s["cost"] += cost
        if result == "성공": s["success"] += 1
        elif result == "유지": s["maintain"] += 1
        elif result == "파괴": s["destroy"] += 1
        Database.save_stats(stats); return stats

    @staticmethod
    def record_spawn(grade):
        stats = Database.load_stats(); stats["spawn_counts"][grade] += 1
        Database.save_stats(stats); return stats

    @staticmethod
    def get_route_by_weapon_name(data, name):
        for rid, info in data["routes"].items():
            if name in info["levels"].values(): return rid, info
        return None, None

    @staticmethod
    def clear_database():
        init = {"routes": {}, "unclassified": {}}
        Database.save_all(init); return init

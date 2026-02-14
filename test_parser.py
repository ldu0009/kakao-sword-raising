import re
import json
import os

def test_parsing():
    file_path = "KakaoTalk_20260214_1954_23_587_group.txt"
    if not os.path.exists(file_path):
        print("Error: File not found")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    header_pattern = r'\[([^\]]+)\]\s*\[(오[전후]\s*\d+:\d+)\]'
    parts = re.split(header_pattern, raw_text)
    messages = []
    
    for i in range(1, len(parts), 3):
        if i + 2 < len(parts):
            messages.append({
                "sender": parts[i].strip(),
                "time": parts[i+1].strip(),
                "content": parts[i+2].strip()
            })

    print(f"Total: {len(messages)}")
    
    bot_msgs = [m for m in messages if "플레이봇" in m["sender"]]
    print(f"Bot Messages: {len(bot_msgs)}")
    
    if bot_msgs:
        latest = bot_msgs[-1]
        print(f"Latest Bot Msg Time: {latest['time']}")
        
        gold_match = re.search(r"골드\s*[:：]\s*([\d,]+)", latest["content"])
        weapon_match = re.search(r"검\s*[:：]\s*([^\n\r]+)", latest["content"])
        
        print(f"Gold: {gold_match.group(1) if gold_match else 'None'}")
        print(f"Weapon: {weapon_match.group(1) if weapon_match else 'None'}")

if __name__ == "__main__":
    test_parsing()

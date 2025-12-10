import random

def select_theme():
    # お題のデータベース（タプルでペアを管理）
    # (単語A, 単語B) の順序は固定でOK
    topics_db = [
        ("りんご", "梨"),
        ("スキー", "スノボ"),
        ("LINE", "Instagram"),
        ("マクドナルド", "モスバーガー"),
        ("映画館", "水族館"),
        ("幽霊", "宇宙人"),
        ("シャワー", "お風呂"),
    ]

    # 1. リストからランダムに1つのペアを選ぶ
    selected_pair = random.choice(topics_db)
    
    # 2. どちらを「市民（多数派）」にし、どちらを「ウルフ（少数派）」にするかランダムに決める
    # これをしないと、データベースの左側が常に市民になってしまうため
    word_a, word_b = selected_pair
    
    if random.random() < 0.5:
        citizen_word = word_a
        wolf_word = word_b
    else:
        citizen_word = word_b
        wolf_word = word_a

    return citizen_word, wolf_word

# --- 実行テスト ---
citizen, wolf = select_theme()

print(f"【市民ワード】: {citizen}")
print(f"【ウルフワード】: {wolf}")
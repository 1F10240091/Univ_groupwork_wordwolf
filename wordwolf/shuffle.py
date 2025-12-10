def assign_roles(players_count, wolf_count=1):
    """
    players_count: プレイヤーの人数 (例: 5)
    wolf_count: ウルフの人数 (例: 1)
    """
    # 1. お題を取得
    citizen_word, wolf_word = select_theme()
    
    # 2. 配布用リストを作成
    # 市民の数 = 全員 - ウルフの数
    game_words = [citizen_word] * (players_count - wolf_count)
    # ウルフのワードを追加
    game_words.extend([wolf_word] * wolf_count)
    
    # 3. リストをシャッフル（誰がウルフかわからなくする）
    random.shuffle(game_words)
    
    return game_words, citizen_word, wolf_word

# --- 実行例（プレイヤー5人、ウルフ1人の場合）---
players = 5
distributed_words, true_citizen, true_wolf = assign_roles(players)

print(f"プレイヤーへの配布リスト（中身は秘密）: {distributed_words}")
# 結果例: ['りんご', 'りんご', '梨', 'りんご', 'りんご'] 
# ※ '梨' がウルフ
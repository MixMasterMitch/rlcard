

def cards_by_rank(cards):
    hand_by_rank = {}
    for card in cards:
        if card.rank not in hand_by_rank:
            hand_by_rank[card.rank] = []
        hand_by_rank[card.rank].append(card)
    return hand_by_rank
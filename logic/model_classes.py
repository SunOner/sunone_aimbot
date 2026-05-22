PLAYER_CLASS_ID = 0
HEAD_CLASS_ID = 1

HIDEOUT_TARGET_CLASS_IDS = (5, 6)

CLASS_NAMES = {
    PLAYER_CLASS_ID: "player",
    HEAD_CLASS_ID: "head",
    2: "weapon",
    3: "outline",
    4: "dead_body",
    5: "hideout_target_human",
    6: "hideout_target_balls",
    8: "smoke",
    9: "fire",
}

NON_TARGET_CLASS_IDS = {2, 3, 4, 8, 9, 10}


def is_head_class(class_id) -> bool:
    try:
        return int(class_id) == HEAD_CLASS_ID
    except (TypeError, ValueError):
        return False

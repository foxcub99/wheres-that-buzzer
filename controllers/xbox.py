button_names_xbox = {
    0: "A",
    1: "B",
    2: "X",
    3: "Y",
    # 4: "L1",
    # 5: "R1",
    # 6: "L2",
    # 7: "R2",
    # 8: "Share",
    # 9: "Options",
    # 10: "L3",
    11: "Up",
    12: "Down",
    13: "Left",
    14: "Right",
}


def get_button_name_xbox(button_id):
    return button_names_xbox.get(button_id, "Not Mapped")

def get_button_id_xbox(button_name):
    for id, name in button_names_xbox.items():
        if name == button_name:
            return id
    return None
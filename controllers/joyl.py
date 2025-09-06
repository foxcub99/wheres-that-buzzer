button_names_joyl = {
    0: "Down",
    1: "Left",
    2: "Right",
    3: "Up",
    # 4: "L1",
    # 5: "R1",
    # 6: "L2",
    # 7: "R2",
    # 8: "Share",
    # 9: "Options",
    # 10: "L3",
    # 11: "R3",
    # 12: "PS",
    # 13: "Touchpad",
}


def get_button_name_joyl(button_id):
    return button_names_joyl.get(button_id, "Not Mapped")

def get_button_id_joyl(button_name):
    for id, name in button_names_joyl.items():
        if name == button_name:
            return id
    return None
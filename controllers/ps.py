button_names_ps = {
    0: "Cross",
    1: "Circle",
    2: "Square",
    3: "Triangle",
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


def get_button_name_ps(button_id):
    return button_names_ps.get(button_id, "Not Mapped")

def get_button_id_ps(button_name):
    for id, name in button_names_ps.items():
        if name == button_name:
            return id
    return None
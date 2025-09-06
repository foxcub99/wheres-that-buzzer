button_names_joyr = {
    0: "X",
    1: "A",
    2: "Y",
    3: "B",
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


def get_button_name_joyr(button_id):
    return button_names_joyr.get(button_id, "Not Mapped")

def get_button_id_joyr(button_name):
    for id, name in button_names_joyr.items():
        if name == button_name:
            return id
    return None
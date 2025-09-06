button_names_keyboard = {
    "Key.esc": "Esc",
    "a": "a",
    "b": "b",
}


def get_button_name_keyboard(button_id):
    return button_names_keyboard.get(button_id, "Not Mapped")

def get_button_id_keyboard(button_name):
    for id, name in button_names_keyboard.items():
        if name == button_name:
            return id
    return None
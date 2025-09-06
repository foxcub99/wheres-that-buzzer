from . import joyl, joyr, ps, switch, xbox

def get_button_name(controller_type, button_id):
    if "Xbox" in controller_type:
        return xbox.get_button_name_xbox(button_id)
    elif "DualSense" in controller_type or "DUALSHOCK" in controller_type or "PS4" in controller_type:
        return ps.get_button_name_ps(button_id)
    elif "(L)" in controller_type:
        return joyl.get_button_name_joyl(button_id)
    elif "(R)" in controller_type:
        return joyr.get_button_name_joyr(button_id)
    elif "Pro" in controller_type:
        return switch.get_button_name_switch(button_id)
    else:
        return "Unknown Controller"

# Helper to get all valid button ids for a controller type
def get_all_button_ids(controller_type):
    if "Xbox" in controller_type:
        return list(xbox.button_names_xbox.keys())
    elif "DualSense" in controller_type or "DUALSHOCK" in controller_type or "PS4" in controller_type:
        return list(ps.button_names_ps.keys())
    elif "(L)" in controller_type:
        return list(joyl.button_names_joyl.keys())
    elif "(R)" in controller_type:
        return list(joyr.button_names_joyr.keys())
    elif "Pro" in controller_type:
        return list(switch.button_names_switch.keys())
    else:
        return list(range(0, 15))

def get_button_id(controller_type, button_name):
    if "Xbox" in controller_type:
        return xbox.get_button_id_xbox(button_name)
    elif "DualSense" in controller_type or "DUALSHOCK" in controller_type or "PS4" in controller_type:
        return ps.get_button_id_ps(button_name)
    elif "(L)" in controller_type:
        return joyl.get_button_id_joyl(button_name)
    elif "(R)" in controller_type:
        return joyr.get_button_id_joyr(button_name)
    elif "Pro" in controller_type:
        return switch.get_button_id_switch(button_name)
    else:
        return "Unknown Controller"
## Ren'Py project options for Chaco.

define config.name = "Chaco"
define config.version = "0.3.0"
define gui.show_name = True
define config.has_autosave = True
define config.autosave_slots = 3

# Window size
define config.screen_width = 1280
define config.screen_height = 720

# Text
define gui.text_size = 22
define gui.name_text_size = 22

# Disable rollback for network-driven game (state lives on the server)
define config.rollback_enabled = False
define config.rollback_length = 0

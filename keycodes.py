"""
Keycodes used by ObinsKit application to designate keypresses.

originalMap originally came from dighelm project where it was produced by
reverse engineering the ObinsKit Electron app. Here originalMap has been
"syntactically pythonified" and cleaned up by:
    1. Commenting out entries with duplicate key names:
        a. ENTER and 0-9:
               These all appear in the [88-98] range. I modified the code
               below to simply not insert if already in the map.
        b. CTRL, ALT, SHIFT:
              These were not exactly duplicates but were mislabeled Left/Right
              variants of Ctrl, Alt, and Shift. For these, I prepended "Left "
              or " Right" to their names in originalMap to disambiguate.
              This detail was previously stored in the 'info' field, which is
              unused in this project.
    2. Removing unused dict elements:
        a. alias
        b. info
        c. icon

We transform `originalMap` into more useful representations of the data, maps
keyed by name and value, repectively:
  1. `keycodes_by_value`, which optimizes lookups using the integer keycode and
  2. `keycodes_by_name`, which optimizes lookups using the string name.

Nota Bene:
    * "value" in this context is the integer that appears in macro_value
      in the SQLITE db.

References:
    * https://github.com/reischapa/dighelm/blob/master/keycodes.js#L1
    * https://github.com/reischapa/dighelm/issues/1
"""

originalMap = [
    [    1,  {"name": "Esc",           "value":  41}],
    [    2,  {"name": "1",             "value":  30}],
    [    3,  {"name": "2",             "value":  31}],
    [    4,  {"name": "3",             "value":  32}],
    [    5,  {"name": "4",             "value":  33}],
    [    6,  {"name": "5",             "value":  34}],
    [    7,  {"name": "6",             "value":  35}],
    [    8,  {"name": "7",             "value":  36}],
    [    9,  {"name": "8",             "value":  37}],
    [    10, {"name": "9",             "value":  38}],
    [    11, {"name": "0",             "value":  39}],
    [    12, {"name": "-_",            "value":  45}],
    [    13, {"name": "=+",            "value":  46}],
    [    14, {"name": "Backspace",     "value":  42}],
    [    15, {"name": "Tab",           "value":  43}],
    [    16, {"name": "Q",             "value":  20}],
    [    17, {"name": "W",             "value":  26}],
    [    18, {"name": "E",             "value":   8}],
    [    19, {"name": "R",             "value":  21}],
    [    20, {"name": "T",             "value":  23}],
    [    21, {"name": "Y",             "value":  28}],
    [    22, {"name": "U",             "value":  24}],
    [    23, {"name": "I",             "value":  12}],
    [    24, {"name": "O",             "value":  18}],
    [    25, {"name": "P",             "value":  19}],
    [    26, {"name": "[{",            "value":  47}],
    [    27, {"name": "]}",            "value":  48}],
    [    28, {"name": "Enter",         "value":  40}],
    [    29, {"name": "LeftCtrl",      "value": 224}],
    [    30, {"name": "A",             "value":   4}],
    [    31, {"name": "S",             "value":  22}],
    [    32, {"name": "D",             "value":   7}],
    [    33, {"name": "F",             "value":   9}],
    [    34, {"name": "G",             "value":  10}],
    [    35, {"name": "H",             "value":  11}],
    [    36, {"name": "J",             "value":  13}],
    [    37, {"name": "K",             "value":  14}],
    [    38, {"name": "L",             "value":  15}],
    [    39, {"name": ";:",            "value":  51}],
    [    40, {"name": '"',             "value":  52}],
    [    41, {"name": "`~",            "value":  53}],
    [    42, {"name": "LeftShift",     "value": 225}],
    [    43, {"name": "\\|",           "value":  49}],
    [    44, {"name": "Z",             "value":  29}],
    [    45, {"name": "X",             "value":  27}],
    [    46, {"name": "C",             "value":   6}],
    [    47, {"name": "V",             "value":  25}],
    [    48, {"name": "B",             "value":   5}],
    [    49, {"name": "N",             "value":  17}],
    [    50, {"name": "M",             "value":  16}],
    [    51, {"name": ",<",            "value":  54}],
    [    52, {"name": ".>",            "value":  55}],
    [    53, {"name": "/?",            "value":  56}],
    [    54, {"name": "RightShift",    "value": 229}],
    [    56, {"name": "LeftAlt",       "value": 226}],
    [    57, {"name": "Space",         "value":  44}],
    [    58, {"name": "CapsLock",      "value":  57}],
    [    59, {"name": "F1",            "value":  58}],
    [    60, {"name": "F2",            "value":  59}],
    [    61, {"name": "F3",            "value":  60}],
    [    62, {"name": "F4",            "value":  61}],
    [    63, {"name": "F5",            "value":  62}],
    [    64, {"name": "F6",            "value":  63}],
    [    65, {"name": "F7",            "value":  64}],
    [    66, {"name": "F8",            "value":  65}],
    [    67, {"name": "F9",            "value":  66}],
    [    68, {"name": "F10",           "value":  67}],
    [    69, {"name": "NumLock",       "value":  83}],
    [    70, {"name": "Scroll Lock",   "value":  71}],
    #[    71, {"name": "7",             "value":  95}],  # DUPLICATE
    #[    72, {"name": "8",             "value":  96}],  # DUPLICATE
    #[    73, {"name": "9",             "value":  97}],  # DUPLICATE
    [    74, {"name": "-",             "value":  86}],
    #[    75, {"name": "4",             "value":  92}],   # DUPLICATE
    #[    76, {"name": "5",             "value":  93}],   # DUPLICATE
    #[    77, {"name": "6",             "value":  94}],   # DUPLICATE
    [    78, {"name": "+",             "value":  87}],
    #[    79, {"name": "1",             "value": 89}],  # DUPLICATE
    #[    80, {"name": "2",             "value": 90}],  # DUPLICATE
    #[    81, {"name": "3",             "value": 91}],  # DUPLICATE
    #[    82, {"name": "0",             "value": 98}],  # DUPLICATE
    [    83, {"name": ".",             "value":  99}],
    [    87, {"name": "F11",           "value":  68}],
    [    88, {"name": "F12",           "value":  69}],
    [    91, {"name": "PrintScreen",   "value":  70}],
    #[ 3612,{"name": "Enter",           "value":  88}],  # DUPLICATE
    [ 3613, {"name": "RightCtrl",      "value": 228}],
    [ 3639, {"name": "PrintScreen",    "value":  70}],
    [ 3640, {"name": "RightAlt",       "value": 230}],
    [ 3653, {"name": "Pause",          "value":  72}],
    [ 3655, {"name": "Home",           "value":  74}],
    [ 3657, {"name": "PageUp",         "value":  75}],
    [ 3663, {"name": "End",            "value":  77}],
    [ 3665, {"name": "PageDown",       "value":  78}],
    [ 3666, {"name": "Insert",         "value":  73}],
    [ 3667, {"name": "Delete",         "value":  76}],
    # [ 3675, {"name": "icon.left_gui",  "value": 227, "alias": "Win/Cmd", "icon": "win-mac"}],  # What's This?
    # [ 3676, {"name": "icon.right_gui", "value": 231, "alias": "Win/Cmd", "icon": "win-mac"}],  # What's This?
    [ 3677, {"name": "Menu",           "value": 101}],
    [57416, {"name": "↑",              "value":  82}],
    [57419, {"name": "←",              "value":  80}],
    [57421, {"name": "→",              "value":  79}],
    [57424, {"name": "↓",              "value":  81}],
    [61000, {"name": "↑",              "value":  82}],
    [61001, {"name": "PageUp",         "value":  75}],
    [61003, {"name": "←",              "value":  80}],
    [61005, {"name": "→",              "value":  79}],
    [61007, {"name": "End",            "value":  77}],
    [61008, {"name": "↓",              "value":  81}],
    [61009, {"name": "PageDown",       "value":  78}],
    [61010, {"name": "Insert",         "value":  73}],
    [61011, {"name": "Delete",         "value":  76}],
    [60999, {"name": "Home",           "value":  74}],
]

keycodes_by_value = {
    _dict["value"]: {"id": _id, "name": _dict["name"]} for _id, _dict in originalMap
}
keycodes_by_name = {
    _dict["name"]: {"id": _id, "value": _dict["value"]} for _id, _dict in originalMap
}

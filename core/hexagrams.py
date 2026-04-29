"""64 hexagrams with names, themes, and symbolic tone tags."""

HEXAGRAMS = {
    1:  ("Qián",  "The Creative",            "Decisive forward action; strength."),
    2:  ("Kūn",   "The Receptive",           "Yielding, supportive, fertile ground."),
    3:  ("Zhūn",  "Difficulty at Beginning", "Initial chaos before order."),
    4:  ("Méng",  "Youthful Folly",          "Inexperience; need for guidance."),
    5:  ("Xū",    "Waiting",                 "Patience before the storm."),
    6:  ("Sòng",  "Conflict",                "Friction, disputes, legal trouble."),
    7:  ("Shī",   "The Army",                "Disciplined collective force."),
    8:  ("Bǐ",    "Holding Together",        "Union, alliance, solidarity."),
    9:  ("Xiǎo Chù", "Small Taming",         "Restraint of small things."),
    10: ("Lǚ",    "Treading",                "Cautious conduct on dangerous ground."),
    11: ("Tài",   "Peace",                   "Harmonious flow."),
    12: ("Pǐ",    "Standstill",              "Stagnation, blocked communication."),
    13: ("Tóng Rén", "Fellowship",           "Like minds gathering."),
    14: ("Dà Yǒu","Great Possession",        "Abundance, but watch for envy."),
    15: ("Qiān",  "Modesty",                 "Humility brings success."),
    16: ("Yù",    "Enthusiasm",              "Joyful momentum, possible recklessness."),
    17: ("Suí",   "Following",               "Adaptation; risk of being misled."),
    18: ("Gǔ",    "Work on the Decayed",     "Repair of corruption."),
    19: ("Lín",   "Approach",                "Arrival of influence."),
    20: ("Guān",  "Contemplation",           "Observation, watchfulness."),
    21: ("Shì Hé","Biting Through",          "Decisive judgment; punishment."),
    22: ("Bì",    "Grace",                   "Surface beauty; appearances."),
    23: ("Bō",    "Splitting Apart",         "Decay, opportunism, predation."),
    24: ("Fù",    "Return",                  "Renewal after darkness."),
    25: ("Wú Wàng","Innocence",              "Spontaneity; unexpected events."),
    26: ("Dà Chù","Great Taming",            "Restraining great force."),
    27: ("Yí",    "Nourishment",             "What you feed grows."),
    28: ("Dà Guò","Great Excess",            "Critical overload, breaking point."),
    29: ("Kǎn",   "The Abyss",               "Repeated danger; trapped flow."),
    30: ("Lí",    "The Clinging Fire",       "Brightness, but also burning."),
    31: ("Xián",  "Influence",               "Mutual attraction."),
    32: ("Héng",  "Duration",                "Long-lasting patterns."),
    33: ("Dùn",   "Retreat",                 "Strategic withdrawal."),
    34: ("Dà Zhuàng","Great Power",          "Force; risk of overreach."),
    35: ("Jìn",   "Progress",                "Steady advance."),
    36: ("Míng Yí","Darkening of the Light", "Concealment, suppressed truth."),
    37: ("Jiā Rén","The Family",             "Domestic order."),
    38: ("Kuí",   "Opposition",              "Misunderstanding, divergence."),
    39: ("Jiǎn",  "Obstruction",             "Obstacles in path."),
    40: ("Xiè",   "Deliverance",             "Release from tension."),
    41: ("Sǔn",   "Decrease",                "Loss, sacrifice."),
    42: ("Yì",    "Increase",                "Gain, expansion."),
    43: ("Guài",  "Breakthrough",            "Resolute action; confrontation."),
    44: ("Gòu",   "Coming to Meet",          "Unexpected encounter; seduction."),
    45: ("Cuì",   "Gathering Together",      "Crowds; collective energy."),
    46: ("Shēng", "Pushing Upward",          "Gradual rise."),
    47: ("Kùn",   "Oppression",              "Exhaustion, scarcity."),
    48: ("Jǐng",  "The Well",                "Shared resource; community."),
    49: ("Gé",    "Revolution",              "Sudden upheaval."),
    50: ("Dǐng",  "The Cauldron",            "Transformation through fire."),
    51: ("Zhèn",  "The Arousing Thunder",    "Shock, sudden disturbance."),
    52: ("Gèn",   "Keeping Still",           "Stillness, meditation."),
    53: ("Jiàn",  "Gradual Development",     "Slow, steady growth."),
    54: ("Guī Mèi","The Marrying Maiden",    "Subordinate position; deception risk."),
    55: ("Fēng",  "Abundance",               "Peak; soon to wane."),
    56: ("Lǚ",    "The Wanderer",            "Transience, vulnerability of strangers."),
    57: ("Xùn",   "The Gentle Wind",         "Subtle, penetrating influence."),
    58: ("Duì",   "The Joyous Lake",         "Pleasure, social gathering."),
    59: ("Huàn",  "Dispersion",              "Dissolution of barriers."),
    60: ("Jié",   "Limitation",              "Discipline, boundaries."),
    61: ("Zhōng Fú","Inner Truth",           "Sincerity reaches all."),
    62: ("Xiǎo Guò","Small Excess",          "Minor overstepping."),
    63: ("Jì Jì", "After Completion",        "Order achieved; complacency risk."),
    64: ("Wèi Jì","Before Completion",       "Almost there; danger near goal."),
}

DANGER_HEXAGRAMS = {6, 21, 23, 28, 29, 36, 38, 39, 47, 49, 51, 54, 56}
NEUTRAL_HEXAGRAMS = {3, 4, 5, 12, 17, 20, 33, 41, 44, 55, 62, 64}
HARMONY_HEXAGRAMS = {1, 2, 7, 8, 9, 10, 11, 13, 14, 15, 16, 18, 19, 22,
                     24, 25, 26, 27, 30, 31, 32, 34, 35, 37, 40, 42, 43,
                     45, 46, 48, 50, 52, 53, 57, 58, 59, 60, 61, 63}


def hexagram_tone(num: int) -> str:
    if num in DANGER_HEXAGRAMS:
        return "danger"
    if num in NEUTRAL_HEXAGRAMS:
        return "neutral"
    return "harmony"

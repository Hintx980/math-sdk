"""StoneMind Rift game configuration."""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Configuration for StoneMind Rift (5x5 cluster with features)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "stone_mind_rift"
        self.provider_number = 0
        self.working_name = "StoneMind Rift"
        self.wincap = 5000.0
        self.win_type = "cluster"
        self.rtp = 0.9600
        self.construct_paths()

        # Grid
        self.num_reels = 5
        self.num_rows = [5] * self.num_reels

        # Paytable: 9 symbols with three cluster tiers (3-7, 8-12, 13-25)
        # Codes map to emojis for FE:
        # L1=Gray Rock, L2=Brown Bone, L3=Purple Shard, L4=Blue Stone,
        # H1=Light Blue Pebble, H2=Green Jade, H3=Yellow Amber, H4=Orange Fossil, H5=Red Ruby
        r1, r2, r3 = (3, 7), (8, 12), (13, 25)
        pay_group = {
            (r1, "L1"): 0.1, (r2, "L1"): 0.6, (r3, "L1"): 1.5,
            (r1, "L2"): 0.15, (r2, "L2"): 0.8, (r3, "L2"): 2.5,
            (r1, "L3"): 0.2, (r2, "L3"): 1.0, (r3, "L3"): 4.0,
            (r1, "L4"): 0.3, (r2, "L4"): 1.2, (r3, "L4"): 6.0,
            (r1, "H1"): 0.4, (r2, "H1"): 1.5, (r3, "H1"): 8.0,
            (r1, "H2"): 0.5, (r2, "H2"): 2.0, (r3, "H2"): 10.0,
            (r1, "H3"): 0.75, (r2, "H3"): 4.0, (r3, "H3"): 15.0,
            (r1, "H4"): 1.0, (r2, "H4"): 8.0, (r3, "H4"): 20.0,
            (r1, "H5"): 2.5, (r2, "H5"): 15.0, (r3, "H5"): 50.0,
        }
        self.paytable = self.convert_range_table(pay_group)

        # Special symbols
        # W=wild, M=multiplier, B=tnt bomb, R=respins, PRIZE tokens: mni/maj/meg/max
        self.include_padding = True
        self.special_symbols = {
            "wild": ["W"],
            "multiplier": ["M"],
            "tnt": ["B"],
            "respin": ["R"],
            "prize": ["mni", "maj", "meg", "max"],
        }

        # We do not use scatter; set empty to disable FS checks in draw flow
        self.freespin_triggers = {self.basegame_type: {}, self.freegame_type: {}}
        self.anticipation_triggers = {self.basegame_type: 0, self.freegame_type: 0}

        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        # Bet modes
        # Base: 90% normal spins (2 features per spin), 10% portal to super (4 features per spin)
        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="super",
                        quota=0.05,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_freegame": True,
                            # Multiplier values for super spins
                            "mult_values": {
                                self.basegame_type: {10: 32, 20: 26, 50: 18, 100: 12, 200: 7, 500: 5},
                                self.freegame_type: {10: 32, 20: 26, 50: 18, 100: 12, 200: 7, 500: 5},
                            },
                        },
                    ),
                    Distribution(
                        criteria="normal",
                        quota=0.95,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_freegame": False,
                            # Multiplier values for normal spins
                            "mult_values": {
                                self.basegame_type: {1: 45, 2: 25, 3: 15, 5: 8, 10: 5, 20: 2, 50: 1, 100: 1},
                                self.freegame_type: {1: 45, 2: 25, 3: 15, 5: 8, 10: 5, 20: 2, 50: 1, 100: 1},
                            },
                        },
                    ),
                ],
            ),
            # Super Buy: direct entry to 5-spin super mode with strong multipliers
            BetMode(
                name="super_buy",
                cost=6.5,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="super",
                        quota=1.0,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_freegame": True,
                            "mult_values": {
                                self.basegame_type: {10: 32, 20: 26, 50: 18, 100: 12, 200: 7, 500: 5},
                                self.freegame_type: {10: 32, 20: 26, 50: 18, 100: 12, 200: 7, 500: 5},
                            },
                        },
                    )
                ],
            ),
        ]

        # Prize values (applied when TNT destroys a prize token)
        self.prize_values = {"mni": 10, "maj": 50, "meg": 100, "max": 250}


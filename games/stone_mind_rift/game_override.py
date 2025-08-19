from games.stone_mind_rift.game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome


class GameStateOverride(GameExecutables):
    """Override points for StoneMind Rift special symbols."""

    def reset_book(self):
        super().reset_book()
        self.reset_feature_state()

    def assign_special_sym_function(self):
        # Assign symbol attributes on creation
        self.special_symbol_functions = {
            "M": [self.assign_mult_property],  # multiplier
            "W": [],  # wild has built-in handling via special_symbols
            "B": [self.assign_tnt_property],
            "R": [self.assign_respin_property],
            "mni": [self.assign_prize_property],
            "maj": [self.assign_prize_property],
            "meg": [self.assign_prize_property],
            "max": [self.assign_prize_property],
        }

    def assign_mult_property(self, symbol):
        multiplier_value = get_random_outcome(
            self.get_current_distribution_conditions()["mult_values"][self.gametype]
        )
        symbol.multiplier = multiplier_value

    def assign_tnt_property(self, symbol):
        symbol.tnt = True

    def assign_respin_property(self, symbol):
        symbol.respin = True

    def assign_prize_property(self, symbol):
        symbol.prize = True

    def check_game_repeat(self):
        if self.repeat == False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

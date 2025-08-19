"""Handles the state and output for StoneMind Rift spins."""

from games.stone_mind_rift.game_override import GameStateOverride
from src.calculations.board import Board
from src.calculations.cluster import Cluster


class GameState(GameStateOverride, Board):
    """Game logic: 5 spins, features per spin, cluster tumbles."""

    def run_spin(self, sim):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            # Determine criteria from distribution (super vs normal)
            # criteria already set by simulator; keep as-is

            # Base/Free structure: using freegame to represent the 5-spin portal mode
            if self.get_current_distribution_conditions()["force_freegame"]:
                # Enter 5-spin feature mode
                self.reset_fs_spin()
                self.fs = 0
                self.tot_fs = 5
                self.run_freespin()
            else:
                # Normal single spin with 2 features
                self.gametype = self.config.basegame_type
                self.choose_features_for_spin()
                self.draw_board()
                self._resolve_with_tumbles_and_optional_respin()

            self.evaluate_finalwin()

        self.imprint_wins()

    def run_freespin(self):
        # 5 spins; each spin uses 4 random features
        self.reset_fs_spin()
        self.tot_fs = 5
        while self.fs < self.tot_fs:
            self.update_freespin()
            self.choose_features_for_spin()
            self.draw_board()
            self._resolve_with_tumbles_and_optional_respin()

        self.end_freespin()

    def _resolve_with_tumbles_and_optional_respin(self):
        # Standard tumble cascade
        self.get_clusters_update_wins()
        while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
            self.tumble_game_board()
            self.get_clusters_update_wins()
            self.emit_tumble_win_events()

        # One-time respin: explode all non-special tiles and tumble once
        if hasattr(self, "active_features_this_spin") and "respin" in self.active_features_this_spin:
            # mark all non-special cells for explode
            for r in range(self.config.num_reels):
                for c in range(self.config.num_rows[r]):
                    if not self.board[r][c].special:
                        self.board[r][c].explode = True
            self.tumble_game_board()
            # After respin, allow another cascade chain
            self.get_clusters_update_wins()
            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                self.tumble_game_board()
                self.get_clusters_update_wins()
                self.emit_tumble_win_events()


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
			# Portal near-miss dopamine: emit a portal percent each spin
			import random
			if self.criteria == "super":
				portal_percent = random.uniform(0.90, 1.00)
			else:
				# skew toward near-miss values 0.85-0.89 frequently
				r = random.random()
				if r < 0.35:
					portal_percent = random.uniform(0.85, 0.89)
				elif r < 0.85:
					portal_percent = random.uniform(0.40, 0.84)
				else:
					portal_percent = random.uniform(0.00, 0.39)
			self.emit_portal_event(portal_percent)

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
				# Assign spin wins to basegame and finalize spin total
				self.set_end_tumble_event()
				self.win_manager.update_gametype_wins(self.gametype)

			# align running total with base+free before final accounting
			self.win_manager.running_bet_win = self.win_manager.basegame_wins + self.win_manager.freegame_wins
			
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
			# Assign each FS spin wins to freegame and finalize spin total
			self.set_end_tumble_event()
			self.win_manager.update_gametype_wins(self.gametype)

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

		# Second-chance respin: if dead spin in normal mode and respin not selected, 12% chance
		import random
		if (
			self.criteria == "normal"
			and (self.win_manager.spin_win == 0)
			and (not (hasattr(self, "active_features_this_spin") and "respin" in self.active_features_this_spin))
			and random.random() < 0.12
		):
			for r in range(self.config.num_reels):
				for c in range(self.config.num_rows[r]):
					if not self.board[r][c].special:
						self.board[r][c].explode = True
			self.tumble_game_board()
			self.get_clusters_update_wins()
			while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
				self.tumble_game_board()
				self.get_clusters_update_wins()
				self.emit_tumble_win_events()

		# Tiny consolation wins on dead spins (dopamine) without inflating RTP too much
		if self.win_manager.spin_win == 0:
			if random.random() < 0.08:
				consolation = round(random.uniform(0.05, 0.10), 3)
				# Record as a simple win entry (no positions)
				self.win_data = {
					"totalWin": consolation,
					"wins": [
						{
							"symbol": "CONS",
							"clusterSize": 1,
							"win": consolation,
							"positions": [],
							"meta": {"kind": "consolation", "winWithoutMult": consolation},
						}
					],
				}
				self.win_manager.update_spinwin(consolation)
				# Emit end-of-spin events (not tumble chain)
				if self.win_data["totalWin"] > 0:
					from src.events.events import win_info_event, update_tumble_win_event
					win_info_event(self)
					update_tumble_win_event(self)
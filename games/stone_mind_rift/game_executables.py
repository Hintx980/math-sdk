from games.stone_mind_rift.game_calculations import GameCalculations
from src.calculations.cluster import Cluster
from src.events.events import update_freespin_event


class GameExecutables(GameCalculations):
    """StoneMind Rift grouped helpers."""

    def reset_feature_state(self):
        self.active_features_this_spin = []

    def choose_features_for_spin(self):
        # super: 4 features, normal: 2 features
        import random

        feature_pool = ["wild", "mult", "tnt", "respin", "prize"]
        count = 3 if self.criteria == "super" else 1
        self.active_features_this_spin = random.sample(feature_pool, k=count)

    def get_clusters_update_wins(self):
        wild_key = "wild" if (hasattr(self, "active_features_this_spin") and "wild" in self.active_features_this_spin) else "__no_wild__"
        clusters = Cluster.get_clusters(self.board, wild_key)
        return_data = {"totalWin": 0, "wins": []}
        self.board, self.win_data = self.evaluate_clusters_with_features(
            config=self.config,
            board=self.board,
            clusters=clusters,
            global_multiplier=self.global_multiplier,
            return_data=return_data,
        )

        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    def update_freespin(self) -> None:
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.tumblewin_mult = 0
        self.win_data = {}

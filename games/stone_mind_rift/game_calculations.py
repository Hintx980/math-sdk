from src.executables.executables import Executables
from src.calculations.cluster import Cluster


class GameCalculations(Executables):
    """Implements multipliers, TNT, respin and prize logic layered on clusters."""

    def evaluate_clusters_with_features(
        self,
        config,
        board,
        clusters,
        global_multiplier: int = 1,
        return_data: dict = {"totalWin": 0, "wins": []},
    ):
        exploding_positions = []
        total_win = 0.0

        # First pass: compute base cluster wins with in-cluster multipliers (M) as additive, min 1
        for sym, sym_clusters in clusters.items():
            for cluster in sym_clusters:
                size = len(cluster)
                if (size, sym) not in config.paytable:
                    continue
                # Multipliers only active if the feature is selected this spin
                cluster_mult = 1
                if hasattr(self, "active_features_this_spin") and "mult" in self.active_features_this_spin:
                    cm = 0
                    for pos in cluster:
                        reel, row = pos
                        if hasattr(board[reel][row], "multiplier") and int(getattr(board[reel][row], "multiplier")) > 0:
                            cm += getattr(board[reel][row], "multiplier")
                    cluster_mult = max(cm, 1)
                base_win = config.paytable[(size, sym)]
                win_amount = base_win * cluster_mult * global_multiplier
                total_win += win_amount
                json_positions = [{"reel": p[0], "row": p[1]} for p in cluster]

                central_pos = Cluster.get_central_cluster_position(json_positions)
                return_data["wins"].append(
                    {
                        "symbol": sym,
                        "clusterSize": size,
                        "win": win_amount,
                        "positions": json_positions,
                        "meta": {
                            "globalMult": global_multiplier,
                            "clusterMult": cluster_mult,
                            "winWithoutMult": base_win,
                            "overlay": {"reel": central_pos[0], "row": central_pos[1]},
                        },
                    }
                )
                for pos in cluster:
                    if {"reel": pos[0], "row": pos[1]} not in exploding_positions:
                        exploding_positions.append({"reel": pos[0], "row": pos[1]})
                    board[pos[0]][pos[1]].explode = True

        # TNT: remove 8-neighbourhood around any B that is adjacent (8-way) to any exploding position
        if hasattr(self, "active_features_this_spin") and "tnt" in self.active_features_this_spin:
            to_explode = []
            for reel in range(config.num_reels):
                for row in range(config.num_rows[reel]):
                    sym_obj = board[reel][row]
                    if hasattr(sym_obj, "tnt") and getattr(sym_obj, "tnt"):
                        touching = False
                        for e in exploding_positions:
                            if abs(e["reel"] - reel) <= 1 and abs(e["row"] - row) <= 1 and not (
                                e["reel"] == reel and e["row"] == row
                            ):
                                touching = True
                                break
                        if touching:
                            # explode its neighbourhood but do not remove special features
                            for dr in (-1, 0, 1):
                                for dc in (-1, 0, 1):
                                    nr, nc = reel + dr, row + dc
                                    if 0 <= nr < config.num_reels and 0 <= nc < config.num_rows[nr]:
                                        if nr == reel and nc == row:
                                            # bomb itself
                                            to_explode.append({"reel": nr, "row": nc})
                                        else:
                                            if not board[nr][nc].special:
                                                to_explode.append({"reel": nr, "row": nc})
            # Deduplicate
            unique = []
            for p in to_explode:
                if p not in unique:
                    unique.append(p)
            for p in unique:
                board[p["reel"]][p["row"]].explode = True

        # Prize tokens: award only if destroyed by TNT this evaluation
        if hasattr(self, "active_features_this_spin") and "prize" in self.active_features_this_spin:
            prize_val = 0
            for reel in range(config.num_reels):
                for row in range(config.num_rows[reel]):
                    sym_obj = board[reel][row]
                    if hasattr(sym_obj, "prize") and getattr(sym_obj, "prize"):
                        if getattr(sym_obj, "explode", False):
                            code = sym_obj.name
                            if code in config.prize_values:
                                prize_val += config.prize_values[code]
            if prize_val > 0:
                total_win += prize_val
                return_data["wins"].append(
                    {
                        "symbol": "PRIZE",
                        "clusterSize": 1,
                        "win": prize_val,
                        "positions": [],
                        "meta": {"kind": "tnt_collect"},
                    }
                )

        return_data["totalWin"] += total_win
        return board, return_data

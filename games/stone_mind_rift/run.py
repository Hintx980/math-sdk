"""Run StoneMind Rift to generate configs/books (if enabled)."""

import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from games.stone_mind_rift.gamestate import GameState
from games.stone_mind_rift.game_config import GameConfig
from games.stone_mind_rift.game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":

    num_threads = 6
    rust_threads = 12
    batching_size = 20000
    compression = False
    profiling = False

    num_sim_args = {
        "base": int(2e2),
        "super_buy": int(1e2),
    }

    run_conditions = {
        "run_sims": False,
        "run_optimization": False,
        "run_analysis": False,
        "upload_data": False,
    }
    target_modes = ["base", "super_buy"]

    config = GameConfig()
    gamestate = GameState(config)
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        create_stat_sheet(config.game_id)


from src.config.optimization_paramaters import OptimizationParameters


class OptimizationSetup:
    def __init__(self, config):
        self.config = config
        self.opt_params = OptimizationParameters(
            rtp_target=config.rtp,
            avg_win_target=1.0,
            hit_rate_target=0.3,
            record_conditions=True,
        )


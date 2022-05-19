from typing import Dict, List

import altair as alt
import pandas as pd

from great_expectations.core import ExpectationConfiguration
from great_expectations.rule_based_profiler.types import Domain, ParameterNode
from great_expectations.rule_based_profiler.types.altair import AltairDataTypes
from great_expectations.rule_based_profiler.types.data_assistant_result import (
    DataAssistantResult,
)
from great_expectations.rule_based_profiler.types.data_assistant_result.plot_result import (
    PlotMode,
)


class OnboardingDataAssistantResult(DataAssistantResult):
    def _create_display_chart_for_column_domain_expectation(
        self,
        expectation_configurations: List[ExpectationConfiguration],
        attributed_metrics: Dict[Domain, Dict[str, ParameterNode]],
        plot_mode: PlotMode,
        sequential: bool,
    ) -> List[alt.VConcatChart]:
        column_dfs: List[pd.DataFrame] = self._create_column_dfs_for_charting(
            attributed_metrics=attributed_metrics,
            expectation_configurations=expectation_configurations,
            plot_mode=plot_mode,
        )

        metric_type: alt.StandardType = AltairDataTypes.QUANTITATIVE.value
        metric_name: str = "column_distinct_values_count"

        return self._chart_column_values(
            column_dfs=column_dfs,
            metric_name=metric_name,
            metric_type=metric_type,
            plot_mode=plot_mode,
            sequential=sequential,
        )

from math import ceil
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from time_series_expectations.generator.daily_time_series_generator import (
    DailyTimeSeriesGenerator,
)
from time_series_expectations.generator.time_series_generator import TrendParams


class HourlyTimeSeriesGenerator(DailyTimeSeriesGenerator):
    """Generate an hourly time series with trend, seasonality, and outliers."""

    def _generate_hourly_seasonality(
        self,
        time_range: np.ndarray,
        hourly_seasonality_params: List[Tuple[float, float]],
    ) -> np.ndarray:
        """Generate an annual seasonality component for a time series."""

        return sum(
            [
                alpha * np.cos(2 * np.pi * (i + 1) * time_range / 24)
                + beta * np.sin(2 * np.pi * (i + 1) * time_range / 24)
                for i, (alpha, beta) in enumerate(hourly_seasonality_params)
            ]
        )

    def _generate_hourly_time_series(
        self,
        size: int,
        hourly_seasonality: float,
        hourly_seasonality_params: Optional[List[Tuple[float, float]]] = None,
        trend_params: Optional[List[TrendParams]] = None,
        weekday_dummy_params: Optional[List[float]] = None,
        annual_seasonality_params: Optional[List[Tuple[float, float]]] = None,
        holiday_alpha: float = 3.5,
        outlier_alpha: float = 2.5,
        noise_scale: float = 1.0,
    ):
        """Generate an hourly time series."""
        if hourly_seasonality_params is None:
            # Create 10 random hourly seasonality parameters
            hourly_seasonality_params = [
                (
                    np.random.normal() / 100,
                    np.random.normal() / 100,
                )
                for i in range(4)
            ]

        time_range = np.arange(size)

        hourly_seasonality_series = self._generate_hourly_seasonality(
            time_range=time_range,
            hourly_seasonality_params=hourly_seasonality_params,
        ) * hourly_seasonality

        hourly_outliers = self._generate_posneg_pareto(outlier_alpha, size)

        daily_time_series = self._generate_daily_time_series(
            size=ceil(size / 24),
            trend_params=trend_params,
            weekday_dummy_params=weekday_dummy_params,
            annual_seasonality_params=annual_seasonality_params,
            holiday_alpha=holiday_alpha,
            outlier_alpha=1000000,#outlier_alpha,
            noise_scale=noise_scale,
        )
        return np.exp(hourly_seasonality_series) * np.repeat(daily_time_series, 24)[:size] + hourly_outliers

    def generate_df(
        self,
        size: Optional[int] = 90 * 24,  # 90 days worth of data
        start_date: Optional[str] = "2018-01-01",
        hourly_seasonality: float = 1.0,
        hourly_seasonality_params: Optional[List[Tuple[float, float]]] = None,
        trend_params: Optional[List[TrendParams]] = None,
        weekday_dummy_params: Optional[List[float]] = None,
        annual_seasonality_params: Optional[List[Tuple[float, float]]] = None,
        holiday_alpha: float = 3.5,
        outlier_alpha: float = 2.5,
        noise_scale: float = 1.0,
    ) -> pd.DataFrame:
        """Generate a time series as a pandas dataframe.

        Keyword Args:
            size: The number of days in the time series.
            start_date: The start date of the time series.
            trend_params: A list of trend parameters corresponding to cutpoints in the time series.
            weekday_dummy_params: A list of weekday dummy parameters. Should be a list of length 7, with each day corresponding to the average difference in the time series on that day.
            annual_seasonality_params: A list of annual seasonality parameters used to create a cyclic component in the time series.
            holiday_alpha: The alpha parameter for the pareto distribution used to generate holiday effects.
            outlier_alpha: The alpha parameter for the pareto distribution used to generate outlier effects.
            noise_scale: The scale parameter for the standard deviation of the normal distribution used to generate noise.

        Returns:
            A pandas dataframe with a date column and a time series column.

        Notes:
            * Holiday and outlier effects are generated using a pareto distribution. The alpha parameter controls the shape of the distribution. A higher alpha value will result in more extreme holiday and outlier effects.
            * Holidays don't correspond to actual holidays. Instead, they are generated by randomly selecting days in the time series.
            * Annual seasonality is generated by Fourier series. The number of fourier terms is determined by the length of the annual_seasonality_params list. The first element of each tuple in the list is the amplitude of the sine term, and the second element is the amplitude of the cosine term.
        """

        return pd.DataFrame(
            {
                "ds": pd.date_range(start_date, periods=size, freq="60min"),
                "y": self._generate_hourly_time_series(
                    size=size,
                    hourly_seasonality=hourly_seasonality,
                    hourly_seasonality_params=hourly_seasonality_params,
                    trend_params=trend_params,
                    weekday_dummy_params=weekday_dummy_params,
                    annual_seasonality_params=annual_seasonality_params,
                    holiday_alpha=holiday_alpha,
                    outlier_alpha=outlier_alpha,
                    noise_scale=noise_scale,
                ),
            }
        )

from dataclasses import dataclass
from typing import List, Optional, Union

import altair as alt


@dataclass(frozen=True)
class PlotComponent:
    name: str
    alt_type: alt.StandardType

    @property
    def title(self) -> str:
        return self.name.replace("_", " ").title()

    def generate_tooltip(self, format: str = "") -> alt.Tooltip:
        """Wrapper around alt.Tooltip creation.

        Args:
            format (str): Desired format within tooltip

        Returns:
            An instance of alt.Tooltip containing relevant information from the PlotComponent class.
        """
        return alt.Tooltip(
            field=self.name,
            type=self.alt_type,
            title=self.title,
            format=format,
        )

    def plot_on_axis(self) -> Union[alt.X, alt.Y]:
        """Wrapper around alt.X/alt.Y plotting utility.

        Returns:
            Either an alt.X or alt.Y instance based on desired axis.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class MetricPlotComponent(PlotComponent):
    def plot_on_axis(self) -> alt.Y:
        """
        Plots metric on Y axis - see parent `PlotComponent` for more details.
        """
        return alt.Y(
            self.name,
            type=self.alt_type,
            title=self.title,
        )


@dataclass(frozen=True)
class DomainPlotComponent(PlotComponent):
    subtitle: Optional[str] = None

    @property
    def title(self) -> str:
        return self.name.title()

    def plot_on_axis(self) -> alt.X:
        """
        Plots domain on X axis - see parent `PlotComponent` for more details.
        """
        return alt.X(
            self.name,
            type=self.alt_type,
            title=self.title,
        )


@dataclass(frozen=True)
class BatchPlotComponent:
    batch_identifiers: List[str]
    alt_type: alt.StandardType

    @property
    def titles(self) -> List[str]:
        return [
            batch_identifier.replace("_", " ").title().replace("Id", "ID")
            for batch_identifier in self.batch_identifiers
        ]

    def generate_tooltip(self, format: str = "") -> List[alt.Tooltip]:
        """Wrapper around alt.Tooltip creation.

        Args:
            format (str): Desired format within tooltip

        Returns:
            A list of instances of alt.Tooltip containing relevant information from the BatchPlotComponent class.
        """
        tooltip: List = []
        for idx, batch_identifier in enumerate(self.batch_identifiers):
            tooltip.append(
                alt.Tooltip(
                    field=batch_identifier,
                    type=self.alt_type,
                    title=self.titles[idx],
                    format=format,
                )
            )
        return tooltip


@dataclass(frozen=True)
class ExpectationKwargPlotComponent(PlotComponent):
    metric_plot_component: MetricPlotComponent

    def plot_on_axis(self) -> alt.Y:
        """
        Plots domain on Y axis - see parent `PlotComponent` for more details.
        """
        return alt.Y(
            self.name,
            type=self.metric_plot_component.alt_type,
            title=self.metric_plot_component.title,
        )


def determine_plot_title(
    metric_plot_component: MetricPlotComponent,
    domain_plot_component: DomainPlotComponent,
) -> alt.TitleParams:
    """Determines the appropriate title for a chart based on input componentsself.

    Conditionally renders a subtitle if relevant (specifically with column domain)

    Args:
        metric_plot_component: Plot utility corresponding to a given metric.
        domain_plot_component: Plot utility corresponding to a given domain.

    Returns:
        An Altair TitleParam object

    """
    contents: str = f"{metric_plot_component.title} per {domain_plot_component.title}"
    subtitle: Optional[str] = domain_plot_component.subtitle

    title: alt.TitleParams
    if subtitle:
        title = alt.TitleParams(contents, subtitle=[subtitle])
    else:
        title = alt.TitleParams(contents)

    return title

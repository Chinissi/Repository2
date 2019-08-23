import os
import sys
import traceback
from typing import List

from pyspark.ml.base import Transformer
from pyspark.ml.pipeline import (
    Pipeline,
    PipelineModel
)
from pyspark.sql import (
    DataFrame,
    SparkSession
)
from pyspark.sql.types import (
    FloatType
)
from pyspark.sql.functions import (
    col,
    when,
    lit
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from common.utils import (
    ge_tap
)


class TitanicCsvPipeline:
    """
    Pipeline for the "Titanic CSV" example.
    """

    def __init__(self, spark_session: SparkSession):
        super(TitanicCsvPipeline, self).__init__()

        self.spark_session = spark_session

        self.stages = self._gather_processing_stages()

    def _gather_processing_stages(self) -> List[Transformer]:
        remove_age_na_rows_transformer: Transformer = RemoveAgeNARowsTransformer(
            spark_session=self.spark_session
        )
        convert_age_to_float_transformer: Transformer = ConvertAgeToFloatTransformer(
            spark_session=self.spark_session
        )
        categorize_life_stage_by_age_transformer: Transformer = CategorizeLifeStageByAgeTransformer(
            spark_session=self.spark_session
        )

        stages: List[Transformer] = [
            remove_age_na_rows_transformer,
            convert_age_to_float_transformer,
            categorize_life_stage_by_age_transformer
        ]

        return stages

    def run(self, df: DataFrame) -> DataFrame:
        """
        :param df:
        """
        stages: List = self.stages
        if stages and len(stages) > 0:
            pipeline_obj: Pipeline = Pipeline(stages=stages)
            df_res: DataFrame = pipeline_obj.fit(df).transform(df)
            return df_res
        else:
            return df


class RemoveAgeNARowsTransformer(Transformer):
    """
    Removes rows in which the value of the "Age" column is not available.
    """

    def __init__(self, spark_session: SparkSession):
        super(RemoveAgeNARowsTransformer, self).__init__()

        self.spark_session = spark_session

    def _transform(self, df: DataFrame) -> DataFrame:
        df_res: DataFrame = df.filter(col("Age") != "NA")
        return df_res


class ConvertAgeToFloatTransformer(Transformer):
    """
    Converts the value of the "Age" column to a floating point type.
    """

    def __init__(self, spark_session: SparkSession):
        super(ConvertAgeToFloatTransformer, self).__init__()

        self.spark_session = spark_session

    def _transform(self, df: DataFrame) -> DataFrame:
        df_res: DataFrame = df.withColumn("age_as_float", df["Age"].cast(FloatType()))
        return df_res


class CategorizeLifeStageByAgeTransformer(Transformer):
    """
    Categorizes life stage by "age_as_float" column.
    """

    def __init__(self, spark_session: SparkSession):
        super(CategorizeLifeStageByAgeTransformer, self).__init__()

        self.spark_session = spark_session

    def _transform(self, df: DataFrame) -> DataFrame:
        df_res: DataFrame = df.withColumn(
            "life_stage",
            when(
                df["age_as_float"] < 18.0, "child"
            ).otherwise(
                when(
                    df["age_as_float"] >= 65.0, "senior"
                ).otherwise("adult")
            )
        )
        return df_res


class ValidationTransformer(Transformer):
    """
    Wraps Great Expectations Data Tap API Call
    """

    def __init__(self, data_asset_name: str, spark_session: SparkSession):
        super(ValidationTransformer, self).__init__()

        self.data_asset_name = data_asset_name
        self.spark_session = spark_session

    def _transform(self, df: DataFrame) -> DataFrame:
        df_res: DataFrame = df.withColumn(
            "life_stage",
            when(
                df["age_as_float"] < 18.0, "child"
            ).otherwise(
                when(
                    df["age_as_float"] >= 65.0, "senior"
                ).otherwise("adult")
            )
        )
        return df_res

---
title: How to add Spark support for custom Metrics
---
import Prerequisites from '../../connecting_to_your_data/components/prerequisites.jsx'
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

:::warning
This guide only applies to Great Expectations versions 0.13 and above, which make use of the new modular Expectation architecture. If you have implemented a custom Expectation but have not yet migrated it using the new modular patterns, you can still use this guide to implement custom renderers for your Expectation.
:::

This guide will help you implement native Spark support for your custom Metric. 

<Prerequisites>

- [Set up a working deployment of Great Expectations](../../../tutorials/getting_started/intro.md)
- Configured a [Data Context](../../../tutorials/getting_started/initialize_a_data_context.md).
- Implemented a [custom Expectation](../../../guides/expectations/creating_custom_expectations/how_to_create_custom_column_aggregate_expectations.md).
    
</Prerequisites>

Steps
-----

Similarly to the SQLAlchemy case, there are several ways we can implement our Expectation's logic in PySpark, such as: 
1.  Defining a partial function that takes a PySpark DataFrame column as input
2.  Directly executing queries on PySpark DataFrames to determine the value of your Expectation's metric directly 
3.  Using an existing metric that is already defined for PySpark. 

<Tabs
  groupId="-type"
  defaultValue='columnmap'
  values={[
  {label: 'Partial Function', value:'partialfunction'},
  {label: 'Query Execution', value:'queryexecution'},
  {label: 'Existing Metric', value:'existingmetric'},
  ]}>

<TabItem value="partialfunction">
Great Expectations allows for much of the PySpark DataFrame logic to be abstracted away by specifying metric behavior as a partial function. To do this, use one of the decorators `@column_aggregate_partial` (for column aggregate expectation) , `@column_condition_partial` (for column map expectations), ` `@column_pair_condition_partial` (for column pair map metrics), or `@multicolumn_condition_partial` for multicolumn map metrics`. The decorated method takes in an SQLAlchemy `Column` object and will either return a `sqlalchemy.sql.functions.Function` or a `ColumnOperator` that Great Expectations will use to generate the appropriate SQL queries. 


For example, the `ColumnValuesEqualThree` metric can be defined as: 

```python
def _spark(cls, column, **kwargs):
    return column.isin([3])
```
    
If we need a builtin function from `pyspark.sql.functions`, usually aliased to F, the import logic in 
`from great_expectations.expectations.metrics.import_manager import F`
handles the case when PySpark is not installed. 

`F.udf` also allows us to apply a Python function as a Spark UDF, so another way of expressing the above is as: 

```python
@column_condition_partial(engine=SparkDFExecutionEngine)
def _spark(cls, column, strftime_format, **kwargs):
    def is_equal_to_three(val):
        return (val == 3)

    success_udf = F.udf(is_equal_to_three, sparktypes.BooleanType())
    return success_udf(column)
```
    
Or, for example, a column aggregate metric that returns the maximum value could be written as: 
```python
@column_aggregate_partial(engine=SparkDFExecutionEngine)
def _spark(cls, column, **kwargs):
    return F.max(column)
```    
   
</TabItem> 
    
<TabItem value="queryexecution">
The most direct way of implementing a metric is by computing its value from provided PySpark objects. 
        
```python
 @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: "SqlAlchemyExecutionEngine",
        metric_domain_kwargs: Dict,
        metric_value_kwargs: Dict,
        metrics: Dict[Tuple, Any],
        runtime_configuration: Dict,
    ):
        (
            df,
            compute_domain_kwargs,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(
            metric_domain_kwargs, domain_type=MetricDomainTypes.COLUMN
        )
        column = accessor_domain_kwargs["column"]

        return df.where(F.col(column) % 3 == 0).count()
```
    
Here df is a PySpark DataFrame, for which we want to compute the metric value for the column `column`.
    
For example, to count the number of values in the column divisible by 3, 
    
```python
    return df.where(F.col(column) % 3 == 0).count()
```
</TabItem> 
    
<TabItem value="existingmetric">\
When using the value of an existing metric, the method signature is the same as when defining a metric value. 
```python
    @metric_value(engine=SparkDFExecutionEngine, metric_fn_type="value")
    def _spark(
        cls,
        execution_engine: "SparkDFExecutionEngine",
        metric_domain_kwargs: Dict,
        metric_value_kwargs: Dict,
        metrics: Dict[Tuple, Any],
        runtime_configuration: Dict,
    ):
```    
    
The `metrics` argument that the method is called with will be populated with your metric's dependencies, resolved by calling the `_get_evaluation_dependencies` class method. Suppose we wanted to implement a version of the `ColumnValuesEqualThree` expectation using the `column.value_counts` metric, which is already implemented for the PySpark execution engine. We would then modify `_get_evaluation_dependencies` as follows: 
    
```python 
    @classmethod
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):

        dependencies = super()._get_evaluation_dependencies(
            metric=metric,
            configuration=configuration,
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )

        if isinstance(execution_engine, SparkExecutionEngine):
            dependencies["column.value_counts"] = MetricConfiguration(
                metric_name="column.value_counts",
                metric_domain_kwargs=metric.metric_domain_kwargs,
            )
        return dependencies    
```
Then within the `_spark` function, we would add: 

```python
    column_value_counts = metrics.get("column.value_counts")
    return(all(column_value_counts.index==3))
```
</TabItem>
</Tabs>

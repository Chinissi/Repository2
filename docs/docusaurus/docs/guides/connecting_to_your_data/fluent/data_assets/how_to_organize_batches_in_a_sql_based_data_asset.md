---
title: How to organize Batches in a SQL-based Data Asset
tag: [how-to, connect to data]
description: A technical guide demonstrating how to split the data returned by a SQL Data Asset into multiple Batches and explicitly sort those Batches.
keywords: [Great Expectations, Data Asset, Batch Request, fluent configuration method, SQL]
---

import TechnicalTag from '/docs/term_tags/_tag.mdx';


<!-- ## Introduction -->

<!-- ## Prerequisites -->
import Prerequisites from '/docs/components/_prerequisites.jsx'
import SetupAndInstallForSqlData from '/docs/components/setup/link_lists/_setup_and_install_for_sql_data.md'
import ConnectingToSqlDatasourcesFluently from '/docs/components/connect_to_data/link_lists/_connecting_to_sql_datasources_fluently.md'
import ConnectingToSqlDatasourcesBlockConfig from '/docs/components/connect_to_data/link_lists/_connecting_to_sql_datasources_block_config.md'

<!-- ### Import GX and instantiate a Data Context -->
import ImportGxAndInstantiateADataContext from '/docs/components/setup/data_context/_import_gx_and_instantiate_a_data_context.md'

<!-- ### 1. Create a `batching_regex` -->
import TipFilesystemDatasourceNestedSourceDataFolders from '/docs/components/connect_to_data/filesystem/_tip_filesystem_datasource_nested_source_data_folders.md'

<!-- ## Next steps -->
import AfterCreateAndConfigureDataAsset from '/docs/components/connect_to_data/next_steps/_after_create_and_configure_data_asset.md'

## Introduction

In this guide we will demonstrate the ways in which Batches can be organized in a SQL-based Data Asset.  We will discuss how to use Splitters to divide the data in a table or query based on the contents of a provided field.  We will also show how to add Batch Sorters to a Data Asset in order to specify the order in which Batches are returned.

## Prerequisites

<Prerequisites>

- A working installation of Great Expectations
- A Data Asset in a SQL-based Datasource
- A passion for data quality

</Prerequisites>


<details>
<summary>

### If you still need to set up and install GX...

</summary>

Please reference the appropriate one of these guides:

<SetupAndInstallForSqlData />

</details>

<details>
<summary>

### If you still need to connect a Datasource to a SQL database...

</summary>

Please reference the appropriate one of these guides:

<ConnectingToSqlDatasourcesFluently />

Or, for guides on using the block-config method for advanced SQL Datasource configurations, please see:

<ConnectingToSqlDatasourcesBlockConfig />


</details>


## Steps

### 1. Import GX and instantiate a Data Context

<ImportGxAndInstantiateADataContext />

### 1. Retrieve a SQL Datasource and Data Asset

For this guide, we will use a previously defined Datasource named `"MyDatasource"`.  For purposes of our demonstration, this Datasource is a Pandas Filesystem Datasource that uses a folder named "data" as its `base_folder`.

To retrieve this Datasource, we will supply the `get_datasource(...)` method of our Data Context with the name of the Datasource we wish to retrieve:

```python title="Python code"
my_datasource = context.get_datasource("MyDatasource")
```

### 2. Add a Splitter to the Data Asset

```python title="Python code"
table_asset.add_year_and_month_splitter(column_name="pickup_datetime")
```

### 3. (Optional) Add Batch Sorters to the Data Asset

We will now add a Batch Sorter to our Data Asset.  This will allow us to explicitly state the order in which our Batches are returned when we request data from the Data Asset.  To do this, we will pass a list of sorters to the `add_sorters(...)` method of our Data Asset.

The items in our list of sorters will correspond to the names of the groups in our `batching_regex` that we want to sort our Batches on.  The names are prefixed with a `+` or a `-` depending on if we want to sort our Batches in ascending or descending order based on the given group.

If there were multiple named groups we could include multiple items in our sorter list and our Batches would be returned in the order specified by the list: sorted first according to the first item, then the second, and so forth.

However, in this example we only have one named group, `"year"`, so our list of sorters will only have one element.  We will add an ascending sorter based on the contents of the regex group `"year"`:

```python title="Python code"
my_asset.add_sorters(["+year"])
```

### 4. Use a Batch Request to verify the Data Asset works as desired

To verify that our Data Asset will return the desired files as Batches, we will define a quick Batch Request that will include all the Batches available in the Data asset.  Then we will use that Batch Request to get a list of the returned Batches.

```python title="Python code"
my_batch_request = my_asset.my_asset.build_batch_request()
batches = datasource.get_batch_list_from_batch_request(my_batch_request)
```

Because a Batch List contains a lot of metadata, it will be easiest to verify which files were included in the returned Batches if we only look at the `batch_spec` of each returned Batch:

```python title="Python code"
for batch in batches:
    print(batch.batch_spec)
```

## Next steps

Now that you have further configured a Data Asset, you may want to look into:

### Requesting Data from a Data Asset
- [How to request data from a Data Asset](/docs/guides/connecting_to_your_data/fluent/batch_requests/how_to_request_data_from_a_data_asset.md)

### Using Data Assets to create Expectations
- [Use a Data Asset to create Expectations while interactively evaluating a set of data](/docs/guides/expectations/how_to_create_and_edit_expectations_with_instant_feedback_from_a_sample_batch_of_data.md)
- [Use the Onboarding Data Assistant to evaluate one or more Batches of data and create Expectations](/docs/guides/expectations/data_assistants/how_to_create_an_expectation_suite_with_the_onboarding_data_assistant.md)
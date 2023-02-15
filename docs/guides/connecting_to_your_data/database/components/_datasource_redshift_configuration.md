import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs
  groupId="yaml-or-python"
  defaultValue='yaml'
  values={[
  {label: 'YAML', value:'yaml'},
  {label: 'Python', value:'python'},
  ]}>

<TabItem value="yaml">

Put your connection string in this template:

```python file=../../../../../tests/integration/docusaurus/connecting_to_your_data/database/redshift_yaml_example.py#L28-L42
```

Run this code to test your configuration.

```python file=../../../../../tests/integration/docusaurus/connecting_to_your_data/database/redshift_yaml_example.py#L51
```

</TabItem>

<TabItem value="python">

Put your connection string in this template:

```python file=../../../../../tests/integration/docusaurus/connecting_to_your_data/database/redshift_python_example.py#L28-L45
```

Run this code to test your configuration.

```python file=../../../../../tests/integration/docusaurus/connecting_to_your_data/database/redshift_python_example.py#L51
```

</TabItem>

</Tabs>

You will see your database tables listed as `Available data_asset_names` in the output of `test_yaml_config()`.

Feel free to adjust your configuration and re-run `test_yaml_config` as needed.
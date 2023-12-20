<details>
<summary>

#### Getting a Data Context

</summary>

**Quickstart Data Context**
- [Instantiate a Data Context](/docs/oss/guides/setup/configuring_data_contexts/instantiating_data_contexts/instantiate_data_context)

**Filesystem Data Contexts**
- [How to initialize a filesystem Data Context in Python](/docs/oss/guides/setup/configuring_data_contexts/instantiating_data_contexts/instantiate_data_context)
- [How to instantiate a specific Filesystem Data Context](/docs/oss/guides/setup/configuring_data_contexts/instantiating_data_contexts/instantiate_data_context)

**In-memory Data Contexts**
- [How to instantiate an Ephemeral Data Context](/docs/oss/guides/setup/configuring_data_contexts/instantiating_data_contexts/instantiate_data_context)

</details>

<details>
<summary>

#### Saving a Data Context

</summary>

Filesystem and Cloud Data Contexts automatically save any changes as they are made.  The only type of Data Context that does not immediately save changes in a persisting way is the Ephemeral Data Context, which is an in-memory Data Context that will not persist beyond the current Python session.  However, an Ephemeral Data Context can be converted to a Filesystem Data Context if you wish to save its contents for future use.

For more information, please see:
- [How to convert an Ephemeral Data Context to a Filesystem Data Context](/docs/oss/guides/setup/configuring_data_contexts/how_to_convert_an_ephemeral_data_context_to_a_filesystem_data_context)

</details>
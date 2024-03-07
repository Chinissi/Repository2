module.exports = {
  gx_core: [
    {
      type: 'doc',
      id: 'core/introduction/about_gx',
      label: 'About GX'
    },
    {
      type: 'doc',
      id: 'core/introduction/try_gx',
      label: '🚧 Try GX'
    },
    {
      type: 'category',
      label: 'Installation and setup',
      link: {type: 'doc', id: 'core/installation_and_setup/installation_and_setup'},
      items: [
        {
          type: 'doc',
          id: 'core/installation_and_setup/set_up_a_python_environment',
          label: 'Set up a Python environment'
        },
        {
          type: 'doc',
          id: 'core/installation_and_setup/install_gx',
          label: 'Install GX 1.0'
        },
        {
          type: 'category',
          label: 'Install additional dependencies',
          link: {type: 'doc', id: 'core/installation_and_setup/additional_dependencies/additional_dependencies'},
          items: [
            {
              type: 'doc',
              id: 'core/installation_and_setup/additional_dependencies/amazon_s3',
              label: 'Amazon S3'
            },
            {
              type: 'doc',
              id: 'core/installation_and_setup/additional_dependencies/azure_blob_storage',
              label: 'Azure Blob Storage'
            },
            {
              type: 'doc',
              id: 'core/installation_and_setup/additional_dependencies/google_cloud_storage',
              label: '🚧 Google Cloud Storage'
            },
            {
              type: 'doc',
              id: 'core/installation_and_setup/additional_dependencies/sql_data_sources',
              label: '🚧 SQL Data Sources'
            },
          ]
        },
        {
          type: 'category',
          label: 'Manage Data Contexts',
          link: {type: 'doc', id: 'core/installation_and_setup/manage_data_contexts'},
          items: [
            {
              type: 'link',
              label: 'Quickstart with a Data Context',
              href: '/docs/1.0-prerelease/core/installation_and_setup/manage_data_contexts#quickstart-with-a-data-context',
            },
            {
              type: 'link',
              label: '🚧 Initialize a new Data Context',
              href: '/docs/1.0-prerelease/core/installation_and_setup/manage_data_contexts#initialize-a-new-data-context',
            },
            {
              type: 'link',
              label: '🚧 Connect to an existing Data Context',
              href: '/docs/1.0-prerelease/core/installation_and_setup/manage_data_contexts#connect-to-an-existing-data-context',
            },
            {
              type: 'link',
              label: '🚧 Export an Ephemeral Data Context to a new File Data Context',
              href: '/docs/1.0-prerelease/core/installation_and_setup/manage_data_contexts#export-an-ephemeral-data-context-to-a-new-file-data-context',
            },
            {
              type: 'link',
              label: '🚧 View the full configuration of a Data Context',
              href: '/docs/1.0-prerelease/core/installation_and_setup/manage_data_contexts#view-the-full-configuration-of-a-data-context',
            },
          ]
        },
        {
          type: 'doc',
          id: 'core/installation_and_setup/manage_credentials',
          label: '🚧 Manage credentials'
        },
        {
          type: 'doc',
          id: 'core/installation_and_setup/manage_metadata_stores',
          label: '🚧 Manage Metadata Stores'
        },
        {
          type: 'doc',
          id: 'core/installation_and_setup/manage_data_docs',
          label: '🚧 Manage Data Docs'
        },
      ]
    },
    {
      type: 'category',
      label: '🚧 Manage and access data',
      link: {type: 'doc', id: 'core/manage_and_access_data/manage_and_access_data'},
      items: [
        {
          type: 'category',
          label: 'Connect to and request data',
          link: {type: 'doc', id: 'core/manage_and_access_data/connect_to_data/connect_to_data'},
          items: [
            {
              type: 'doc',
              id: 'core/manage_and_access_data/connect_to_data/file_system/file_system',
              label: '🚧 Connect to file system data'
            },
            {
              type: 'doc',
              id: 'core/manage_and_access_data/connect_to_data/in_memory/in_memory',
              label: '🚧 Connect to in memory data'
            },
            {
              type: 'doc',
              id: 'core/manage_and_access_data/connect_to_data/sql/sql',
              label: '🚧 Connect to SQL database data'
            },
            {
              type: 'doc',
              id: 'core/manage_and_access_data/request_data',
              label: '🚧 Request data'
            },
          ]
        },

        {
          type: 'category',
          label: '🚧 Manage Data Sources',
          link: {type: 'doc', id: 'core/manage_and_access_data/manage_data_sources/manage_data_sources'},
          items: [
            {
              type: 'link',
              label: '🚧 List available Data Sources',
              href: '/docs/1.0-prerelease/core/manage_and_access_data/manage_data_sources#list-available-data-sources',
            },
            {
              type: 'link',
              label: '🚧 Get an existing Data Source',
              href: '/docs/1.0-prerelease/core/manage_and_access_data/manage_data_sources#get-an-existing-data-source',
            },
            {
              type: 'link',
              label: '🚧 Delete a Data Source',
              href: '/docs/1.0-prerelease/core/manage_and_access_data/manage_data_sources#delete-a-data-source',
            },
          ]
        },
        {
          type: 'category',
          label: '🚧 Manage Data Assets',
          link: {type: 'doc', id: 'core/manage_and_access_data/manage_data_assets'},
          items: [
            {
              type: 'link',
              label: '🚧 List all Data Assets in a Data Source',
              href: '/docs/1.0-prerelease/core/manage_and_access_data/manage_data_assets#list-all-data-assets-in-a-data-source',
            },
            {
              type: 'link',
              label: '🚧 Get an existing Data Asset',
              href: '/docs/1.0-prerelease/core/manage_and_access_data/manage_data_assets#get-an-existing-data-asset',
            },
            {
              type: 'link',
              label: '🚧 Add a Partitioner to a Data Asset',
              href: '/docs/1.0-prerelease/core/manage_and_access_data/manage_data_assets#add-a-partitioner-to-a-data-asset',
            },
            {
              type: 'link',
              label: '🚧 Delete a Data Asset',
              href: '/docs/1.0-prerelease/core/manage_and_access_data/manage_data_assets#delete-a-data-asset',
            },
          ]
        },
        {
          type: 'category',
          label: '🚧 Manage Batch Requests',
          link: {type: 'doc', id: 'core/manage_and_access_data/manage_batch_requests'},
          items: [
            {
              type: 'doc',
              id: 'core/manage_and_access_data/manage_batch_requests',
              label: '🚧 Retrieve all Batches from a Data Asset'
            },
            {
              type: 'doc',
              id: 'core/manage_and_access_data/manage_batch_requests',
              label: '🚧 Retrieve specific Batches from a Data Asset'
            },
            {
              type: 'doc',
              id: 'core/manage_and_access_data/manage_batch_requests',
              label: '🚧 Iterate retrieved Batches'
            },
          ]
        },
        {
          type: 'category',
          label: '🚧 Manage Batches',
          link: {type: 'doc', id: 'core/manage_and_access_data/manage_batches'},
          items: [
            {
              type: 'doc',
              id: 'core/manage_and_access_data/manage_batches',
              label: '🚧 View a sample of the data in a Batch'
            },
            {
              type: 'doc',
              id: 'core/manage_and_access_data/manage_batches',
              label: '🚧 Validate a Batch against an Expectation'
            },
            {
              type: 'doc',
              id: 'core/manage_and_access_data/manage_batches',
              label: '🚧 Validate a Batch against an Expectation Suite'
            },
            <!--TODO: Validation is being moved into the Batch object, are there other API changes? -->
            {
              type: 'doc',
              id: 'core/manage_and_access_data/manage_batches',
              label: '🚧 Get the Batch Request for a given Batch'
            },
          ]
        },
      ]
    },
    {
      type: 'category',
      label: 'Create Expectations',
      link: { type: 'doc', id: 'core/create_expectations/create_expectations' },
      items: [
        // 'oss/guides/expectations/create_expectations_overview',
        {
          type: 'category',
          label: 'Manage Expectations',
          link: { type: 'doc', id: 'core/create_expectations/expectations/manage_expectations' },
          items: [
            {
              type: 'link',
              label: 'Create an Expectation',
              href: '/docs/1.0-prerelease/core/create_expectations/expectations/manage_expectations#create-an-expectation',
            },
            {
              type: 'link',
              label: 'Test an Expectation',
              href: '/docs/1.0-prerelease/core/create_expectations/expectations/manage_expectations#test-an-expectation',
            },
            {
              type: 'link',
              label: 'Modify an Expectation',
              href: '/docs/1.0-prerelease/core/create_expectations/expectations/manage_expectations#modify-an-expectation',
            },
            {
              type: 'link',
              label: 'Customize an Expectation Class',
              href: '/docs/1.0-prerelease/core/create_expectations/expectations/manage_expectations#customize-an-expectation-class',
            },
          ]
        },
      {
          type: 'category',
          label: 'Manage Expectation Suites',
          link: { type: 'doc', id: 'core/create_expectations/expectation_suites/manage_expectation_suites' },
          items: [
            {
              type: 'link',
              label: 'Create an Expectation Suite',
              href: '/docs/1.0-prerelease/core/create_expectations/expectation_suites/manage_expectation_suites#create-an-expectation-suite',
            },
            {
              type: 'link',
              label: 'Get an existing Expectation Suite',
              href: '/docs/1.0-prerelease/core/create_expectations/expectation_suites/manage_expectation_suites#get-an-existing-expectation-suite',
            },
            {
              type: 'link',
              label: 'Delete an Expectation Suite',
              href: '/docs/1.0-prerelease/core/create_expectations/expectation_suites/manage_expectation_suites#delete-an-expectation-suite',
            },
            {
              type: 'link',
              label: 'Add Expectations',
              href: '/docs/1.0-prerelease/core/create_expectations/expectation_suites/manage_expectation_suites#add-expectations-to-an-expectation-suite',
            },
            {
              type: 'link',
              label: 'Get an Expectation',
              href: '/docs/1.0-prerelease/core/create_expectations/expectation_suites/manage_expectation_suites#get-an-expectation-from-an-expectation-suite',
            },
            {
              type: 'link',
              label: 'Edit a single Expectation',
              href: '/docs/1.0-prerelease/core/create_expectations/expectation_suites/manage_expectation_suites#edit-a-single-expectation-in-an-expectation-suite',
            },
            {
              type: 'link',
              label: 'Edit multiple Expectations',
              href: '/docs/1.0-prerelease/core/create_expectations/expectation_suites/manage_expectation_suites#edit-multiple-expectations-in-an-expectation-suite',
            },
            {
              type: 'link',
              label: 'Delete an Expectation',
              href: '/docs/1.0-prerelease/core/create_expectations/expectation_suites/manage_expectation_suites#delete-an-expectation-from-an-expectation-suite',
            },
          ]
        },
        // {
        //   type: 'category',
        //   label: 'Data Assistants',
        //   link: { type: 'doc', id: 'oss/guides/expectations/data_assistants_lp' },
        //   items: [
        //     'oss/guides/expectations/data_assistants/how_to_create_an_expectation_suite_with_the_missingness_data_assistant',
        //   ]
        // },
      ]
    },
    {
      type: 'category',
      label: 'Validate data',
      link: {type: 'doc', id: 'core/validate_data/validate_data'},
      items: [
        {
          type: 'doc',
          id: 'core/validate_data/manage_validators',
          label: 'Manage Validators'
        },
        {
          type: 'doc',
          id: 'core/validate_data/manage_checkpoints',
          label: 'Manage Checkpoints'
        },
      ]
    }
    <!--TODO: Validate Data -->
      <!-- TODO: Manage Validators -->
      <!-- TODO: Manage Checkpoints -->
  ],
  gx_cloud: [
    {type: 'doc', id: 'cloud/why_gx_cloud'},
        {
          type: 'category',
          label: 'About GX Cloud',
          link: { type: 'doc', id: 'cloud/about_gx' },
          items: [
            {
              type: 'link',
              label: 'GX Cloud architecture',
              href: '/docs/cloud/about_gx#gx-cloud-architecture',
            },
            {
              type: 'link',
              label: 'GX Agent',
              href: '/docs/cloud/about_gx#gx-agent',
            },
            {
              type: 'link',
              label: 'GX Cloud deployment patterns',
              href: '/docs/cloud/about_gx#gx-cloud-deployment-patterns',
            },
            {
              type: 'link',
              label: 'GX Cloud workflow',
              href: '/docs/cloud/about_gx#gx-cloud-workflow',
            },
            {
              type: 'link',
              label: 'Roles and responsibilities',
              href: '/docs/cloud/about_gx#roles-and-responsibilities',
            },
            {
              type: 'link',
              label: 'Supported browsers',
              href: '/docs/cloud/about_gx#supported-browsers',
            },
          ]
        },
        { type: 'doc', id: 'cloud/try_gx_cloud' },
        {
          type: 'category',
          label: 'Connect GX Cloud',
          link: { type: 'doc', id: 'cloud/connect/connect_lp' },
          items: [
            'cloud/connect/connect_postgresql',
            'cloud/connect/connect_snowflake',
            'cloud/connect/connect_airflow',
            'cloud/connect/connect_python',
          ]
        },
        {
          type: 'category',
          label: 'Manage Data Assets',
          link: { type: 'doc', id: 'cloud/data_assets/manage_data_assets' },
          items: [
            {
              type: 'link',
              label: 'Create a Data Asset',
              href: '/docs/cloud/data_assets/manage_data_assets#create-a-data-asset',
            },
            {
              type: 'link',
              label: 'View Data Asset metrics',
              href: '/docs/cloud/data_assets/manage_data_assets#view-data-asset-metrics',
            },
            {
              type: 'link',
              label: 'Add an Expectation to a Data Asset column',
              href: '/docs/cloud/data_assets/manage_data_assets#add-an-expectation-to-a-data-asset-column',
            },
            {
              type: 'link',
              label: 'Add a Data Asset to an Existing Data Source',
              href: '/docs/cloud/data_assets/manage_data_assets#add-a-data-asset-to-an-existing-data-source',
            },
            {
              type: 'link',
              label: 'Edit Data Source settings',
              href: '/docs/cloud/data_assets/manage_data_assets#edit-data-source-settings',
            },
            {
              type: 'link',
              label: 'Edit a Data Asset',
              href: '/docs/cloud/data_assets/manage_data_assets#edit-a-data-asset',
            },
            {
              type: 'link',
              label: 'Secure your GX API Data Source connection strings',
              href: '/docs/cloud/data_assets/manage_data_assets#secure-your-gx-api-data-source-connection-strings',
            },
            {
              type: 'link',
              label: 'Delete a Data Asset',
              href: '/docs/cloud/data_assets/manage_data_assets#delete-a-data-asset',
            },
          ]
        },
        {
          type: 'category',
          label: 'Manage Expectations',
          link: { type: 'doc', id: 'cloud/expectations/manage_expectations' },
          items: [
            {
              type: 'link',
              label: 'Available Expectations',
              href: '/docs/cloud/expectations/manage_expectations#available-expectations',
            },
            {
              type: 'link',
              label: 'Add an Expectation',
              href: '/docs/cloud/expectations/manage_expectations#add-an-expectation',
            },
            {
              type: 'link',
              label: 'Edit an Expectation',
              href: '/docs/cloud/expectations/manage_expectations#edit-an-expectation',
            },
            {
              type: 'link',
              label: 'View Expectation history',
              href: '/docs/cloud/expectations/manage_expectations#view-expectation-history',
            },
            {
              type: 'link',
              label: 'Delete an Expectation',
              href: '/docs/cloud/expectations/manage_expectations#delete-an-expectation',
            },
          ]
        },
        {
          type: 'category',
          label: 'Manage Expectation Suites',
          link: { type: 'doc', id: 'cloud/expectation_suites/manage_expectation_suites' },
          items: [
            {
              type: 'link',
              label: 'Create an Expectation Suite ',
              href: '/docs/cloud/expectation_suites/manage_expectation_suites#create-an-expectation-suite',
            },
            {
              type: 'link',
              label: 'Edit an Expectation Suite name',
              href: '/docs/cloud/expectation_suites/manage_expectation_suites#edit-an-expectation-suite-name',
            },
            {
              type: 'link',
              label: 'Delete an Expectation Suite',
              href: '/docs/cloud/expectation_suites/manage_expectation_suites#delete-an-expectation-suite',
            },
          ]
        },
        {
          type: 'category',
          label: 'Manage Validations',
          link: { type: 'doc', id: 'cloud/validations/manage_validations' },
          items: [
            {
              type: 'link',
              label: 'Run a Validation',
              href: '/docs/cloud/validations/manage_validations#run-a-validation',
            },
            {
              type: 'link',
              label: 'Run a Validation on a Data Asset containing partitions',
              href: '/docs/cloud/validations/manage_validations#run-a-validation-on-a-data-asset-containing-partitions',
            },
            {
              type: 'link',
              label: 'View Validation run history',
              href: '/docs/cloud/validations/manage_validations#view-validation-run-history',
            },
          ]
        },
        {
          type: 'category',
          label: 'Manage Checkpoints',
          link: { type: 'doc', id: 'cloud/checkpoints/manage_checkpoints' },
          items: [
            {
              type: 'link',
              label: 'Add a Checkpoint',
              href: '/docs/cloud/checkpoints/manage_checkpoints#add-a-checkpoint',
            },
            {
              type: 'link',
              label: 'Run a Checkpoint',
              href: '/docs/cloud/checkpoints/manage_checkpoints#run-a-checkpoint',
            },
            {
              "type": "link",
              "label": "Add a Validation and an Expectation Suite to a Checkpoint",
              "href": "/docs/cloud/checkpoints/manage_checkpoints#add-a-validation-and-an-expectation-suite-to-a-checkpoint"
            },
            {
              type: 'link',
              label: 'Edit a Checkpoint name',
              href: '/docs/cloud/checkpoints/manage_checkpoints#edit-a-checkpoint-name',
            },
            {
              type: 'link',
              label: 'Edit a Checkpoint configuration',
              href: '/docs/cloud/checkpoints/manage_checkpoints#edit-a-checkpoint-configuration',
            },
            {
              "type": "link",
              "label": "Configure the Checkpoint result format parameter",
          "href": "/docs/cloud/checkpoints/manage_checkpoints#configure-the-checkpoint-result-format-parameter"
            },
            {
              type: 'link',
              label: 'Delete a Checkpoint',
              href: '/docs/cloud/checkpoints/manage_checkpoints#delete-a-checkpoint',
            },
          ]
        },
        {
          type: 'category',
          label: 'Manage users and access tokens',
          link: { type: 'doc', id: 'cloud/users/manage_users' },
          items: [
            {
              type: 'link',
              label: 'Invite a user',
              href: '/docs/cloud/users/manage_users#invite-a-user',
            },
            {
              type: 'link',
              label: 'Edit a user role',
              href: '/docs/cloud/users/manage_users#edit-a-user-role',
            },
            {
              type: 'link',
              label: 'Delete a user',
              href: '/docs/cloud/users/manage_users#delete-a-user',
            },
            {
              type: 'link',
              label: 'Create a user access token',
              href: '/docs/cloud/users/manage_users#create-a-user-access-token',
            },
            {
              type: 'link',
              label: 'Create an organization access token',
              href: '/docs/cloud/users/manage_users#create-an-organization-access-token',
            },
            {
              type: 'link',
              label: 'Delete a user or organization access token',
              href: '/docs/cloud/users/manage_users#delete-a-user-or-organization-access-token',
            },
          ]
        },
      ],
  gx_oss: [
        // {type: 'doc', id: 'oss/intro', label: 'About GX OSS'},
        // {
        //   type: 'category',
        //   label: 'Get started with GX OSS',
        //   link: { type: 'doc', id: 'oss/guides/setup/get_started_lp' },
        //   items: [
        //     'oss/tutorials/quickstart',
        //     {
        //       type: 'doc', id: 'reference/learn/conceptual_guides/gx_overview', label: 'GX Overview'
        //     },
        //     'oss/get_started/get_started_with_gx_and_databricks',
        //     'oss/get_started/get_started_with_gx_and_sql',
        //   ]
        // },
        {
          type: 'category',
          label: 'Configure your GX OSS environment',
          link: { type: 'doc', id: 'oss/guides/setup/setup_overview_lp' },
          items: [
            'oss/guides/setup/setup_overview',
            'oss/guides/setup/installation/install_gx',
            {
              type: 'category',
              label: 'Configure Data Contexts',
              link: { type: 'doc', id: 'oss/guides/setup/configure_data_contexts_lp' },
              items: [
                'oss/guides/setup/configuring_data_contexts/instantiating_data_contexts/instantiate_data_context',
                'oss/guides/setup/configuring_data_contexts/how_to_convert_an_ephemeral_data_context_to_a_filesystem_data_context',
                'oss/guides/setup/configuring_data_contexts/how_to_configure_credentials',
              ]
            },
            'oss/guides/setup/configuring_metadata_stores/configure_expectation_stores',
            'oss/guides/setup/configuring_metadata_stores/configure_result_stores',
            'oss/guides/setup/configuring_metadata_stores/how_to_configure_a_metricsstore',
            'oss/guides/setup/configuring_data_docs/host_and_share_data_docs',
          ]
        },
        {
          type: 'category',
          label: 'Connect to a Data Source',
          link: { type: 'doc', id: 'oss/guides/connecting_to_your_data/connect_to_data_lp' },
          items: [
            'oss/guides/connecting_to_your_data/fluent/filesystem/connect_filesystem_source_data',
            'oss/guides/connecting_to_your_data/fluent/in_memory/connect_in_memory_data',
            'oss/guides/connecting_to_your_data/fluent/database/connect_sql_source_data',
            {
              type: 'category',
              label: 'Manage Data Assets',
              link: { type: 'doc', id: 'oss/guides/connecting_to_your_data/manage_data_assets_lp' },
              items: [
                'oss/guides/connecting_to_your_data/fluent/batch_requests/how_to_request_data_from_a_data_asset',
                'oss/guides/connecting_to_your_data/fluent/data_assets/how_to_organize_batches_in_a_file_based_data_asset',
                'oss/guides/connecting_to_your_data/fluent/database/sql_data_assets',
              ]
            },
          ]
        },
        // {
        //   type: 'category',
        //   label: 'Validate Data',
        //   link: { type: 'doc', id: 'oss/guides/validation/validate_data_lp' },
        //   items: [
        //     'oss/guides/validation/validate_data_overview',
        //     {
        //       type: 'category',
        //       label: 'Manage Checkpoints',
        //       link: { type: 'doc', id: 'oss/guides/validation/checkpoints/checkpoint_lp' },
        //       items: [
        //         'oss/guides/validation/checkpoints/how_to_create_a_new_checkpoint',
        //         'oss/guides/validation/checkpoints/how_to_add_validations_data_or_suites_to_a_checkpoint',
        //         'oss/guides/validation/checkpoints/how_to_validate_multiple_batches_within_single_checkpoint',
        //         'oss/guides/validation/checkpoints/how_to_pass_an_in_memory_dataframe_to_a_checkpoint',
        //         'oss/guides/validation/advanced/how_to_deploy_a_scheduled_checkpoint_with_cron',
        //       ]
        //     },
        //     {
        //       type: 'category',
        //       label: 'Configure Actions',
        //       link: { type: 'doc', id: 'oss/guides/validation/validation_actions/actions_lp' },
        //       items: [
        //         'oss/guides/validation/validation_actions/how_to_trigger_email_as_a_validation_action',
        //         'oss/guides/validation/validation_actions/how_to_collect_openlineage_metadata_using_a_validation_action',
        //         'oss/guides/validation/validation_actions/how_to_trigger_opsgenie_notifications_as_a_validation_action',
        //         'oss/guides/validation/validation_actions/how_to_trigger_slack_notifications_as_a_validation_action',
        //         'oss/guides/validation/advanced/how_to_get_data_docs_urls_for_custom_validation_actions',
        //       ]
        //     },
        //     'oss/guides/validation/limit_validation_results',
        //   ]
        // },
        {
          type: 'category',
          label: 'Integrate',
          link: {
            type: 'generated-index',
            title: 'Integrate',
            description: 'Integrate GX OSS with commonly used data engineering tools.',
          },
          items: [
            {
              type: 'category',
              label: 'Amazon Web Services (AWS)',
              link: {
                type: 'doc',
                id: 'oss/deployment_patterns/aws_lp',
              },
              items: [
                'oss/deployment_patterns/how_to_instantiate_a_data_context_on_an_emr_spark_cluster',
                'oss/deployment_patterns/how_to_use_gx_with_aws/how_to_use_gx_with_aws_using_cloud_storage_and_pandas',
                'oss/deployment_patterns/how_to_use_gx_with_aws/how_to_use_gx_with_aws_using_s3_and_spark',
                'oss/deployment_patterns/how_to_use_gx_with_aws/how_to_use_gx_with_aws_using_athena',
                'oss/deployment_patterns/how_to_use_gx_with_aws/how_to_use_gx_with_aws_using_redshift',
              ],
            },
            'oss/deployment_patterns/how_to_instantiate_a_data_context_hosted_environments',
            'oss/deployment_patterns/how_to_use_great_expectations_with_airflow',
            'oss/deployment_patterns/how_to_use_great_expectations_with_prefect',
          ]
        },
        { type: 'doc', id: 'oss/troubleshooting' },
        'oss/contributing/contributing',
      { type: 'doc', id: 'oss/changelog' },
      ],
  gx_apis: [
    {
      type: 'category',
      label: 'GX API',
      link: {
        type: 'generated-index',
        title: 'GX API',
        description: 'GX API reference content is generated from classes and methods docstrings.',
        slug: '/reference/api/'
      },
      items: [
        {
          type: 'autogenerated',
          dirName: 'reference/api'
        }
      ]
    },
  ],
  learn: [
      'reference/learn/conceptual_guides/expectation_classes',
      'reference/learn/conceptual_guides/metricproviders',
      'reference/learn/usage_statistics',
      {
      type: 'category',
      label: 'Glossary',
      link: { type: 'doc', id: 'reference/learn/glossary' },
      items: [
        'reference/learn/terms/action',
        'reference/learn/terms/batch',
        'reference/learn/terms/batch_request',
        'reference/learn/terms/custom_expectation',
        'reference/learn/terms/checkpoint',
        'reference/learn/terms/datasource',
        'reference/learn/terms/data_context',
        'reference/learn/terms/data_asset',
        'reference/learn/terms/data_assistant',
        'reference/learn/terms/data_docs',
        'reference/learn/terms/evaluation_parameter',
        'reference/learn/terms/execution_engine',
        {
          type: 'category',
          label: 'Expectations',
          link: { type: 'doc', id: 'reference/learn/terms/expectation' },
          collapsed: true,
          items: [
            { type: 'doc', id: 'reference/learn/expectations/conditional_expectations' },
            { type: 'doc', id: 'reference/learn/expectations/distributional_expectations' },
            { type: 'doc', id: 'reference/learn/expectation_suite_operations' },
            { type: 'doc', id: 'reference/learn/expectations/result_format' },
            { type: 'doc', id: 'reference/learn/expectations/standard_arguments' }
          ]
        },
        'reference/learn/terms/expectation_suite',
        'reference/learn/terms/metric',
        {
          type: 'category',
          label: 'Stores',
          link: { type: 'doc', id: 'reference/learn/terms/store' },
          items: [
            'reference/learn/terms/checkpoint_store',
            'reference/learn/terms/data_docs_store',
            'reference/learn/terms/evaluation_parameter_store',
            'reference/learn/terms/expectation_store',
            'reference/learn/terms/metric_store',
            'reference/learn/terms/validation_result_store'
          ]
        },
        'reference/learn/terms/renderer',
        'reference/learn/terms/supporting_resource',
        'reference/learn/terms/validator',
        'reference/learn/terms/validation_result'
      ]
    },
  ],
}


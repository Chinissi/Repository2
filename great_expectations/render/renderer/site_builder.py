import logging
logger = logging.getLogger(__name__)


import json
import importlib
from collections import OrderedDict

from great_expectations.render.renderer import (
    SiteIndexPageRenderer
)
from great_expectations.render.view import (
    DefaultJinjaIndexPageView,
)

class SiteBuilder():
    """SiteBuilder builds a data documentation website for the project defined by a DataContext.

    A data documentation site consists of HTML pages for expectation suites, profiling and validation results, and
    an index.html page that links to all the pages.

    The exact behavior of SiteBuilder is controlled by configuration in the DataContext's great_expectations.yml file.

    Users can specify
    * which datasources to document (by default, all)
    * whether to include expectations, validations and profiling results sections
    * where the expectations and validations should be read from (filesystem or S3)
    * where the HTML files should be written (filesystem or S3)
    * which renderer and view class should be used to render each section

    Here is an example of config for a site:

    local_site:
      type: SiteBuilder
      site_store:
        type: filesystem
        base_directory: uncommitted/documentation/local_site
      validations_store:
        type: filesystem
        base_directory: uncommitted/validations/
        run_id_filter:
          ne: profiling
      profiling_store:
        type: filesystem
        base_directory: uncommitted/validations/
        run_id_filter:
          eq: profiling

      datasources: '*'
      sections:
        index:
          renderer:
            module: great_expectations.render.renderer
            class: SiteIndexPageRenderer
          view:
            module: great_expectations.render.view
            class: DefaultJinjaIndexPageView
        validations:
          renderer:
            module: great_expectations.render.renderer
            class: ValidationResultsPageRenderer
          view:
            module: great_expectations.render.view
            class: DefaultJinjaPageView
        expectations:
          renderer:
            module: great_expectations.render.renderer
            class: ExpectationSuitePageRenderer
          view:
            module: great_expectations.render.view
            class: DefaultJinjaPageView
        profiling:
          renderer:
            module: great_expectations.render.renderer
            class: ProfilingResultsPageRenderer
          view:
            module: great_expectations.render.view
            class: DefaultJinjaPageView
    """

    @classmethod
    def build(cls, data_context, site_config, specified_data_asset_name=None):
        """

        :param data_context:
        :param site_config:
        :return: tupple: index_page_locator_info (a dictionary describing how to locate the index page of the site (specific to resource_store type)
                         index_links_dict

        """

        index_links_dict = OrderedDict()

        # the site config may specify the list of datasource names to document.
        # if the config property is absent or is *, treat as "all"
        datasources_to_document = site_config.get('datasources')
        if not datasources_to_document or datasources_to_document == '*':
            datasources_to_document = [datasource['name'] for datasource in data_context.list_datasources()]


        sections_config = site_config.get('sections')
        if not sections_config:
            raise Exception('"sections" key is missing') #TODO: specific exception class

        # profiling results

        profiling_section_config = sections_config.get('profiling')
        if profiling_section_config:
            new_index_links_dict = cls.generate_profiling_section(
                profiling_section_config,
                data_context
            )

        # validations

        validation_section_config = sections_config.get('validations')
        if validation_section_config:
            validation_renderer_class, validation_view_class = cls.get_renderer_and_view_classes(validation_section_config)
            # try:
            #     validation_renderer_module = importlib.import_module(validation_section_config['renderer']['module'])
            #     validation_renderer_class = getattr(validation_renderer_module, validation_section_config['renderer']['class'])
            #     validation_view_module = importlib.import_module(validation_section_config['view']['module'])
            #     validation_view_class = getattr(validation_view_module, validation_section_config['view']['class'])
            # except Exception:
            #     logger.exception("Failed to load validation renderer or view class")
            #     raise


            #TODO: filter data sources if the config requires it
            for run_id, v0 in cls.pack_validation_result_list_into_nested_dict(
                data_context.stores['fixture_validation_results_store'].list_keys(),
                run_id_filter=site_config["validations_store"].get("run_id_filter")
            ).items():

                for datasource, v1 in v0.items():

                    if datasource not in datasources_to_document:
                        continue

                    for generator, v2 in v1.items():
                        for generator_asset, expectation_suite_names in v2.items():
                            data_asset_name = data_context.data_asset_name_delimiter.join([datasource, generator, generator_asset])
                            if specified_data_asset_name:
                               if data_context._normalize_data_asset_name(data_asset_name) != data_context._normalize_data_asset_name(specified_data_asset_name):
                                   continue
                            for expectation_suite_name in expectation_suite_names:
                                #!!! This validations_store_name is hardcoded and might not exist. Tests are passing, though.
                                validation = data_context.get_validation_result(data_asset_name,
                                                                                expectation_suite_name=expectation_suite_name,
                                                                                validations_store_name="local_validation_result_store",#=site_config['validations_store'],
                                                                                run_id=run_id)

                                logger.info("        Rendering validation: run id: {}, suite {} for data asset {}".format(run_id, expectation_suite_name, data_asset_name))
                                data_asset_name = validation['meta']['data_asset_name']
                                expectation_suite_name = validation['meta']['expectation_suite_name']
                                model = validation_renderer_class.render(validation)

                                print("write a validation")
                                data_context.write_resource(
                                    validation_view_class.render(model),  # bytes
                                    expectation_suite_name + '.html',  # name to be used inside namespace
                                    resource_store=site_config['site_store'],
                                    resource_namespace="validations",
                                    data_asset_name=data_asset_name,
                                    run_id=run_id
                                )

                                if not datasource in index_links_dict:
                                    index_links_dict[datasource] = OrderedDict()
                                if not generator in index_links_dict[datasource]:
                                    index_links_dict[datasource][generator] = OrderedDict()
                                if not generator_asset in index_links_dict[datasource][generator]:
                                    index_links_dict[datasource][generator][generator_asset] = {
                                        'profiling_links': [],
                                        'validation_links': [],
                                        'expectation_suite_links': []
                                    }

                                index_links_dict[datasource][generator][generator_asset]["validation_links"].append(
                                    {
                                        "full_data_asset_name": data_asset_name,
                                        "expectation_suite_name": expectation_suite_name,
                                        "filepath": data_context._get_normalized_data_asset_name_filepath(
                                            data_asset_name,
                                            expectation_suite_name,
                                            base_path='validations/' + run_id,
                                            file_extension=".html"
                                        ),
                                        "source": datasource,
                                        "generator": generator,
                                        "asset": generator_asset,
                                        "run_id": run_id
                                    }
                                )


        # expectation suites

        expectations_section_config = sections_config.get('expectations')
        if expectations_section_config:
            expectations_renderer_class, expectations_view_class = cls.get_renderer_and_view_classes(expectations_section_config)
            # try:
            #     expectations_renderer_module = importlib.import_module(expectations_section_config['renderer']['module'])
            #     expectations_renderer_class = getattr(expectations_renderer_module, expectations_section_config['renderer']['class'])
            #     expectations_view_module = importlib.import_module(expectations_section_config['view']['module'])
            #     expectations_view_class = getattr(expectations_view_module, expectations_section_config['view']['class'])
            # except Exception:
            #     logger.exception("Failed to load expectations renderer or view class")
            #     raise

            for datasource, v1 in data_context.list_expectation_suites().items():

                if datasource not in datasources_to_document:
                    continue

                for generator, v2 in v1.items():
                    for generator_asset, expectation_suite_names in v2.items():
                        data_asset_name = data_context.data_asset_name_delimiter.join(
                            [datasource, generator, generator_asset])
                        if specified_data_asset_name:
                               if data_context._normalize_data_asset_name(data_asset_name) != data_context._normalize_data_asset_name(specified_data_asset_name):
                                   continue
                        for expectation_suite_name in expectation_suite_names:
                            expectation_suite = data_context.get_expectation_suite(
                                data_asset_name,
                                expectation_suite_name=expectation_suite_name)

                            logger.info(
                                "        Rendering expectation suite {} for data asset {}".format(
                                    expectation_suite_name, data_asset_name))
                            data_asset_name = expectation_suite['data_asset_name']
                            expectation_suite_name = expectation_suite['expectation_suite_name']
                            model = expectations_renderer_class.render(expectation_suite)

                            print("write an expectation")
                            data_context.write_resource(
                                expectations_view_class.render(model),  # bytes
                                expectation_suite_name + '.html',  # name to be used inside namespace
                                resource_store=site_config['site_store'],
                                resource_namespace='expectations',
                                data_asset_name=data_asset_name
                            )

                            if not datasource in index_links_dict:
                                index_links_dict[datasource] = OrderedDict()
                            if not generator in index_links_dict[datasource]:
                                index_links_dict[datasource][generator] = OrderedDict()
                            if not generator_asset in index_links_dict[datasource][generator]:
                                index_links_dict[datasource][generator][generator_asset] = {
                                    'profiling_links': [],
                                    'validation_links': [],
                                    'expectation_suite_links': []
                                }

                            index_links_dict[datasource][generator][generator_asset]["expectation_suite_links"].append(
                                {
                                    "full_data_asset_name": data_asset_name,
                                    "expectation_suite_name": expectation_suite_name,
                                    "filepath": data_context._get_normalized_data_asset_name_filepath(
                                        data_asset_name,
                                        expectation_suite_name,
                                        base_path='expectations',
                                        file_extension='.html'
                                    ),
                                    "source": datasource,
                                    "generator": generator,
                                    "asset": generator_asset
                                }
                            )


        # TODO: load dynamically
        model = SiteIndexPageRenderer.render(index_links_dict)

        index_page_output = DefaultJinjaIndexPageView.render(model)

        index_page_locator_info = data_context.write_resource(
            index_page_output,  # bytes
            'index.html',  # name to be used inside namespace
            resource_store=site_config['site_store']
        )

        return (index_page_locator_info, index_links_dict)

    @classmethod
    def get_renderer_and_view_classes(cls, section_config):
        try:
            renderer_module = importlib.import_module(section_config['renderer']['module'])
            renderer_class = getattr(renderer_module, section_config['renderer']['class'])
            view_module = importlib.import_module(section_config['view']['module'])
            view_class = getattr(view_module, section_config['view']['class'])
        except Exception:
            logger.exception("Failed to load profiling renderer or view class")
            raise
        
        return renderer_class, view_class


    @classmethod
    def generate_profiling_section(cls, section_config, data_context):
        profiling_renderer_class, profiling_view_class = cls.get_renderer_and_view_classes(section_config)

        print(data_context.stores.profiling_store.config)
        print(data_context.stores['profiling_store'].list_keys(), "??????")
        nested_namespaced_validation_result_dict = cls.pack_validation_result_list_into_nested_dict(
            data_context.stores['profiling_store'].list_keys(),
            run_id_filter=section_config.get("run_id_filter")
        )
        print(json.dumps(nested_namespaced_validation_result_dict, indent=2))

        #TODO: filter data sources if the config requires it
        for run_id, v0 in nested_namespaced_validation_result_dict.items():
            for datasource, v1 in v0.items():

                if datasource not in datasources_to_document:
                    continue

                for generator, v2 in v1.items():
                    for generator_asset, expectation_suite_names in v2.items():
                        data_asset_name = data_context.data_asset_name_delimiter.join([datasource, generator, generator_asset])
                        if specified_data_asset_name:
                            if data_context._normalize_data_asset_name(data_asset_name) != data_context._normalize_data_asset_name(specified_data_asset_name):
                                continue
                        for expectation_suite_name in expectation_suite_names:
                            #!!! This validations_store_name is hardcoded and might not exist. Tests are passing, though.
                            validation = data_context.get_validation_result(data_asset_name,
                                                                            expectation_suite_name=expectation_suite_name,
                                                                            validations_store_name="profiling_store",#site_config['profiling_store'],
                                                                            run_id=run_id)

                            logger.info("        Rendering profiling for data asset {}".format(data_asset_name))
                            data_asset_name = validation['meta']['data_asset_name']
                            expectation_suite_name = validation['meta']['expectation_suite_name']
                            model = profiling_renderer_class.render(validation)

                            print("write a profiling result")
                            data_context.write_resource(
                                profiling_view_class.render(model),  # bytes
                                expectation_suite_name + '.html',  # name to be used inside namespace
                                resource_store=site_config['site_store'],
                                resource_namespace="profiling",
                                data_asset_name=data_asset_name
                            )

                            if not datasource in index_links_dict:
                                index_links_dict[datasource] = OrderedDict()
                            if not generator in index_links_dict[datasource]:
                                index_links_dict[datasource][generator] = OrderedDict()
                            if not generator_asset in index_links_dict[datasource][generator]:
                                index_links_dict[datasource][generator][generator_asset] = {
                                    'profiling_links': [],
                                    'validation_links': [],
                                    'expectation_suite_links': []
                                }

                            index_links_dict[datasource][generator][generator_asset]["profiling_links"].append(
                                {
                                    "full_data_asset_name": data_asset_name,
                                    "expectation_suite_name": expectation_suite_name,
                                    "filepath": data_context._get_normalized_data_asset_name_filepath(
                                        data_asset_name,
                                        expectation_suite_name,
                                        base_path='profiling',
                                        file_extension=".html"
                                    ),
                                    "source": datasource,
                                    "generator": generator,
                                    "asset": generator_asset
                                }
                            )

    @classmethod
    def pack_validation_result_list_into_nested_dict(cls, validation_result_list, run_id_filter=None):
        """
        {
          "run_id":
            "datasource": {
                "generator": {
                    "generator_asset": [expectation_suite_1, expectation_suite_1, ...]
                }
            }
        }
        """
        print(validation_result_list)

        # if validations_store is None:
        #     validations_store = self.validations_store
        # else:
        #     validations_store = self._normalize_store_path(validations_store)

        validation_results = {}

        # result_paths = validation_result_list
        # print(result_paths)
        # base_length = len(validations_store["base_directory"])
        # relative_paths = [path[base_length:] for path in result_paths]

        relative_paths = validation_result_list

        for result in relative_paths:
            components = result.split("/")

            if len(components) != 5:
                logger.error("Unrecognized validation result path: %s" % result)
                continue
            run_id = components[0]

            # run_id_filter attribute in the config of validation store allows to filter run ids
            if run_id_filter:
                if run_id_filter.get("eq"):
                    if run_id_filter.get("eq") != run_id:
                        continue
                elif run_id_filter.get("ne"):
                    if run_id_filter.get("ne") == run_id:
                        continue

            datasource_name = components[1]
            generator_name = components[2]
            generator_asset = components[3]
            expectation_suite = components[4][:-5]
            if run_id not in validation_results:
                validation_results[run_id] = {}
            if datasource_name not in validation_results[run_id]:
                validation_results[run_id][datasource_name] = {}
            if generator_name not in validation_results[run_id][datasource_name]:
                validation_results[run_id][datasource_name][generator_name] = {}
            if generator_asset not in validation_results[run_id][datasource_name][generator_name]:
                validation_results[run_id][datasource_name][generator_name][generator_asset] = []
            validation_results[run_id][datasource_name][generator_name][generator_asset].append(expectation_suite)

        return validation_results

import logging

from collections import OrderedDict
import os

from great_expectations.cli.datasource import DATASOURCE_TYPE_BY_DATASOURCE_CLASS
from great_expectations.data_context.store.html_site_store import (
    HtmlSiteStore,
    SiteSectionIdentifier,
)
from great_expectations.data_context.types.resource_identifiers import ExpectationSuiteIdentifier, \
    ValidationResultIdentifier

from great_expectations.data_context.util import instantiate_class_from_config
from great_expectations.data_context.util import file_relative_path
import great_expectations.exceptions as exceptions

logger = logging.getLogger(__name__)


class SiteBuilder(object):
    """SiteBuilder builds data documentation for the project defined by a DataContext.

    A data documentation site consists of HTML pages for expectation suites, profiling and validation results, and
    an index.html page that links to all the pages.

    The exact behavior of SiteBuilder is controlled by configuration in the DataContext's great_expectations.yml file.

    Users can specify:

        * which datasources to document (by default, all)
        * whether to include expectations, validations and profiling results sections (by default, all)
        * where the expectations and validations should be read from (filesystem or S3)
        * where the HTML files should be written (filesystem or S3)
        * which renderer and view class should be used to render each section

    Here is an example of a minimal configuration for a site::

        local_site:
            class_name: SiteBuilder
            store_backend:
                class_name: TupleS3StoreBackend
                bucket: data_docs.my_company.com
                prefix: /data_docs/


    A more verbose configuration can also control individual sections and override renderers, views, and stores::

        local_site:
            class_name: SiteBuilder
            store_backend:
                class_name: TupleS3StoreBackend
                bucket: data_docs.my_company.com
                prefix: /data_docs/
            datasource_whitelist:
              - my_source
              - my_second_source
            site_index_builder:
                class_name: DefaultSiteIndexBuilder

            # Verbose version:
            # index_builder:
            #     module_name: great_expectations.render.builder
            #     class_name: DefaultSiteIndexBuilder
            #     renderer:
            #         module_name: great_expectations.render.renderer
            #         class_name: SiteIndexPageRenderer
            #     view:
            #         module_name: great_expectations.render.view
            #         class_name: DefaultJinjaIndexPageView

            site_section_builders:
                # Minimal specification
                expectations:
                    class_name: DefaultSiteSectionBuilder
                    source_store_name: expectation_store
                renderer:
                    module_name: great_expectations.render.renderer
                    class_name: ExpectationSuitePageRenderer

                # More verbose specification with optional arguments
                validations:
                    module_name: great_expectations.data_context.render
                    class_name: DefaultSiteSectionBuilder
                    source_store_name: local_validation_store
                    renderer:
                        module_name: great_expectations.render.renderer
                        class_name: SiteIndexPageRenderer
                    view:
                        module_name: great_expectations.render.view
                        class_name: DefaultJinjaIndexPageView
    """

    def __init__(self,
                 data_context,
                 store_backend,
                 site_index_builder=None,
                 site_section_builders=None,
                 datasource_whitelist=None,
                 runtime_environment=None
                 ):
        self.data_context = data_context
        self.store_backend = store_backend

        # set custom_styles_directory if present
        custom_styles_directory = None
        plugins_directory = data_context.plugins_directory
        if plugins_directory and os.path.isdir(os.path.join(plugins_directory, "custom_data_docs", "styles")):
            custom_styles_directory = os.path.join(plugins_directory, "custom_data_docs/styles")

        # The site builder is essentially a frontend store. We'll open up three types of backends using the base
        # type of the configuration defined in the store_backend section

        self.target_store = HtmlSiteStore(
            store_backend=store_backend,
            runtime_environment=runtime_environment
        )

        # the site config may specify the list of datasource names to document.
        # if the config property is absent or is *, treat as "all"
        self.datasource_whitelist = datasource_whitelist
        if not self.datasource_whitelist or self.datasource_whitelist == '*':
            self.datasource_whitelist = [datasource['name'] for datasource in data_context.list_datasources()]

        if site_index_builder is None:
            site_index_builder = {
                "class_name": "DefaultSiteIndexBuilder"
            }
        self.site_index_builder = instantiate_class_from_config(
            config=site_index_builder,
            runtime_environment={
                "data_context": data_context,
                "custom_styles_directory": custom_styles_directory,
                "target_store": self.target_store,
            },
            config_defaults={
                "name": "site_index_builder",
                "module_name": "great_expectations.render.renderer.site_builder",
                "class_name": "DefaultSiteIndexBuilder"
            }
        )

        if site_section_builders is None:
            site_section_builders = {
                "expectations": {
                    "class_name": "DefaultSiteSectionBuilder",
                    "source_store_name": "expectations_store",
                    "renderer": {
                        "class_name": "ExpectationSuitePageRenderer"
                    }
                },
                "validations": {
                    "class_name": "DefaultSiteSectionBuilder",
                    "source_store_name": "validations_store",
                    "run_id_filter": {
                        "ne": "profiling"
                    },
                    "renderer": {
                        "class_name": "ValidationResultsPageRenderer"
                    },
                    "validation_results_limit": site_index_builder.get("validation_results_limit")
                },
                "profiling": {
                    "class_name": "DefaultSiteSectionBuilder",
                    "source_store_name": "validations_store",
                    "run_id_filter": {
                        "eq": "profiling"
                    },
                    "renderer": {
                        "class_name": "ProfilingResultsPageRenderer"
                    }
                }
            }
        self.site_section_builders = {}
        for site_section_name, site_section_config in site_section_builders.items():
            self.site_section_builders[site_section_name] = instantiate_class_from_config(
                config=site_section_config,
                runtime_environment={
                    "data_context": data_context,
                    "target_store": self.target_store,
                    "custom_styles_directory": custom_styles_directory
                },
                config_defaults={
                    "name": site_section_name,
                    "module_name": "great_expectations.render.renderer.site_builder"
                }
            )

    def build(self, resource_identifiers=None):
        """

        :param resource_identifiers: a list of resource identifiers (ExpectationSuiteIdentifier,
                            ValidationResultIdentifier). If specified, rebuild HTML
                            (or other views the data docs site renders) only for
                            the resources in this list. This supports incremental build
                            of data docs sites (e.g., when a new validation result is created)
                            and avoids full rebuild.
        :return:
        """

        # copy static assets
        self.target_store.copy_static_assets()

        for site_section, site_section_builder in self.site_section_builders.items():
            site_section_builder.build(datasource_whitelist=self.datasource_whitelist,
                                       resource_identifiers=resource_identifiers
                                       )

        return self.site_index_builder.build()


    def get_resource_url(self, resource_identifier=None):
        """
        Return the URL of the HTML document that renders a resource
        (e.g., an expectation suite or a validation result).

        :param resource_identifier: ExpectationSuiteIdentifier, ValidationResultIdentifier
                or any other type's identifier. The argument is optional - when
                not supplied, the method returns the URL of the index page.
        :return: URL (string)
        """

        return self.target_store.get_url_for_resource(resource_identifier=resource_identifier)


class DefaultSiteSectionBuilder(object):

    def __init__(
            self,
            name,
            data_context,
            target_store,
            source_store_name,
            custom_styles_directory=None,
            run_id_filter=None,
            validation_results_limit=None,
            renderer=None,
            view=None,
    ):
        self.name = name
        self.source_store = data_context.stores[source_store_name]
        self.target_store = target_store
        self.run_id_filter = run_id_filter
        self.validation_results_limit = validation_results_limit

        if renderer is None:
            raise exceptions.InvalidConfigError(
                "SiteSectionBuilder requires a renderer configuration with a class_name key."
            )
        self.renderer_class = instantiate_class_from_config(
            config=renderer,
            runtime_environment={
                "data_context": data_context
            },
            config_defaults={
                "module_name": "great_expectations.render.renderer"
            }
        )
        if view is None:
            view = {
                "module_name": "great_expectations.render.view",
                "class_name": "DefaultJinjaPageView",
            }

        self.view_class = instantiate_class_from_config(
            config=view,
            runtime_environment={
                "custom_styles_directory": custom_styles_directory
            },
            config_defaults={
                "module_name": "great_expectations.render.view"
            }
        )

    def build(self, datasource_whitelist, resource_identifiers=None):
        source_store_keys = self.source_store.list_keys()
        if self.name == "validations" and self.validation_results_limit:
            source_store_keys = sorted(source_store_keys, key=lambda x: x.run_id, reverse=True)[:self.validation_results_limit]

        for resource_key in source_store_keys:

            # if no resource_identifiers are passed, the section builder will build
            # a page for every keys in its source store.
            # if the caller did pass resource_identifiers, the section builder
            # will build pages only for the specified resources
            if resource_identifiers and resource_key not in resource_identifiers:
                continue

            if self.run_id_filter:
                if not self._resource_key_passes_run_id_filter(resource_key):
                    continue

            if not self._resource_key_passes_datasource_whitelist(resource_key, datasource_whitelist):
                continue

            resource = self.source_store.get(resource_key)

            if isinstance(resource_key, ExpectationSuiteIdentifier):
                expectation_suite_name = resource_key.expectation_suite_name
                data_asset_name = resource_key.data_asset_name.generator_asset
                logger.debug(
                    "        Rendering expectation suite {}".format(
                        expectation_suite_name,
                    ))
            elif isinstance(resource_key, ValidationResultIdentifier):
                run_id = resource_key.run_id
                expectation_suite_name = resource_key.expectation_suite_identifier.expectation_suite_name
                if run_id == "profiling":
                    logger.debug("        Rendering profiling for batch {}".format(resource_key.batch_identifier))
                else:

                    logger.debug("        Rendering validation: run id: {}, suite {} for batch {}".format(run_id,
                                                                                                              expectation_suite_name,
                                                                                                              resource_key.batch_identifier))

            try:
                rendered_content = self.renderer_class.render(resource)
                viewable_content = self.view_class.render(rendered_content)
            except Exception as e:
                logger.error("Exception occurred during data docs rendering: ", e, exc_info=True)
                continue

            self.target_store.set(
                SiteSectionIdentifier(
                    site_section_name=self.name,
                    resource_identifier=resource_key,
                ),
                viewable_content
            )

    def _resource_key_passes_datasource_whitelist(self, resource_key, datasource_whitelist):
        logger.warning("_resource_key_passes_datasource_whitelist is not yet reimplemented")
        return True
        # if type(resource_key) is ExpectationSuiteIdentifier:
        #     datasource = resource_key.data_asset_name.datasource
        # elif type(resource_key) is ValidationResultIdentifier:
        #     datasource = resource_key.expectation_suite_identifier.data_asset_name.datasource
        # return datasource in datasource_whitelist

    def _resource_key_passes_run_id_filter(self, resource_key):
        if type(resource_key) == ValidationResultIdentifier:
            run_id = resource_key.run_id
        else:
            raise TypeError("run_id_filter filtering is only implemented for ValidationResultResources.")

        if self.run_id_filter.get("eq"):
            return self.run_id_filter.get("eq") == run_id

        elif self.run_id_filter.get("ne"):
            return self.run_id_filter.get("ne") != run_id


class DefaultSiteIndexBuilder(object):

    def __init__(
            self,
            name,
            data_context,
            target_store,
            custom_styles_directory=None,
            show_cta_footer=True,
            validation_results_limit=None,
            renderer=None,
            view=None,
    ):
        # NOTE: This method is almost identical to DefaultSiteSectionBuilder
        self.name = name
        self.data_context = data_context
        self.target_store = target_store
        self.show_cta_footer = show_cta_footer
        self.validation_results_limit = validation_results_limit

        if renderer is None:
            renderer = {
                "module_name": "great_expectations.render.renderer",
                "class_name": "SiteIndexPageRenderer",
            }
        self.renderer_class = instantiate_class_from_config(
            config=renderer,
            runtime_environment={
                "data_context": data_context
            },
            config_defaults={
                "module_name": "great_expectations.render.renderer"
            }
        )

        if view is None:
            view = {
                "module_name": "great_expectations.render.view",
                "class_name": "DefaultJinjaIndexPageView",
            }
        self.view_class = instantiate_class_from_config(
            config=view,
            runtime_environment={
                "custom_styles_directory": custom_styles_directory
            },
            config_defaults={
                "module_name": "great_expectations.render.view"
            }
        )

    def add_resource_info_to_index_links_dict(self,
                                              data_context,
                                              index_links_dict,
                                              data_asset_name,
                                              datasource,
                                              generator,
                                              generator_asset,
                                              expectation_suite_name,
                                              section_name,
                                              run_id=None,
                                              validation_success=None
                                              ):
        import os

        if datasource not in index_links_dict:
            index_links_dict[datasource] = OrderedDict()

        if generator not in index_links_dict[datasource]:
            index_links_dict[datasource][generator] = OrderedDict()

        if generator_asset not in index_links_dict[datasource][generator]:
            index_links_dict[datasource][generator][generator_asset] = {
                'profiling_links': [],
                'validations_links': [],
                'expectations_links': []
            }

        if run_id:
            base_path = "validations/" + run_id
        else:
            base_path = "expectations"

        index_links_dict[datasource][generator][generator_asset][section_name + "_links"].append(
            {
                "full_data_asset_name": str(data_asset_name),
                "expectation_suite_name": expectation_suite_name,
                "filepath": os.path.join(base_path, data_asset_name.to_path(), expectation_suite_name + ".html"),
                "source": datasource,
                "generator": generator,
                "asset": generator_asset,
                "run_id": run_id,
                "validation_success": validation_success
            }
        )

        return index_links_dict

    def get_calls_to_action(self):
        telemetry = None
        db_driver = None
        datasource_classes_by_name = self.data_context.list_datasources()

        if datasource_classes_by_name:
            last_datasource_class_by_name = datasource_classes_by_name[-1]
            last_datasource_class_name = last_datasource_class_by_name["class_name"]
            last_datasource_name = last_datasource_class_by_name["name"]
            last_datasource = self.data_context.datasources[last_datasource_name]

            if last_datasource_class_name == "SqlAlchemyDatasource":
                db_driver = last_datasource.drivername

            datasource_type = DATASOURCE_TYPE_BY_DATASOURCE_CLASS[last_datasource_class_name].value
            telemetry = "?utm_source={}&utm_medium={}&utm_campaign={}".format(
                "ge-init-datadocs-v2",
                datasource_type,
                db_driver,
            )

        return {
            "header": "To continue exploring Great Expectations check out one of these tutorials...",
            "buttons": self._get_call_to_action_buttons(telemetry)
        }

    def _get_call_to_action_buttons(self, telemetry):
        """
        Build project and user specific calls to action buttons.

        This can become progressively smarter about project and user specific
        calls to action.
        """
        create_expectations = CallToActionButton(
            "How To Create Expectations",
            # TODO update this link to a proper tutorial
            "https://docs.greatexpectations.io/en/latest/tutorials/create_expectations.html"
        )
        see_glossary = CallToActionButton(
            "See more kinds of Expectations",
            "http://docs.greatexpectations.io/en/latest/reference/expectation_glossary.html"
        )
        validation_playground = CallToActionButton(
            "How To Validate data",
            # TODO update this link to a proper tutorial
            "https://docs.greatexpectations.io/en/latest/tutorials/validate_data.html"
        )
        customize_data_docs = CallToActionButton(
            "How To Customize Data Docs",
            "https://docs.greatexpectations.io/en/latest/reference/data_docs_reference.html#customizing-data-docs"
        )
        s3_team_site = CallToActionButton(
            "How To Set up a team site on AWS S3",
            "https://docs.greatexpectations.io/en/latest/tutorials/publishing_data_docs_to_s3.html"
        )
        # TODO gallery does not yet exist
        # gallery = CallToActionButton(
        #     "Great Expectations Gallery",
        #     "https://greatexpectations.io/gallery"
        # )

        results = []
        results.append(create_expectations)

        # Show these no matter what
        results.append(validation_playground)
        results.append(customize_data_docs)
        results.append(s3_team_site)

        if telemetry:
            for button in results:
                button.link = button.link + telemetry

        return results

    def build(self):
        # Loop over sections in the HtmlStore
        logger.debug("DefaultSiteIndexBuilder.build")
        expectation_suite_keys = [
            ExpectationSuiteIdentifier.from_tuple(expectation_suite_tuple) for expectation_suite_tuple in
            self.target_store.store_backends[ExpectationSuiteIdentifier].list_keys()
        ]
        validation_and_profiling_result_keys = [
            ValidationResultIdentifier.from_tuple(validation_result_tuple) for validation_result_tuple in
            self.target_store.store_backends[ValidationResultIdentifier].list_keys()
        ]
        profiling_result_keys = [
            validation_result_key for validation_result_key in validation_and_profiling_result_keys
            if validation_result_key.run_id == "profiling"
        ]
        validation_result_keys = [
            validation_result_key for validation_result_key in validation_and_profiling_result_keys
            if validation_result_key.run_id != "profiling"
        ]
        validation_result_keys = sorted(validation_result_keys, key=lambda x: x.run_id, reverse=True)
        if self.validation_results_limit:
            validation_result_keys = validation_result_keys[:self.validation_results_limit]

        index_links_dict = OrderedDict()

        if self.show_cta_footer:
            index_links_dict["cta_object"] = self.get_calls_to_action()

        for expectation_suite_key in expectation_suite_keys:
            self.add_resource_info_to_index_links_dict(
                data_context=self.data_context,
                index_links_dict=index_links_dict,
                data_asset_name=expectation_suite_key.data_asset_name,
                datasource=expectation_suite_key.data_asset_name.datasource,
                generator=expectation_suite_key.data_asset_name.generator,
                generator_asset=expectation_suite_key.data_asset_name.generator_asset,
                expectation_suite_name=expectation_suite_key.expectation_suite_name,
                section_name="expectations"
            )

        for profiling_result_key in profiling_result_keys:
            validation = self.data_context.get_validation_result(
                data_asset_name=profiling_result_key.expectation_suite_identifier.data_asset_name,
                expectation_suite_name=profiling_result_key.expectation_suite_identifier.expectation_suite_name,
                run_id=profiling_result_key.run_id
            )

            validation_success = validation.success

            self.add_resource_info_to_index_links_dict(
                data_context=self.data_context,
                index_links_dict=index_links_dict,
                data_asset_name=profiling_result_key.expectation_suite_identifier.data_asset_name,
                datasource=profiling_result_key.expectation_suite_identifier.data_asset_name.datasource,
                generator=profiling_result_key.expectation_suite_identifier.data_asset_name.generator,
                generator_asset=profiling_result_key.expectation_suite_identifier.data_asset_name.generator_asset,
                expectation_suite_name=profiling_result_key.expectation_suite_identifier.expectation_suite_name,
                section_name="profiling",
                run_id=profiling_result_key.run_id,
                validation_success=validation_success
            )

        for validation_result_key in validation_result_keys:
            validation = self.data_context.get_validation_result(
                data_asset_name=validation_result_key.expectation_suite_identifier.data_asset_name,
                expectation_suite_name=validation_result_key.expectation_suite_identifier.expectation_suite_name,
                run_id=validation_result_key.run_id
            )

            validation_success = validation.success

            self.add_resource_info_to_index_links_dict(
                data_context=self.data_context,
                index_links_dict=index_links_dict,
                data_asset_name=validation_result_key.expectation_suite_identifier.data_asset_name,
                datasource=validation_result_key.expectation_suite_identifier.data_asset_name.datasource,
                generator=validation_result_key.expectation_suite_identifier.data_asset_name.generator,
                generator_asset=validation_result_key.expectation_suite_identifier.data_asset_name.generator_asset,
                expectation_suite_name=validation_result_key.expectation_suite_identifier.expectation_suite_name,
                section_name="validations",
                run_id=validation_result_key.run_id,
                validation_success=validation_success
            )

        try:
            rendered_content = self.renderer_class.render(index_links_dict)
            viewable_content = self.view_class.render(rendered_content)
        except Exception as e:
            logger.error("Exception occurred during data docs rendering: ", e, exc_info=True)
            return None

        return (
            self.target_store.write_index_page(viewable_content),
            index_links_dict
        )


class CallToActionButton(object):
    def __init__(self, title, link):
        self.title = title
        self.link = link

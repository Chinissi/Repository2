# -*- coding: utf-8 -*-

import pytest
import shutil

import json
import os
from collections import OrderedDict

import great_expectations as ge
from great_expectations.render.renderer import (
    DescriptivePageRenderer,
    DescriptiveColumnSectionRenderer,
    PrescriptiveColumnSectionRenderer,
    PrescriptivePageRenderer,
)
from great_expectations.render.view import DefaultJinjaPageView
from great_expectations.render.view.view import render_string_template
from great_expectations.render.renderer.content_block import ValueListContentBlockRenderer
from great_expectations.profile.basic_dataset_profiler import BasicDatasetProfiler

from great_expectations.data_context.util import safe_mmkdir


@pytest.fixture(scope="module")
def titanic_validation_results():
    with open("./tests/test_sets/expected_cli_results_default.json", "r") as infile:
        return json.load(infile)


@pytest.fixture(scope="module")
def titanic_expectations():
    with open("./tests/test_sets/titanic_expectations.json", "r") as infile:
        return json.load(infile, object_pairs_hook=OrderedDict)


@pytest.fixture(scope="module")
def titanic_profiler_evrs():
    with open('./tests/render/fixtures/BasicDatasetProfiler_evrs.json', 'r') as infile:
        return json.load(infile, object_pairs_hook=OrderedDict)


@pytest.fixture(scope="module")
def titanic_profiler_evrs_with_exception():
    with open('./tests/render/fixtures/BasicDatasetProfiler_evrs_with_exception.json', 'r') as infile:
        return json.load(infile)


@pytest.fixture(scope="module")
def titanic_dataset_profiler_expectations():
    with open('./tests/render/fixtures/BasicDatasetProfiler_expectations.json', 'r') as infile:
        return json.load(infile, object_pairs_hook=OrderedDict)


@pytest.fixture(scope="module")
def titanic_dataset_profiler_expectations_with_distribution():
    with open('/Users/james/dev/great_expectations/tests/render/fixtures/BasicDatasetProfiler_expectations_with_distribution.json', 'r') as infile:
        return json.load(infile, encoding="utf-8", object_pairs_hook=OrderedDict)


# Deprecate this fixture until we migrate to fuller project structure
# @pytest.fixture(scope="module")
# def movielens_project_dir(tmp_path_factory):
#     source_path = './tests/test_fixtures/movielens_project/great_expectations/'
#     project_path = str(tmp_path_factory.mktemp('movielens_project'))
#     project_ge_config_path = os.path.join(project_path, "great_expectations")
#     shutil.copytree(source_path, project_ge_config_path)
#     return project_ge_config_path


@pytest.mark.smoketest
def test_smoke_render_descriptive_page_renderer(titanic_validation_results):
    rendered = DescriptivePageRenderer.render(titanic_validation_results)
    with open('./tests/render/output/test_render_descriptive_page_renderer.json', 'w') as outfile:
        json.dump(rendered, outfile, indent=2)

    assert len(rendered["sections"]) > 5


@pytest.mark.smoketest
def test_render_descriptive_column_section_renderer(titanic_validation_results):
    # Group EVRs by column
    evrs = {}
    for evr in titanic_validation_results["results"]:
        try:
            column = evr["expectation_config"]["kwargs"]["column"]
            if column not in evrs:
                evrs[column] = []
            evrs[column].append(evr)
        except KeyError:
            pass

    for column in evrs.keys():
        with open('./tests/render/output/test_render_descriptive_column_section_renderer__' + column + '.json', 'w') \
                as outfile:
            json.dump(DescriptiveColumnSectionRenderer.render(evrs[column]), outfile, indent=2)


@pytest.mark.smoketest
def test_render_prescriptive_column_section_renderer(titanic_expectations):
    # Group expectations by column
    exp_groups = {}
    # print(json.dumps(titanic_expectations, indent=2))
    for exp in titanic_expectations["expectations"]:
        try:
            column = exp["kwargs"]["column"]
            if column not in exp_groups:
                exp_groups[column] = []
            exp_groups[column].append(exp)
        except KeyError:
            pass

    for column in exp_groups.keys():
        with open('./tests/render/output/test_render_prescriptive_column_section_renderer' + column + '.json', 'w') \
                as outfile:
            json.dump(PrescriptiveColumnSectionRenderer.render(exp_groups[column]), outfile, indent=2)


def test_content_block_list_available_expectations():
    available_expectations = ValueListContentBlockRenderer.list_available_expectations()
    assert available_expectations == ['expect_column_values_to_be_in_set']


@pytest.mark.smoketest
def test_render_profiled_fixture_expectations(titanic_dataset_profiler_expectations):
    rendered_json = PrescriptivePageRenderer.render(titanic_dataset_profiler_expectations)
    rendered_page = DefaultJinjaPageView.render(rendered_json)

    with open('./tests/render/output/test_render_profiled_fixture_expectations.html', 'w') as f:
        f.write(rendered_page)

    assert rendered_page[:15] == "<!DOCTYPE html>"
    assert rendered_page[-7:] == "</html>"


@pytest.mark.smoketest
def test_render_profiled_fixture_expectations_with_distribution(titanic_dataset_profiler_expectations_with_distribution):
    # Tests sparkline
    rendered_json = PrescriptivePageRenderer.render(titanic_dataset_profiler_expectations_with_distribution)
    rendered_page = DefaultJinjaPageView.render(rendered_json)

    with open('./tests/render/output/titanic_dataset_profiler_expectations_with_distribution.html', 'w', encoding="utf-8") as f:
        f.write(rendered_page)

    assert rendered_page[:15] == "<!DOCTYPE html>"
    assert rendered_page[-7:] == "</html>"


@pytest.mark.smoketest
def test_render_profiled_fixture_evrs(titanic_profiler_evrs):
    rendered_json = DescriptivePageRenderer.render(titanic_profiler_evrs)
    rendered_page = DefaultJinjaPageView.render(rendered_json)

    with open('./tests/render/output/test_render_profiled_fixture_evrs.html', 'w') as f:
        f.write(rendered_page)

    assert rendered_page[:15] == "<!DOCTYPE html>"
    assert rendered_page[-7:] == "</html>"


@pytest.mark.smoketest
def test_smoke_render_descriptive_page_renderer_with_exception(
        titanic_profiler_evrs_with_exception):
    rendered_json = DescriptivePageRenderer.render(titanic_profiler_evrs_with_exception)
    rendered_page = DefaultJinjaPageView.render(rendered_json)

    with open('./tests/render/output/test_render_descriptive_column_section_renderer_with_exception.html', 'w') as f:
        f.write(rendered_page)

    assert rendered_page[:15] == "<!DOCTYPE html>"
    assert rendered_page[-7:] == "</html>"
    assert "exception" in rendered_page


@pytest.mark.smoketest
def test_full_oobe_flow():
    df = ge.read_csv("examples/data/Titanic.csv")
    df.profile(BasicDatasetProfiler)
    evrs = df.validate()  # ["results"]

    rendered_json = DescriptivePageRenderer.render(evrs)
    rendered_page = DefaultJinjaPageView.render(rendered_json)

    with open('./tests/render/output/test_full_oobe_flow.html', 'w') as f:
        f.write(rendered_page)

    assert rendered_page[:15] == "<!DOCTYPE html>"
    assert rendered_page[-7:] == "</html>"


# Deprecating this overly broad test
#Salvaging this for later use:
    # "notes": {
    #   "format": "markdown",
    #   "content": [
    #     "_To add additional notes, edit the <code>meta.notes.content</code> field in <code>expectations/mydb/default/movies/BasicDatasetProfiler.json</code>_"
    #   ]
    # }

# @pytest.mark.smoketest
# def test_movielens_rendering(movielens_project_dir):
#     context = ge.DataContext(movielens_project_dir)
#     context.render_full_static_site()

#     print(movielens_project_dir)

#     with open(os.path.join(movielens_project_dir, "uncommitted/documentation/mydb/default/movies/BasicDatasetProfiler.html")) as f:
#         html = f.read()
#         assert html != ""
#         assert "This Expectation suite currently contains 19 total Expectations across 3 columns." in html
#         assert "To add additional notes" in html

def test_render_string_template():
    template = {
        "template": "$column Kullback-Leibler (KL) divergence with respect to the following distribution must be lower than $threshold: $sparklines_histogram",
        "params": {
            "column": "categorical_fixed",
            "partition_object": {
                "weights": [
                    0.54,
                    0.32,
                    0.14
                ],
                "values": [
                    "A",
                    "B",
                    "C"
                ]
            },
            "threshold": 0.1,
            "sparklines_histogram": u"\u2588\u2584\u2581"
        },
        "styling": {
            "default": {
                "classes": [
                    "badge",
                    "badge-secondary"
                ]
            },
            "params": {
                "sparklines_histogram": {
                    "styles": {
                        "font-family": "serif"
                    }
                }
            }
        }
    }

    res = render_string_template(template).replace(" ", "").replace("\t", "").replace("\n", "")
    expected = u"""<span>
                <span class="badge badge-secondary" >categorical_fixed</span> Kullback-Leibler (KL) divergence with respect to the following distribution must be lower than <span class="badge badge-secondary" >0.1</span>: <span style="font-family:serif;" >█▄▁</span>
            </span>""".replace(" ", "").replace("\t", "").replace("\n", "")
    assert res == expected

    template = {
        "template": "$column Kullback-Leibler (KL) divergence with respect to the following distribution must be lower than $threshold: $sparklines_histogram",
        "params": {
            "column": "categorical_fixed",
            "partition_object": {
                "weights": [
                    0.54,
                    0.32,
                    0.14
                ],
                "values": [
                    "A",
                    "B",
                    "C"
                ]
            },
            "threshold": 0.1,
            "sparklines_histogram": u"▃▆▁█"
        },
        "styling": {
            "default": {
                "classes": [
                    "badge",
                    "badge-secondary"
                ]
            },
            "params": {
                "sparklines_histogram": {
                    "styles": {
                        "font-family": "serif"
                    }
                }
            }
        }
    }

    res = render_string_template(template).replace(" ", "").replace("\t", "").replace("\n", "")
    expected = u"""<span>
                <span class="badge badge-secondary" >categorical_fixed</span> Kullback-Leibler (KL) divergence with respect to the following distribution must be lower than <span class="badge badge-secondary" >0.1</span>: <span style="font-family:serif;" >▃▆▁█</span>
            </span>""".replace(" ", "").replace("\t", "").replace("\n", "")

    assert res == expected

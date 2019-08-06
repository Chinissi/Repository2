import pytest

import json
from collections import OrderedDict

import great_expectations as ge
import great_expectations.render as render
from great_expectations.render.renderer import (
    DescriptivePageRenderer,
)
from great_expectations.render.view import DefaultJinjaPageView
from great_expectations.render.types import (
    RenderedContentBlock,
    RenderedContentBlockWrapper,
)

@pytest.fixture()
def validation_results():
    with open("./tests/test_sets/expected_cli_results_default.json", "r") as infile:
        return json.load(infile, object_pairs_hook=OrderedDict)


@pytest.fixture()
def expectations():
    with open("./tests/test_sets/titanic_expectations.json", "r") as infile:
        return json.load(infile, object_pairs_hook=OrderedDict)


# noinspection PyPep8Naming
@pytest.mark.smoketest
def test_render_DefaultJinjaPageView_meta_info():
    validation_results = {
        "results": [],
        "statistics": {
            "evaluated_expectations": 156,
            "successful_expectations": 139,
            "unsuccessful_expectations": 17,
            "success_percent": 89.1025641025641
        },
        "meta": {
            "great_expectations.__version__": "0.7.0-beta",
            "data_asset_name": "tetanusvaricella",
            "expectation_suite_name": "my_suite",
            "run_id": "2019-06-25T14:58:09.960521",
            "batch_kwargs": {
                "path": "/Users/user/project_data/public_healthcare_datasets/tetanusvaricella/tetvardata.csv",
                "timestamp": 1561474688.693565
            }
        }
    }
    document = DescriptivePageRenderer.render(validation_results)
    html = DefaultJinjaPageView.render(document)
    print(html)
    # TODO: Use above print to set up snapshot test once we like the result

    assert '<a class="navbar-brand" href="#" style="white-space: normal; word-break: break-all;overflow-wrap: normal; font-size: 1rem; font-weight: 500;">tetanusvaricella</a>' in html


def test_render_section_page():
    section = {
        "section_name": None,
        "content_blocks": [
            {
                "content_block_type": "header",
                "header": "Overview",
            },
            {
                "content_block_type": "table",
                "header": "Dataset info",
                "table_rows": [
                    ["Number of variables", "12"],
                    ["Number of observations", "891"],
                ],
                "styling": {
                    "classes": [
                        "col-6",
                        "table-responsive"
                    ],
                    "styles": {
                        "margin-top": "20px"
                    },
                    "body": {
                        "classes": [
                            "table",
                            "table-sm"
                        ]
                    }
                }
            }
        ]
    }

    rendered_doc = ge.render.view.view.DefaultJinjaSectionView.render({
        "section": section,
        "section_loop": {"index": 1},
    }).replace(" ", "").replace("\t", "").replace("\n", "")

    print(rendered_doc)
    assert rendered_doc == """<div id="section-1" class="ge-section container-fluid">
    <div class="row">
        
<div id="content-block-1" >
    <div id="content-block-1-header" >
        <h3>
            Overview
        </h3></div>
</div>

<div id="content-block-2" class="col-6 table-responsive" style="margin-top:20px;" >
    <div id="content-block-2-header" >
            <h4>
                Dataset info
            </h4></div>
    <table id="content-block-2-body" class="table table-sm" >
        <tr>
            <td id="content-block-2-cell-1-1" >Number of variables</td><td id="content-block-2-cell-1-2" >12</td></tr><tr>
            <td id="content-block-2-cell-2-1" >Number of observations</td><td id="content-block-2-cell-2-2" >891</td></tr></table>
</div>
        
    </div>
</div>""".replace(" ", "").replace("\t", "").replace("\n", "")


def test_rendering_components_without_section_loop_index():
    header_component_content = {
        # "component_type": "header",
        "content_block_type": "header",
        "header": "Overview",
    }
    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render({
        "content_block": header_component_content,
        "content_block_loop": {"index": 2},
    })
    print(rendered_doc)
    assert rendered_doc == \
        """
<div id="content-block-2" >
    <div id="content-block-2-header" >
        <h3>
            Overview
        </h3></div>
</div>"""

    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render({
        "content_block": header_component_content,
    })
    print(rendered_doc)
    assert rendered_doc == \
        """
<div id="content-block" >
    <div id="content-block-header" >
        <h3>
            Overview
        </h3></div>
</div>"""

    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render({
        "content_block": header_component_content,
        "section_loop": {"index": 3},
    })
    print(rendered_doc)
    assert rendered_doc == \
        """
<div id="content-block" >
    <div id="content-block-header" >
        <h3>
            Overview
        </h3></div>
</div>"""


def test_rendering_components_with_styling():
    # Medium-complicated example to verify that all the things are correctly piped to all the places

    header_component_content = {
        # "component_type": "table",
        "content_block_type": "table",
        "header": {
            "template": "$var1 $var2 $var3",
            "params": {
                "var1": "AAA",
                "var2": "BBB",
                "var3": "CCC",
            },
            "styling": {
                "default": {
                    "classes": ["x"]
                },
                "params": {
                    "var1": {
                        "classes": ["y"]
                    }
                }
            }
        },
        "subheader": {
            "template": "$var1 $var2 $var3",
            "params": {
                "var1": "aaa",
                "var2": "bbb",
                "var3": "ccc",
            },
            "styling": {
                "default": {
                    "classes": ["xx"]
                },
                "params": {
                    "var1": {
                        "classes": ["yy"]
                    }
                }
            }
        },
        "table_rows": [
            ["Mean", "446"],
            ["Minimum", "1"],
        ],
        "styling": {
            "classes": ["root_foo"],
            "styles": {"root": "bar"},
            "attributes": {"root": "baz"},
            "header": {
                "classes": ["header_foo"],
                "styles": {"header": "bar"},
                "attributes": {"header": "baz"},
            },
            "subheader": {
                "classes": ["subheader_foo"],
                "styles": {"subheader": "bar"},
                "attributes": {"subheader": "baz"},
            },
            "body": {
                "classes": ["body_foo"],
                "styles": {"body": "bar"},
                "attributes": {"body": "baz"},
            }
        }
    }
    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render({
        "content_block": header_component_content,
        "section_loop": {"index": 1},
        "content_block_loop": {"index": 2},
    })
    print(rendered_doc)
    rendered_doc = rendered_doc.replace(" ", "").replace("\t", "").replace("\n", "")
    
    assert rendered_doc == \
        """
<div id="section-1-content-block-2" class="root_foo" root="baz" style="root:bar;" >
    <div id="section-1-content-block-2-header" class="header_foo" header="baz" style="header:bar;" >
            <h4>
            
            <span>
                <span class="y" >AAA</span> <span class="x" >BBB</span> <span class="x" >CCC</span>
            </span>
        
            </h4></div>
    <table id="section-1-content-block-2-body" class="body_foo" body="baz" style="body:bar;" >
        <tr>
            <td id="section-1-content-block-2-cell-1-1" >Mean</td><td id="section-1-content-block-2-cell-1-2" >446</td></tr><tr>
            <td id="section-1-content-block-2-cell-2-1" >Minimum</td><td id="section-1-content-block-2-cell-2-2" >1</td></tr></table>
</div>""".replace(" ", "").replace("\t", "").replace("\n", "")


### Test all the component types ###


def test_render_header_component():
    header_component_content = RenderedContentBlock({
        # "component_type": "header",
        "content_block_type": "header",
        "header": "Overview",
    })
    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render({
        "content_block": header_component_content,
        "section_loop": {"index": 1},
        "content_block_loop": {"index": 2},
    })
    print(rendered_doc)
    assert rendered_doc == \
        """
<div id="section-1-content-block-2" >
    <div id="section-1-content-block-2-header" >
        <h3>
            Overview
        </h3></div>
</div>"""


def test_render_table_component():
    table_component_content = {
        # "component_type": "header",
        "content_block_type": "table",
        "header": "Overview",
        "table_rows": [
            ["Mean", "446"],
            ["Minimum", "1"],
        ],
        "styling": {
            "classes": ["col-4"],
        }
    }
    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render({
        "content_block": table_component_content,
        "section_loop": {"index": 1},
        "content_block_loop": {"index": 2},
    })
    print(rendered_doc)
    assert rendered_doc == \
        """
<div id="section-1-content-block-2" class="col-4" >
    <div id="section-1-content-block-2-header" >
            <h4>
                Overview
            </h4></div>
    <table id="section-1-content-block-2-body" >
        <tr>
            <td id="section-1-content-block-2-cell-1-1" >Mean</td><td id="section-1-content-block-2-cell-1-2" >446</td></tr><tr>
            <td id="section-1-content-block-2-cell-2-1" >Minimum</td><td id="section-1-content-block-2-cell-2-2" >1</td></tr></table>
</div>"""


def test_render_value_list():
    value_list_component_content = {
        'content_block_type': 'value_list',
        'header': 'Example values',
        'value_list': [{
            'template': '$value',
            'params': {'value': '0'},
            'styling': {'default': {'classes': ['badge', 'badge-info']}}
        }, {
            'template': '$value',
            'params': {'value': '1'},
            'styling': {'default': {'classes': ['badge', 'badge-info']}}
        }],
        'styling': {
            'classes': ['col-4'],
            'styles': {'margin-top': '20px'}
        }
    }

    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render({
        "content_block": value_list_component_content,
        "section_loop": {"index": 1},
        "content_block_loop": {"index": 2},
    })
    print(rendered_doc)
    assert rendered_doc == """
<div id="section-1-content-block-2" class="col-4" style="margin-top:20px;" >
    <div id="section-1-content-block-2-header" >
            <h4>
                Example values
            </h4></div>
    <p id="section-1-content-block-2-body" >
        
            <span>
                <span class="badge badge-info" >0</span>
            </span>
        
        
            <span>
                <span class="badge badge-info" >1</span>
            </span>
        
        </p>
</div>"""


def test_render_graph():
    graph_component_content = RenderedContentBlock(**{
        "content_block_type": "graph",
        "header": "Histogram",
        "graph": "{\"$schema\": \"https://vega.github.io/schema/vega-lite/v2.6.0.json\", \"autosize\": \"fit\", \"config\": {\"view\": {\"height\": 300, \"width\": 400}}, \"data\": {\"name\": \"data-a681d02fb484e64eadd9721b37015d5b\"}, \"datasets\": {\"data-a681d02fb484e64eadd9721b37015d5b\": [{\"bins\": 3.7, \"weights\": 5.555555555555555}, {\"bins\": 10.8, \"weights\": 3.439153439153439}, {\"bins\": 17.9, \"weights\": 17.857142857142858}, {\"bins\": 25.0, \"weights\": 24.206349206349206}, {\"bins\": 32.0, \"weights\": 16.137566137566136}, {\"bins\": 39.1, \"weights\": 12.3015873015873}, {\"bins\": 46.2, \"weights\": 9.788359788359788}, {\"bins\": 53.3, \"weights\": 5.423280423280423}, {\"bins\": 60.4, \"weights\": 3.439153439153439}, {\"bins\": 67.5, \"weights\": 1.8518518518518516}]}, \"encoding\": {\"x\": {\"field\": \"bins\", \"type\": \"ordinal\"}, \"y\": {\"field\": \"weights\", \"type\": \"quantitative\"}}, \"height\": 200, \"mark\": \"bar\", \"width\": 200}",
        "styling": {
            "classes": ["col-4"]
        }
    })

    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render(
        RenderedContentBlockWrapper(**{
        "content_block": graph_component_content,
        "section_loop": {"index": 1},
        "content_block_loop": {"index": 2},
        })
    )
    print(rendered_doc)
    assert rendered_doc == """
<div id="section-1-content-block-2" class="col-4" >
    <div id="section-1-content-block-2-header" >
            <h4>
                Histogram
            </h4></div>
    <div id="section-1-content-block-2-body" ></div>
        <script>
            // Assign the specification to a local variable vlSpec.
            vlSpec = {"$schema": "https://vega.github.io/schema/vega-lite/v2.6.0.json", "autosize": "fit", "config": {"view": {"height": 300, "width": 400}}, "data": {"name": "data-a681d02fb484e64eadd9721b37015d5b"}, "datasets": {"data-a681d02fb484e64eadd9721b37015d5b": [{"bins": 3.7, "weights": 5.555555555555555}, {"bins": 10.8, "weights": 3.439153439153439}, {"bins": 17.9, "weights": 17.857142857142858}, {"bins": 25.0, "weights": 24.206349206349206}, {"bins": 32.0, "weights": 16.137566137566136}, {"bins": 39.1, "weights": 12.3015873015873}, {"bins": 46.2, "weights": 9.788359788359788}, {"bins": 53.3, "weights": 5.423280423280423}, {"bins": 60.4, "weights": 3.439153439153439}, {"bins": 67.5, "weights": 1.8518518518518516}]}, "encoding": {"x": {"field": "bins", "type": "ordinal"}, "y": {"field": "weights", "type": "quantitative"}}, "height": 200, "mark": "bar", "width": 200};
            // Embed the visualization in the container with id `vis`
            vegaEmbed('#section-1-content-block-2-body', vlSpec, {
                actions: false
            }).then(result=>console.log(result)).catch(console.warn);
        </script>
</div>"""


def test_render_text():
    text_component_content = RenderedContentBlock(**{
        "content_block_type": "text",
        "header": "Histogram",
        "content": ["hello"],
        "styling": {
            "classes": ["col-4"]
        }
    })

    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render(
        RenderedContentBlockWrapper(**{
            "content_block": text_component_content,
            "section_loop": {"index": 1},
            "content_block_loop": {"index": 2},
        })
    )
    print(rendered_doc)
    assert rendered_doc == """
<div id="section-1-content-block-2" class="col-4" >
    <div id="section-1-content-block-2-header" >
            <h4>
                Histogram
            </h4></div>
    <div id="section-1-content-block-2-body" >
        <p>hello</p>
        </div>
</div>"""

    text_component_content = RenderedContentBlock(**{
        "content_block_type": "text",
        "header": "Histogram",
        "content": ["hello", "goodbye"],
        "styling": {
            "classes": ["col-4"]
        }
    })

    rendered_doc = ge.render.view.view.DefaultJinjaComponentView.render(
        RenderedContentBlockWrapper(**{
            "content_block": text_component_content,
            "section_loop": {"index": 1},
            "content_block_loop": {"index": 2},
        })
    )
    print(rendered_doc)
    assert rendered_doc == """
<div id="section-1-content-block-2" class="col-4" >
    <div id="section-1-content-block-2-header" >
            <h4>
                Histogram
            </h4></div>
    <div id="section-1-content-block-2-body" >
        <p>hello</p>
        <p>goodbye</p>
        </div>
</div>"""


# TODO: Add tests for the remaining component types
# * value_list
# * bullet_list
# * graph
# * example_list

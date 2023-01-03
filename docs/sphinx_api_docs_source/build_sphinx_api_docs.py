"""This module provides logic for building Sphinx Docs via an Invoke command.

It is currently specific to this build pattern but can be generalized if
needed in the future.

Typical usage example:

    @invoke.task(
        help={
            "clean": "Clean out existing documentation first. Defaults to True.",
        }
    )
    def my_task(
        ctx,
        clean=True,
    ):

        doc_builder = SphinxInvokeDocsBuilder(ctx=ctx)
        doc_builder.exit_with_error_if_docs_dependencies_are_not_installed()
        doc_builder._build_html_api_docs_in_temp_folder(clean=clean)
        ...
"""
import importlib
import logging
import pathlib
import shutil
from urllib.parse import urlparse

import invoke
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class SphinxInvokeDocsBuilder:
    """Utility class to support building API docs using Sphinx and Invoke."""

    def __init__(self, ctx: invoke.context.Context, base_path: pathlib.Path) -> None:
        """Creates SphinxInvokeDocsBuilder instance.

        Args:
            ctx: Invoke context for use in running commands.
            base_path: Path command is run in for use in determining relative paths.
        """
        self.ctx = ctx
        self.base_path = base_path
        self.docs_path = base_path.parent
        self.repo_root = self.docs_path.parent

        self.temp_sphinx_html_dir = (
            self.repo_root / "temp_docs_build_dir" / "sphinx_api_docs"
        )
        self.docusaurus_api_docs_path = self.docs_path / pathlib.Path("reference/api")

    def build_docs(self) -> None:
        """Main method to build Sphinx docs and convert to Docusaurus."""

        self.exit_with_error_if_docs_dependencies_are_not_installed()

        self._remove_temp_html()

        self._build_html_api_docs_in_temp_folder()

        self._remove_existing_api_docs()

        self._process_and_create_docusaurus_mdx_files()

        self._remove_temp_html()

    @staticmethod
    def exit_with_error_if_docs_dependencies_are_not_installed() -> None:
        """Checks and report which dependencies are not installed."""

        module_dependencies = ("sphinx", "myst_parser", "pydata_sphinx_theme")
        modules_not_installed = []

        for module_name in module_dependencies:
            try:
                importlib.import_module(module_name)
            except ImportError:
                modules_not_installed.append(module_name)

        if modules_not_installed:
            raise invoke.Exit(
                f"Please make sure to install missing docs dependencies: {', '.join(modules_not_installed)} by running pip install -r docs/sphinx_api_docs_source/requirements-dev-api-docs.txt",
                code=1,
            )

        logger.debug("Dependencies installed, proceeding.")

    def _build_html_api_docs_in_temp_folder(self):
        """Builds html api documentation in temporary folder."""
        cmd = f"sphinx-build -M html ./ {self.temp_sphinx_html_dir} -E"
        self.ctx.run(cmd, echo=True, pty=True)
        logger.debug("Raw Sphinx HTML generated.")

    def _remove_existing_api_docs(self) -> None:
        """Removes the existing api docs."""
        if self.docusaurus_api_docs_path.is_dir():
            shutil.rmtree(self.docusaurus_api_docs_path)
        pathlib.Path(self.docusaurus_api_docs_path).mkdir(parents=True, exist_ok=True)
        logger.debug("Existing Docusaurus API docs removed.")

    def _process_and_create_docusaurus_mdx_files(self) -> None:
        """Creates API docs as mdx files to serve from docusaurus from content between <section> tags in the sphinx generated docs."""

        # First get file paths
        static_html_file_path = pathlib.Path(self.temp_sphinx_html_dir) / "html"
        paths = static_html_file_path.glob("**/*.html")
        files = [
            p
            for p in paths
            if p.is_file()
            and p.name not in ("genindex.html", "search.html", "index.html")
            and "_static" not in str(p)
        ]

        # Read the generated html and process the content for conversion to mdx
        # Write out to .mdx file using the relative file directory structure
        for html_file in files:
            logger.info(f"Processing: {str(html_file.absolute())}")
            with open(html_file) as f:
                soup = BeautifulSoup(f.read(), "html.parser")

                # Retrieve and remove the title (it will also be autogenerated by docusaurus)
                title = soup.find("h1").extract()
                title_str = title.get_text(strip=True)
                title_str = title_str.replace("#", "")

                # Add class="sphinx-api-doc" to section tag to reference in css
                doc = soup.find("section")
                doc["class"] = "sphinx-api-doc"

                # Process documentation links
                external_refs = doc.find_all(class_="reference external")
                for external_ref in external_refs:
                    url = external_ref.string
                    url_parts = urlparse(url)
                    url_path = url_parts.path.strip("/").split("/")
                    url_text = url_path[-1]

                    formatted_text = url_text.replace("_", " ").title()

                    external_ref.string = formatted_text

                doc_str = str(doc)

                # Add front matter
                doc_front_matter = (
                    "---\n"
                    f"title: {title_str}\n"
                    f"sidebar_label: {title_str}\n"
                    "---\n"
                    "\n"
                )
                doc_str = doc_front_matter + doc_str

                # Write out mdx files
                output_path = self.docusaurus_api_docs_path / html_file.relative_to(
                    static_html_file_path
                ).with_suffix(".mdx")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as fout:
                    fout.write(doc_str)

        logger.info("Created mdx files for serving with docusaurus.")

    def _remove_temp_html(self) -> None:
        """Remove the Sphinx-generated temporary html files + related files."""
        temp_dir = pathlib.Path(self.temp_sphinx_html_dir)
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

        logger.debug("Removed existing generated raw Sphinx HTML.")

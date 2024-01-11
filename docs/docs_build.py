from __future__ import annotations
from contextlib import contextmanager
from functools import cached_property
import json
from .logging import Logger
import os
import shutil
from pathlib import Path
import re
from typing import TYPE_CHECKING, Generator, List, Optional, cast
from io import BytesIO
import zipfile


from docs.prepare_prior_versions import prepare_prior_versions

if TYPE_CHECKING:
    from invoke.context import Context


class DocsBuilder:
    def __init__(
        self,
        context: Context,
        current_directory: Path,
        is_pull_request: bool,
        is_local: bool,
    ) -> None:
        self._context = context
        self._current_directory = current_directory
        self._is_pull_request = is_pull_request
        self._is_local = is_local

        self._current_commit = self._run_and_get_output("git rev-parse HEAD")
        self._current_branch = self._run_and_get_output(
            "git rev-parse --abbrev-ref HEAD"
        )

    def build_docs(self) -> None:
        """Build API docs + docusaurus docs.
        Currently used in our netlify pipeline.
        """
        self._prepare()
        self.logger.print_header("Building docusaurus docs...")
        self._context.run("yarn build")

    def build_docs_locally(self) -> None:
        """Serv docs locally."""
        self._prepare()
        self.logger.print_header("Running yarn start to serve docs locally...")
        self._context.run("yarn start")

    def _prepare(self) -> None:
        """A whole bunch of common work we need"""
        self.logger.print_header("Preparing to build docs...")
        self._load_files()

        self.logger.print_header(
            "Updating versioned code and docs via prepare_prior_versions.py..."
        )
        # TODO: none of this messing with current directory stuff
        os.chdir("..")
        prepare_prior_versions()
        os.chdir("docusaurus")
        self.logger.print("Updated versioned code and docs")

        self._invoke_api_docs()
        self._checkout_correct_branch()

    @contextmanager
    def _load_zip(self, url: str) -> Generator[zipfile.ZipFile, None, None]:
        import requests  # imported here to avoid this getting imported before `invoke deps` finishes

        response = requests.get(url)
        zip_data = BytesIO(response.content)
        with zipfile.ZipFile(zip_data, "r") as zip_ref:
            yield zip_ref

    def _load_files(self) -> None:
        """Load oss_docs_versions zip and relevant versions from github.

        oss_docs_versions contains the versioned docs to be used later by prepare_prior_versions, as well
        as the versions.json file, which contains the list of versions that we then download from github.
        """

        S3_URL = "https://superconductive-public.s3.us-east-2.amazonaws.com/oss_docs_versions_20230615.zip"
        if os.path.exists("versioned_code"):
            shutil.rmtree("versioned_code")
        os.mkdir("versioned_code")
        self.logger.print(f"Copying previous versioned docs from {S3_URL}")
        with self._load_zip(S3_URL) as zip_ref:
            zip_ref.extractall(self._current_directory)
            versions_json = zip_ref.read("versions.json")
            versions = cast(List[str], json.loads(versions_json))
        for version in versions:
            self.logger.print(
                f"Copying code referenced in docs from {version} and writing to versioned_code/version-{version}"
            )
            url = f"https://github.com/great-expectations/great_expectations/archive/refs/tags/{version}.zip"

            with self._load_zip(url) as zip_ref:
                zip_ref.extractall(self._current_directory / "versioned_code")
                old_location = (
                    self._current_directory
                    / f"versioned_code/great_expectations-{version}"
                )
                new_location = (
                    self._current_directory / f"versioned_code/version-{version}"
                )
                shutil.move(str(old_location), str(new_location))

    def _invoke_api_docs(self) -> None:
        """Invokes the invoke api-docs command.
        If this is a non-PR running on netlify, we use the latest tag. Otherwise, we use the current branch.
        """
        if self._is_pull_request or self._is_local:
            self.logger.print_header(
                "Building locally or from within a pull request, using the latest commit to build API docs so changes can be viewed in the Netlify deploy preview."
            )
        else:
            self._run(f"git checkout {self._latest_tag}")
            self._run("git pull")
            self.logger.print_header(
                f"Not in a pull request. Using latest released version {self._latest_tag} at {self._current_commit} to build API docs."
            )
        self.logger.print(
            "Building API docs for current version. Please ignore sphinx docstring errors in red/pink, for example: ERROR: Unexpected indentation."
        )

        # TODO: not this
        self._run("(cd ../../; invoke api-docs)")

    def _checkout_correct_branch(self) -> None:
        """Ensure we are on the right branch to run docusaurus."""
        if self._is_local:
            self.logger.print_header(
                f"Building locally - Checking back out current branch ({self._current_branch}) before building the rest of the docs."
            )
            self._run(f"git checkout {self._current_branch}")
        else:
            self.logger.print_header(
                f"In a pull request or deploying in netlify (PULL_REQUEST = ${self._is_pull_request}) Checking out ${self._current_commit}."
            )
            self._run(f"git checkout {self._current_commit}")

    def _run(self, command: str) -> Optional[str]:
        result = self._context.run(command)
        if not result:
            return None
        elif not result.ok:
            raise Exception(f"Failed to run command: {command}")
        return result.stdout.strip()

    def _run_and_get_output(self, command: str) -> str:
        output = self._run(command)
        assert output
        return output

    @cached_property
    def _latest_tag(self) -> str:
        tags_string = self._run("git tag")
        assert tags_string is not None
        tags = [t for t in tags_string.split() if self._tag_regex.match(t)]
        return sorted(tags)[-1]

    @cached_property
    def logger(self) -> Logger:
        return Logger()

    @cached_property
    def _tag_regex(self) -> re.Pattern:
        return re.compile(r"([0-9]+\.)+[0-9]+")

---
title: Documentation Site
slug: /readme
---

This documentation site is built using [Docusaurus 2](https://v2.docusaurus.io/), a modern static website generator.

## System Requirements

https://docusaurus.io/docs/installation#requirements

## Installation

Follow the [CONTRIBUTING_CODE](https://github.com/great-expectations/great_expectations/blob/develop/CONTRIBUTING_CODE.md) guide in the `great_expectations` repository to install dev dependencies.

Then run the following command from the repository root to install the rest of the dependencies and build documentation locally (including prior versions) and start a development server:
```console
invoke docs
```

Once you've run `invoke docs` once, you can run `invoke docs --start` to start the development server without copying and building prior versions. Note that if prior versions change your build won't include those changes until you run `invoke docs --clean` and `invoke docs` again.

```console
invoke docs --start
```

To remove versioned code, docs and sidebars run:

```console
invoke docs --clean
```


## Linting

[standard.js](https://standardjs.com/) is used to lint the project. Please run the linter before committing changes.

```console
invoke docs --lint
```

## Build

To build a static version of the site, this command generates static content into the `build` directory. This can be served using any static hosting service.

```console
invoke docs --build
```

## Deployment

Deployment is handled via [Netlify](https://app.netlify.com/sites/niobium-lead-7998/overview).

## Other relevant files

The following are a few details about other files Docusaurus uses that you may wish to be familiar with.

- `sidebars.js`: JavaScript that specifies the sidebar/navigation used in docs pages
- `src`: non-docs pages live here
- `static`: static assets used in docs pages (such as CSS) live here
- `docusaurus.config.js`: the configuration file for Docusaurus
- `babel.config.js`: Babel config file used when building
- `package.json`: dependencies and scripts
- `yarn.lock`: dependency lock file that ensures reproducibility

sitemap.xml is not in the repo since it is built and uploaded by a netlify plugin during the documentation build process. 

## Documentation changes checklist

1. For any pages you have moved or removed, update _redirects to point from the old to the new content location


## Versioning

To add a new version, follow these steps:

1. It may help to start with a fresh virtualenv and clone of gx.
1. Make sure dev dependencies are installed `pip install -c constraints-dev.txt -e ".[test]"` and `pip install pyspark`
1. Install API docs dependencies `pip install -r docs/sphinx_api_docs_source/requirements-dev-api-docs.txt`
1. Run `invoke docs version=<MAJOR.MINOR.PATCH>` (substituting your new version numbers)
1. This will create a new zip file (`oss_docs_versions.zip`). Upload to S3 (run `docs/docs_version_bucket_info.py` to generate the url). This will be used later by `invoke docs --build`


## Versioning and docs build flow (pre v1.0)
### Versioning
```mermaid
sequenceDiagram
    Participant Code
    Participant SphinxBuild as temp_sphinx_api_docs_build_dir/
    Participant Docusaurus as docs/docusaurus
    Participant DocsBuild as docs/docusaurus/build
    Participant Github
    Participant S3
    Participant Netlify

    loop versioning
        % invoke api-docs
        Code ->> SphinxBuild: sphinx generated html
        activate SphinxBuild
        SphinxBuild ->> Docusaurus: html converted to .md and store in docs/docusaurus/docs/reference/api
        deactivate SphinxBuild

        activate Docusaurus
        Code ->> Docusaurus: yarn docusaurus docs:version
        Docusaurus ->> Docusaurus: process new version with prepare_prior_versions.py
        DocsBuild ->> S3: Manually update S3 with the new version
        deactivate Docusaurus
    end

    loop invoke docs --build
        % invoke docs --build
        activate Docusaurus
        S3 ->> Docusaurus: Load versions.json, versoned_code/, versioned_docs/ and versioned_sidebars/

        % invoke api-docs
        Code ->> SphinxBuild: sphinx generated html
        activate SphinxBuild
        SphinxBuild ->> Docusaurus: html converted to .md and store in docs/docusaurus/docs/reference/api
        deactivate SphinxBuild

        % yarn docusaurus build
        activate DocsBuild
        Docusaurus ->> DocsBuild: build docs and versioned_*
        deactivate Docusaurus
        DocsBuild ->> Netlify: Deploy
        deactivate DocsBuild
    end

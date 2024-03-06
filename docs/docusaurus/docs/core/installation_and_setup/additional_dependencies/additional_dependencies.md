---
title: Install additional dependencies
hide_feedback_survey: true
hide_title: true
---

import LinkCardGrid from '@site/src/components/LinkCardGrid';
import LinkCard from '@site/src/components/LinkCard';
import OverviewCard from '@site/src/components/OverviewCard';

<OverviewCard title={frontMatter.title}>
Some environments and Data Sources utilize additional Python libraries or third party utilities that are not included in the base installation of Great Expectations (GX).  If your use cases involve any of the following, follow the corresponding guidance to install the necessary dependencies.
</OverviewCard>



<LinkCardGrid>
  <LinkCard 
    topIcon 
    label="Amazon S3"
    description="Install and set up support for Amazon S3 and GX"
    to="/core/installation_and_setup/additional_dependencies/amazon_s3" 
    icon="/img/expectation_icon.svg" 
  />
<LinkCard 
    topIcon 
    label="Azure Blob Storage"
    description="Install and set up support for Azure Blob Storage and GX"
    to="/core/installation_and_setup/additional_dependencies/azure_blob_storage" 
    icon="/img/expectation_icon.svg" 
  />
<LinkCard 
    topIcon 
    label="Google Cloud Storage"
    description="Install and set up support for Google Cloud Storage and GX"
    to="/core/installation_and_setup/additional_dependencies/google_cloud_storage" 
    icon="/img/expectation_icon.svg" 
  />
<LinkCard 
    topIcon 
    label="SQL Data Sources"
    description="Install and set up support for SQL Data Sources and GX"
    to="/core/installation_and_setup/additional_dependencies/sql_data_sources" 
    icon="/img/expectation_icon.svg" 
  />
</LinkCardGrid>

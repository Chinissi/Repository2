import React from 'react';
import {MDXProvider} from '@mdx-js/react';
import MDXComponents from '@theme/MDXComponents';
import WasThisHelpful from "../../components/WasThisHelpful";
import BrowserOnly from "@docusaurus/BrowserOnly";

export default function MDXContent({children}) {
  const {
    metadata: {frontMatter},
  } = children.type;
  return <MDXProvider components={MDXComponents}>
      {children}
    { !frontMatter.hide_feedback_survey && <BrowserOnly>{() => <WasThisHelpful/>}</BrowserOnly> }
  </MDXProvider>;
}

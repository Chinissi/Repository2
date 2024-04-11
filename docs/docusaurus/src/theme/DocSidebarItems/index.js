import React from 'react';
import DocSidebarItems from '@theme-original/DocSidebarItems';
import {useNavbarMobileSidebar} from "@docusaurus/theme-common/internal";
import BrowserOnly from "@docusaurus/BrowserOnly";

export default function DocSidebarItemsWrapper(props) {
    const mobileSidebar = useNavbarMobileSidebar();
    const handleMobileDocSidebarItemClick = (item) => {
        if(window.innerWidth > 996) return;
        if (!props.onItemClick) return;
        if (item.type === 'link') {
            mobileSidebar.toggle();
        }
    }
  return (
      <BrowserOnly>{() => <DocSidebarItems {...props} onItemClick={handleMobileDocSidebarItemClick} />}</BrowserOnly>
  );
}

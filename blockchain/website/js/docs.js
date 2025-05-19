// GlobalCoyn Documentation JavaScript

// Wait for the page to load
document.addEventListener('DOMContentLoaded', function() {
    // Table of contents generator
    const docContent = document.querySelector('.docs-content');
    if (docContent) {
        const headings = docContent.querySelectorAll('h2');
        if (headings.length > 3) {
            // Create TOC container
            const tocContainer = document.createElement('div');
            tocContainer.className = 'toc-container';
            
            const tocTitle = document.createElement('h3');
            tocTitle.textContent = 'Table of Contents';
            tocContainer.appendChild(tocTitle);
            
            const tocList = document.createElement('ul');
            tocList.className = 'toc-list';
            
            // Add ID to headings and create TOC items
            headings.forEach((heading, index) => {
                // Create an ID if not exists
                if (!heading.id) {
                    heading.id = `section-${index}`;
                }
                
                const tocItem = document.createElement('li');
                const tocLink = document.createElement('a');
                tocLink.href = `#${heading.id}`;
                tocLink.textContent = heading.textContent;
                
                tocItem.appendChild(tocLink);
                tocList.appendChild(tocItem);
            });
            
            tocContainer.appendChild(tocList);
            
            // Insert TOC after the first paragraph
            const firstParagraph = docContent.querySelector('p.lead') || docContent.querySelector('p');
            firstParagraph.parentNode.insertBefore(tocContainer, firstParagraph.nextSibling);
        }
    }
    
    // Add copy buttons to code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        const pre = block.parentNode;
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        
        copyButton.addEventListener('click', function() {
            const code = block.textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyButton.textContent = 'Copied!';
                setTimeout(() => {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });
        
        pre.style.position = 'relative';
        copyButton.style.position = 'absolute';
        copyButton.style.right = '10px';
        copyButton.style.top = '10px';
        pre.appendChild(copyButton);
    });
    
    // Mobile sidebar toggle
    const sidebarToggle = document.createElement('button');
    sidebarToggle.className = 'sidebar-toggle';
    sidebarToggle.innerHTML = '<span></span><span></span><span></span>';
    sidebarToggle.setAttribute('aria-label', 'Toggle documentation menu');
    
    const docsSidebar = document.querySelector('.docs-sidebar');
    if (docsSidebar && window.innerWidth < 960) {
        const docsContainer = document.querySelector('.docs-container');
        docsContainer.insertBefore(sidebarToggle, docsSidebar);
        
        sidebarToggle.addEventListener('click', function() {
            docsSidebar.classList.toggle('show');
            this.classList.toggle('active');
        });
    }
    
    // Dark mode toggle functionality
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            
            // Save preference to localStorage
            if (document.body.classList.contains('dark-mode')) {
                localStorage.setItem('theme', 'dark');
                themeToggle.querySelector('img').src = '../assets/sun.svg';
            } else {
                localStorage.setItem('theme', 'light');
                themeToggle.querySelector('img').src = '../assets/moon.svg';
            }
        });
        
        // Apply saved theme preference
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-mode');
            themeToggle.querySelector('img').src = '../assets/sun.svg';
        }
    }
    
    // Table responsiveness
    const tables = document.querySelectorAll('.docs-content table');
    tables.forEach(table => {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-wrapper';
        wrapper.style.overflowX = 'auto';
        
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
    
    // Add target="_blank" to external links
    const links = document.querySelectorAll('.docs-content a');
    links.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('http')) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
    
    // Highlight current section in sidebar based on scroll position
    const sections = document.querySelectorAll('.doc-section');
    const sidebarLinks = document.querySelectorAll('.docs-sidebar a');
    
    if (sections.length > 0 && sidebarLinks.length > 0) {
        window.addEventListener('scroll', () => {
            let current = '';
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.clientHeight;
                
                if (pageYOffset >= sectionTop - 200) {
                    const sectionId = section.querySelector('h2')?.id || '';
                    if (sectionId) {
                        current = `#${sectionId}`;
                    }
                }
            });
            
            sidebarLinks.forEach(link => {
                link.parentElement.classList.remove('active');
                if (link.getAttribute('href') === current) {
                    link.parentElement.classList.add('active');
                }
            });
        });
    }
});
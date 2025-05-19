// GlobalCoyn Enhanced Website JavaScript

// Wait for the page to load
document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const mobileNavToggle = document.createElement('button');
    mobileNavToggle.classList.add('mobile-nav-toggle');
    mobileNavToggle.setAttribute('aria-label', 'Toggle navigation menu');
    mobileNavToggle.innerHTML = '<span></span><span></span><span></span>';
    
    const nav = document.querySelector('nav');
    const navWrapper = document.querySelector('.nav-wrapper');
    
    if (nav && navWrapper) {
        nav.insertBefore(mobileNavToggle, navWrapper);
        
        mobileNavToggle.addEventListener('click', function() {
            navWrapper.classList.toggle('show');
            this.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (navWrapper && navWrapper.classList.contains('show') && 
            !navWrapper.contains(event.target) && 
            !mobileNavToggle.contains(event.target)) {
            navWrapper.classList.remove('show');
            mobileNavToggle.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    });
    
    // Dark mode toggle
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-mode');
            if (themeToggle.querySelector('img')) {
                themeToggle.querySelector('img').src = 'assets/sun.svg';
            }
        }
        
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            
            // Update icon
            const img = this.querySelector('img');
            if (img) {
                if (document.body.classList.contains('dark-mode')) {
                    img.src = img.src.includes('/assets/') ? 
                        'assets/sun.svg' : '../assets/sun.svg';
                } else {
                    img.src = img.src.includes('/assets/') ? 
                        'assets/moon.svg' : '../assets/moon.svg';
                }
            }
            
            // Save preference
            localStorage.setItem('theme', 
                document.body.classList.contains('dark-mode') ? 'dark' : 'light');
        });
    }
    
    // Smooth scrolling for anchor links
    const anchors = document.querySelectorAll('a[href^="#"]');
    
    for (let anchor of anchors) {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                
                // Close mobile menu if open
                if (navWrapper && navWrapper.classList.contains('show')) {
                    navWrapper.classList.remove('show');
                    mobileNavToggle.classList.remove('active');
                    document.body.classList.remove('menu-open');
                }
                
                const offsetTop = targetElement.getBoundingClientRect().top + window.pageYOffset;
                
                window.scrollTo({
                    top: offsetTop - 70, // Adjust for fixed header
                    behavior: 'smooth'
                });
            }
        });
    }
    
    // Intersection Observer for animations
    const fadeElements = document.querySelectorAll('.fade-in');
    
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    fadeElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(element);
    });
    
    // Network stats counter animation
    const statValues = document.querySelectorAll('.stat-value');
    
    const statsObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    statValues.forEach(stat => {
        statsObserver.observe(stat);
    });
    
    function animateCounter(element) {
        const targetValue = element.innerText;
        let suffix = '';
        
        // Extract number and suffix (e.g., "10.5M" -> number: 10.5, suffix: "M")
        let numericValue;
        if (targetValue.includes('%')) {
            numericValue = parseFloat(targetValue.replace('%', ''));
            suffix = '%';
        } else if (targetValue.includes('M')) {
            numericValue = parseFloat(targetValue.replace('M', ''));
            suffix = 'M';
        } else if (targetValue.includes('K')) {
            numericValue = parseFloat(targetValue.replace('K', ''));
            suffix = 'K';
        } else {
            numericValue = parseInt(targetValue, 10);
        }
        
        // Start from zero
        let startValue = 0;
        const duration = 1500; // ms
        const interval = 16; // ms
        const totalSteps = duration / interval;
        const stepSize = numericValue / totalSteps;
        
        const updateCounter = () => {
            startValue += stepSize;
            
            if (startValue >= numericValue) {
                element.innerText = targetValue;
                return;
            }
            
            // Format the display value
            if (numericValue % 1 === 0) {
                // Integer
                element.innerText = Math.floor(startValue) + suffix;
            } else {
                // Float with one decimal place
                element.innerText = startValue.toFixed(1) + suffix;
            }
            
            requestAnimationFrame(updateCounter);
        };
        
        updateCounter();
    }
    
    // Active menu highlighting
    const sections = document.querySelectorAll('section[id]');
    window.addEventListener('scroll', () => {
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (pageYOffset >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });
        
        if (current) {
            document.querySelectorAll('.nav-links a').forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {
                    link.classList.add('active');
                }
            });
        }
    });
});
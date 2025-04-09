document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggleButton');
    const treeView = document.getElementById('treeView');

    const data = {
        "CNAME": {},
        "README.md": {},
        "assets": {
            "font": {
                "Inter-VariableFont_slnt,wght.ttf": {}
            }
        },
        "images": {
            "cloud-download-white.svg": {},
            "cloud-download.svg": {},
            "envelope-white.svg": {},
            "envelope.svg": {},
            "favicon.ico": {},
            "favicon.svg": {},
            "github-white.svg": {},
            "github.svg": {},
            "linkedin-white.svg": {},
            "linkedin.svg": {},
            "moon-white.svg": {},
            "moon.svg": {},
            "play-white.svg": {},
            "play.svg": {},
            "sun-white.svg": {},
            "sun.svg": {}
        },
        "index.html": {},
        "index.js": {},
        "style.css": {}
    }
    
    // Function to recursively create tree structure
    function createTree(data) {
        let html = '<ul>';
        for (let key in data) {
            if (typeof data[key] === 'object' && data[key] !== null) {
                if (Array.isArray(data[key])) {
                    html += `<li><span class="expandable">${key}</span>`;
                    html += '<ul>';
                    data[key].forEach((item, index) => {
                        if (typeof item === 'object') {
                            html += createTree({ [`Item ${index + 1}`]: item });
                        } else {
                            html += `<li>${key} ${index + 1}: ${item}</li>`;
                        }
                    });
                    html += '</ul>';
                    html += '</li>';
                } else {
                    html += `<li><span class="expandable">${key}</span>${createTree(data[key])}</li>`;
                }
            } else {
                html += `<li>${key}: ${data[key]}</li>`;
            }
        }
        html += '</ul>';
        return html;
    }

    // Toggle visibility of tree view on button click
    toggleButton.addEventListener('click', function() {
        if (treeView.style.display === 'none' || treeView.style.display === '') {
            treeView.style.display = 'block';
            setTimeout(() => {
                treeView.style.opacity = 1;
            }, 50); // Small delay to allow the display to take effect
            treeView.innerHTML = createTree(data);
        } else {
            treeView.style.opacity = 0;
            setTimeout(() => {
                treeView.style.display = 'none';
            }, 500); // Matches the CSS transition duration
        }
    });

    // Add event listeners for expanding and collapsing nodes
    treeView.addEventListener('click', function(e) {
        if (e.target && e.target.matches('.expandable')) {
            const nestedList = e.target.nextElementSibling;
            if (nestedList && nestedList.tagName === 'UL') {
                if (nestedList.style.display === 'block') {
                    nestedList.style.display = 'none';
                    e.target.classList.remove('expanded');
                } else {
                    nestedList.style.display = 'block';
                    e.target.classList.add('expanded');
                }
            }
        }
    });
});

// VulnDash Application
// Sample vulnerability data with realistic CVE information

const SAMPLE_DATA = [
    {
        cve_id: "CVE-2023-23397",
        vendor: "Microsoft",
        product: "Outlook",
        cvss: 9.8,
        severity: "CRITICAL",
        epss: 0.89,
        kev: true,
        description: "Microsoft Outlook Elevation of Privilege Vulnerability allowing NTLM relay attacks.",
        published: "2023-10-24"
    },
    {
        cve_id: "CVE-2023-4863",
        vendor: "Google",
        product: "Chrome (WebP)",
        cvss: 8.8,
        severity: "HIGH",
        epss: 0.75,
        kev: false,
        description: "Heap buffer overflow in libwebp in Google Chrome prior to 116.0.5845.187.",
        published: "2023-10-22"
    },
    {
        cve_id: "CVE-2023-44487",
        vendor: "Apache",
        product: "HTTP/2",
        cvss: 7.5,
        severity: "HIGH",
        epss: 0.62,
        kev: false,
        description: "Rapid Reset DDoS attack vector in HTTP/2 protocol implementation.",
        published: "2023-10-21"
    },
    {
        cve_id: "CVE-2023-22515",
        vendor: "Atlassian",
        product: "Confluence",
        cvss: 10.0,
        severity: "CRITICAL",
        epss: 0.95,
        kev: true,
        description: "Broken Access Control vulnerability in Confluence Data Center and Server.",
        published: "2023-10-18"
    },
    {
        cve_id: "CVE-2023-38545",
        vendor: "Curl",
        product: "libcurl",
        cvss: 6.8,
        severity: "MEDIUM",
        epss: 0.42,
        kev: false,
        description: "SOCKS5 heap buffer overflow vulnerability in curl.",
        published: "2023-10-15"
    },
    {
        cve_id: "CVE-2023-32315",
        vendor: "Openfire",
        product: "Console",
        cvss: 8.1,
        severity: "HIGH",
        epss: 0.58,
        kev: false,
        description: "Path traversal vulnerability via the setup environment.",
        published: "2023-10-14"
    },
    {
        cve_id: "CVE-2023-20002",
        vendor: "Cisco",
        product: "IOS XE",
        cvss: 3.4,
        severity: "LOW",
        epss: 0.15,
        kev: false,
        description: "Minor information disclosure via SNMP polling vectors.",
        published: "2023-10-12"
    },
    {
        cve_id: "CVE-2023-46604",
        vendor: "Apache",
        product: "ActiveMQ",
        cvss: 9.8,
        severity: "CRITICAL",
        epss: 0.87,
        kev: true,
        description: "Remote code execution vulnerability in Apache ActiveMQ.",
        published: "2023-10-10"
    },
    {
        cve_id: "CVE-2023-5217",
        vendor: "Google",
        product: "Chrome (libvpx)",
        cvss: 8.8,
        severity: "HIGH",
        epss: 0.71,
        kev: false,
        description: "Heap buffer overflow in vp8 encoding in libvpx.",
        published: "2023-10-08"
    },
    {
        cve_id: "CVE-2023-42793",
        vendor: "JetBrains",
        product: "TeamCity",
        cvss: 9.8,
        severity: "CRITICAL",
        epss: 0.92,
        kev: true,
        description: "Authentication bypass vulnerability in JetBrains TeamCity.",
        published: "2023-10-05"
    },
    {
        cve_id: "CVE-2023-22518",
        vendor: "Atlassian",
        product: "Confluence",
        cvss: 9.1,
        severity: "CRITICAL",
        epss: 0.88,
        kev: true,
        description: "Improper Authorization vulnerability in Confluence Data Center and Server.",
        published: "2023-11-02"
    },
    {
        cve_id: "CVE-2023-36884",
        vendor: "Microsoft",
        product: "Office",
        cvss: 8.3,
        severity: "HIGH",
        epss: 0.68,
        kev: true,
        description: "Remote Code Execution Vulnerability in Windows Search.",
        published: "2023-11-01"
    },
    {
        cve_id: "CVE-2023-34362",
        vendor: "Progress",
        product: "MOVEit Transfer",
        cvss: 9.8,
        severity: "CRITICAL",
        epss: 0.94,
        kev: true,
        description: "SQL injection vulnerability in Progress MOVEit Transfer.",
        published: "2023-10-30"
    },
    {
        cve_id: "CVE-2023-48788",
        vendor: "Fortinet",
        product: "FortiClient EMS",
        cvss: 9.3,
        severity: "CRITICAL",
        epss: 0.85,
        kev: true,
        description: "SQL Injection vulnerability in Fortinet FortiClient EMS.",
        published: "2023-11-05"
    },
    {
        cve_id: "CVE-2023-20273",
        vendor: "Cisco",
        product: "IOS XE",
        cvss: 7.2,
        severity: "HIGH",
        epss: 0.54,
        kev: false,
        description: "Command injection vulnerability in the web UI.",
        published: "2023-10-28"
    },
    {
        cve_id: "CVE-2023-35078",
        vendor: "Ivanti",
        product: "EPMM",
        cvss: 9.8,
        severity: "CRITICAL",
        epss: 0.91,
        kev: true,
        description: "Authentication bypass vulnerability in Ivanti EPMM.",
        published: "2023-10-27"
    },
    {
        cve_id: "CVE-2023-41265",
        vendor: "Qlik",
        product: "Sense",
        cvss: 9.9,
        severity: "CRITICAL",
        epss: 0.93,
        kev: true,
        description: "HTTP tunneling vulnerability in Qlik Sense.",
        published: "2023-11-03"
    },
    {
        cve_id: "CVE-2023-47246",
        vendor: "SysAid",
        product: "On-Premise",
        cvss: 9.8,
        severity: "CRITICAL",
        epss: 0.89,
        kev: true,
        description: "Path traversal vulnerability in SysAid on-premise software.",
        published: "2023-11-04"
    },
    {
        cve_id: "CVE-2023-3519",
        vendor: "Citrix",
        product: "NetScaler ADC",
        cvss: 9.8,
        severity: "CRITICAL",
        epss: 0.96,
        kev: true,
        description: "Code injection vulnerability in Citrix NetScaler ADC and Gateway.",
        published: "2023-10-25"
    },
    {
        cve_id: "CVE-2023-20198",
        vendor: "Cisco",
        product: "IOS XE Web UI",
        cvss: 10.0,
        severity: "CRITICAL",
        epss: 0.97,
        kev: true,
        description: "Privilege escalation vulnerability in Cisco IOS XE Web UI.",
        published: "2023-10-26"
    },
    {
        cve_id: "CVE-2023-6345",
        vendor: "Google",
        product: "Chrome (Skia)",
        cvss: 8.8,
        severity: "HIGH",
        epss: 0.73,
        kev: false,
        description: "Integer overflow in Skia graphics library.",
        published: "2023-11-06"
    },
    {
        cve_id: "CVE-2023-41990",
        vendor: "Apple",
        product: "iOS",
        cvss: 7.8,
        severity: "HIGH",
        epss: 0.61,
        kev: false,
        description: "Privilege escalation vulnerability in iOS and iPadOS.",
        published: "2023-11-07"
    },
    {
        cve_id: "CVE-2023-5631",
        vendor: "Roundcube",
        product: "Webmail",
        cvss: 6.1,
        severity: "MEDIUM",
        epss: 0.38,
        kev: false,
        description: "Cross-site scripting vulnerability in Roundcube webmail.",
        published: "2023-10-09"
    },
    {
        cve_id: "CVE-2023-44216",
        vendor: "Adobe",
        product: "Acrobat Reader",
        cvss: 7.8,
        severity: "HIGH",
        epss: 0.59,
        kev: false,
        description: "Use-after-free vulnerability in Adobe Acrobat Reader.",
        published: "2023-10-11"
    },
    {
        cve_id: "CVE-2023-39143",
        vendor: "PaperCut",
        product: "MF/NG",
        cvss: 9.8,
        severity: "CRITICAL",
        epss: 0.90,
        kev: true,
        description: "Pre-authentication remote code execution in PaperCut.",
        published: "2023-10-19"
    },
    {
        cve_id: "CVE-2023-35082",
        vendor: "Ivanti",
        product: "MobileIron Core",
        cvss: 9.1,
        severity: "CRITICAL",
        epss: 0.86,
        kev: true,
        description: "Authentication bypass in MobileIron Core.",
        published: "2023-10-20"
    }
];

// Application state
let state = {
    allVulnerabilities: [...SAMPLE_DATA],
    filteredVulnerabilities: [...SAMPLE_DATA],
    currentPage: 1,
    rowsPerPage: 20,
    sortColumn: 'published',
    sortDirection: 'desc',
    filters: {
        vendor: '',
        severity: '',
        kev: '',
        epss: '',
        search: ''
    }
};

let trendChart = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateLastSync();
    setInterval(updateLastSync, 1000);
    applyFilters();
    renderTable();
    updateKPIs();
    initializeTrendChart();
});

// Event listeners
function initializeEventListeners() {
    document.getElementById('vendorFilter').addEventListener('change', (e) => {
        state.filters.vendor = e.target.value;
        applyFiltersAndUpdate();
    });

    document.getElementById('severityFilter').addEventListener('change', (e) => {
        state.filters.severity = e.target.value;
        applyFiltersAndUpdate();
    });

    document.getElementById('kevFilter').addEventListener('change', (e) => {
        state.filters.kev = e.target.value;
        applyFiltersAndUpdate();
    });

    document.getElementById('epssFilter').addEventListener('change', (e) => {
        state.filters.epss = e.target.value;
        applyFiltersAndUpdate();
    });

    document.getElementById('searchInput').addEventListener('input', (e) => {
        state.filters.search = e.target.value.toLowerCase();
        applyFiltersAndUpdate();
    });

    document.getElementById('rowsPerPage').addEventListener('change', (e) => {
        state.rowsPerPage = parseInt(e.target.value);
        state.currentPage = 1;
        renderTable();
    });

    document.getElementById('firstPageBtn').addEventListener('click', () => goToPage(1));
    document.getElementById('prevPageBtn').addEventListener('click', () => goToPage(state.currentPage - 1));
    document.getElementById('nextPageBtn').addEventListener('click', () => goToPage(state.currentPage + 1));
    document.getElementById('lastPageBtn').addEventListener('click', () => {
        const totalPages = Math.ceil(state.filteredVulnerabilities.length / state.rowsPerPage);
        goToPage(totalPages);
    });
}

// Apply filters
function applyFilters() {
    state.filteredVulnerabilities = state.allVulnerabilities.filter(vuln => {
        // Vendor filter
        if (state.filters.vendor && vuln.vendor !== state.filters.vendor) {
            return false;
        }

        // Severity filter
        if (state.filters.severity && vuln.severity !== state.filters.severity) {
            return false;
        }

        // KEV filter
        if (state.filters.kev !== '') {
            const kevValue = state.filters.kev === 'true';
            if (vuln.kev !== kevValue) {
                return false;
            }
        }

        // EPSS threshold filter
        if (state.filters.epss) {
            const threshold = parseFloat(state.filters.epss);
            if (vuln.epss < threshold) {
                return false;
            }
        }

        // Search filter
        if (state.filters.search) {
            const searchLower = state.filters.search;
            const searchableText = `${vuln.cve_id} ${vuln.vendor} ${vuln.product} ${vuln.description}`.toLowerCase();
            if (!searchableText.includes(searchLower)) {
                return false;
            }
        }

        return true;
    });

    // Sort the filtered results
    sortFilteredData();
}

// Sort filtered data
function sortFilteredData() {
    state.filteredVulnerabilities.sort((a, b) => {
        let aVal, bVal;

        switch (state.sortColumn) {
            case 'cve_id':
                aVal = a.cve_id;
                bVal = b.cve_id;
                break;
            case 'vendor':
                aVal = a.vendor;
                bVal = b.vendor;
                break;
            case 'cvss':
                aVal = a.cvss;
                bVal = b.cvss;
                break;
            case 'kev':
                aVal = a.kev ? 1 : 0;
                bVal = b.kev ? 1 : 0;
                break;
            case 'published':
                aVal = new Date(a.published);
                bVal = new Date(b.published);
                break;
            default:
                return 0;
        }

        if (aVal < bVal) return state.sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return state.sortDirection === 'asc' ? 1 : -1;
        return 0;
    });
}

// Apply filters and update all components
function applyFiltersAndUpdate() {
    state.currentPage = 1;
    applyFilters();
    renderTable();
    updateKPIs();
    updateTrendChart();
}

// Update KPI cards
function updateKPIs() {
    const total = state.filteredVulnerabilities.length;
    const kevCount = state.filteredVulnerabilities.filter(v => v.kev).length;
    const highEpss = state.filteredVulnerabilities.filter(v => v.epss > 0.7).length;

    // Calculate new this week and today
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const newWeek = state.filteredVulnerabilities.filter(v => {
        const pubDate = new Date(v.published);
        return pubDate >= weekAgo;
    }).length;

    const newToday = state.filteredVulnerabilities.filter(v => {
        const pubDate = new Date(v.published);
        return pubDate >= todayStart;
    }).length;

    // Update DOM
    document.getElementById('totalVulns').textContent = total;
    document.getElementById('totalChange').textContent = `${total} total`;

    document.getElementById('kevCount').textContent = kevCount;
    const kevPercentage = total > 0 ? Math.round((kevCount / total) * 100) : 0;
    document.getElementById('kevPercentage').textContent = `${kevPercentage}%`;

    document.getElementById('highEpssCount').textContent = highEpss;
    const epssPercentage = total > 0 ? Math.round((highEpss / total) * 100) : 0;
    document.getElementById('highEpssPercentage').textContent = `${epssPercentage}%`;

    document.getElementById('newWeekCount').textContent = newWeek;
    document.getElementById('newTodayCount').textContent = `${newToday} today`;
}

// Render table
function renderTable() {
    const tbody = document.getElementById('vulnTableBody');
    tbody.innerHTML = '';

    const totalPages = Math.ceil(state.filteredVulnerabilities.length / state.rowsPerPage);
    const startIdx = (state.currentPage - 1) * state.rowsPerPage;
    const endIdx = Math.min(startIdx + state.rowsPerPage, state.filteredVulnerabilities.length);

    const pageData = state.filteredVulnerabilities.slice(startIdx, endIdx);

    if (pageData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="p-8 text-center text-slate-500">
                    <div class="flex flex-col items-center gap-2">
                        <span class="material-symbols-outlined text-[48px]">search_off</span>
                        <p>No vulnerabilities found matching your filters</p>
                    </div>
                </td>
            </tr>
        `;
    } else {
        pageData.forEach(vuln => {
            const row = createTableRow(vuln);
            tbody.appendChild(row);
        });
    }

    // Update pagination
    document.getElementById('pageInfo').textContent = `PAGE ${state.currentPage} / ${Math.max(1, totalPages)}`;

    // Update button states
    document.getElementById('firstPageBtn').disabled = state.currentPage === 1;
    document.getElementById('prevPageBtn').disabled = state.currentPage === 1;
    document.getElementById('nextPageBtn').disabled = state.currentPage === totalPages || totalPages === 0;
    document.getElementById('lastPageBtn').disabled = state.currentPage === totalPages || totalPages === 0;
}

// Create table row
function createTableRow(vuln) {
    const tr = document.createElement('tr');
    tr.className = 'group hover:bg-surface-border/30 transition-colors cursor-pointer';

    const severityBadge = getSeverityBadge(vuln.cvss, vuln.severity);
    const statusBadge = getStatusBadge(vuln.kev);

    tr.innerHTML = `
        <td class="p-4 text-sm font-bold ${vuln.kev ? 'text-primary' : 'text-slate-500'} font-mono group-hover:text-white transition-colors">${vuln.cve_id}</td>
        <td class="p-4">
            <div class="flex flex-col">
                <span class="text-sm text-white font-medium">${vuln.vendor}</span>
                <span class="text-xs text-slate-500">${vuln.product}</span>
            </div>
        </td>
        <td class="p-4">
            ${severityBadge}
        </td>
        <td class="p-4">
            ${statusBadge}
        </td>
        <td class="p-4 text-sm text-slate-300 line-clamp-1 group-hover:text-white">
            ${vuln.description}
        </td>
        <td class="p-4 text-right text-xs text-slate-500 font-mono">${vuln.published}</td>
    `;

    return tr;
}

// Get severity badge HTML
function getSeverityBadge(cvss, severity) {
    const badges = {
        'CRITICAL': `<div class="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-accent-pink/10 text-accent-pink border border-accent-pink/20 shadow-[0_0_8px_rgba(255,42,109,0.2)]">${cvss.toFixed(1)} CRITICAL</div>`,
        'HIGH': `<div class="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-orange-500/10 text-orange-500 border border-orange-500/20">${cvss.toFixed(1)} HIGH</div>`,
        'MEDIUM': `<div class="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-yellow-500/10 text-yellow-500 border border-yellow-500/20">${cvss.toFixed(1)} MEDIUM</div>`,
        'LOW': `<div class="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-slate-500/10 text-slate-500 border border-slate-500/20">${cvss.toFixed(1)} LOW</div>`
    };
    return badges[severity] || badges['LOW'];
}

// Get status badge HTML
function getStatusBadge(kev) {
    if (kev) {
        return `
            <div class="flex items-center gap-2">
                <span class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-pink opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-accent-pink"></span>
                </span>
                <span class="text-xs text-accent-pink font-bold uppercase tracking-wide">Active Exploit</span>
            </div>
        `;
    } else {
        return `
            <div class="flex items-center gap-2">
                <span class="h-1.5 w-1.5 rounded-full bg-slate-600"></span>
                <span class="text-xs text-slate-400 font-medium uppercase tracking-wide">No Exploit</span>
            </div>
        `;
    }
}

// Sort table
function sortTable(column) {
    if (state.sortColumn === column) {
        state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortColumn = column;
        state.sortDirection = 'desc';
    }
    applyFilters();
    renderTable();
}

// Pagination
function goToPage(page) {
    const totalPages = Math.ceil(state.filteredVulnerabilities.length / state.rowsPerPage);
    if (page < 1 || page > totalPages) return;
    state.currentPage = page;
    renderTable();
}

// Initialize trend chart
function initializeTrendChart() {
    const ctx = document.getElementById('trendChart').getContext('2d');

    const labels = [];
    const data = [];

    // Generate last 30 days
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));

        // Count vulnerabilities for this date in filtered dataset
        const dateStr = date.toISOString().split('T')[0];
        const count = state.filteredVulnerabilities.filter(v => {
            const vDate = new Date(v.published);
            return vDate.toISOString().split('T')[0] === dateStr;
        }).length;
        data.push(count);
    }

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Vulnerabilities Discovered',
                data: data,
                borderColor: '#2b4bee',
                backgroundColor: 'rgba(43, 75, 238, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#2b4bee',
                pointBorderColor: '#2b4bee',
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 17, 26, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#94a3b8',
                    borderColor: '#2b4bee',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(31, 35, 53, 0.5)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#64748b',
                        font: {
                            family: 'Space Grotesk',
                            size: 10
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(31, 35, 53, 0.5)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#64748b',
                        font: {
                            family: 'Space Grotesk',
                            size: 10
                        },
                        precision: 0
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Update trend chart
function updateTrendChart() {
    if (!trendChart) return;

    const labels = [];
    const data = [];

    // Generate last 30 days based on filtered data
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));

        const dateStr = date.toISOString().split('T')[0];
        const count = state.filteredVulnerabilities.filter(v => {
            const vDate = new Date(v.published);
            return vDate.toISOString().split('T')[0] === dateStr;
        }).length;
        data.push(count);
    }

    trendChart.data.labels = labels;
    trendChart.data.datasets[0].data = data;
    trendChart.update();
}

// Update last sync time
function updateLastSync() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    document.getElementById('lastSync').textContent = `LAST SYNC: ${hours}:${minutes}:${seconds}`;
}

// Refresh data (placeholder for real implementation)
function refreshData() {
    const btn = document.getElementById('refreshBtn');
    const icon = btn.querySelector('.material-symbols-outlined');

    // Add spin animation
    icon.style.animation = 'spin 1s linear';

    // Simulate refresh
    setTimeout(() => {
        icon.style.animation = '';
        // In real implementation, this would fetch new data
        applyFiltersAndUpdate();
    }, 1000);
}

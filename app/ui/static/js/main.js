/**
 * FashionLens — Client-side search, filtering, and interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
    initSearch();
    initFilters();
});

/* ═══════════════════════════════════════════════════════════
   Search
   ═══════════════════════════════════════════════════════════ */

function initSearch() {
    const input = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearch');
    if (!input) return;

    input.addEventListener('input', () => {
        clearBtn.style.display = input.value ? 'block' : 'none';
        applyFiltersAndSearch();
    });

    clearBtn.addEventListener('click', () => {
        input.value = '';
        clearBtn.style.display = 'none';
        applyFiltersAndSearch();
    });
}

/* ═══════════════════════════════════════════════════════════
   Filters
   ═══════════════════════════════════════════════════════════ */

const activeFilters = {};  // { filterName: Set([value1, value2]) }

function initFilters() {
    const toggleBtn = document.getElementById('toggleFilters');
    const panel = document.getElementById('filtersPanel');
    const clearAll = document.getElementById('clearAllFilters');

    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        const isVisible = panel.style.display !== 'none';
        panel.style.display = isVisible ? 'none' : 'block';
    });

    // Filter chip clicks
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const filterName = chip.dataset.filter;
            const value = chip.dataset.value;

            if (!activeFilters[filterName]) {
                activeFilters[filterName] = new Set();
            }

            if (chip.classList.contains('active')) {
                chip.classList.remove('active');
                activeFilters[filterName].delete(value);
                if (activeFilters[filterName].size === 0) {
                    delete activeFilters[filterName];
                }
            } else {
                chip.classList.add('active');
                activeFilters[filterName].add(value);
            }

            updateFilterBadge();
            applyFiltersAndSearch();
        });
    });

    if (clearAll) {
        clearAll.addEventListener('click', clearAllFilters);
    }
}

function clearAllFilters() {
    Object.keys(activeFilters).forEach(k => delete activeFilters[k]);
    document.querySelectorAll('.filter-chip.active').forEach(c => c.classList.remove('active'));
    updateFilterBadge();

    // Also clear search
    const input = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearch');
    if (input) { input.value = ''; }
    if (clearBtn) { clearBtn.style.display = 'none'; }

    applyFiltersAndSearch();
}

function updateFilterBadge() {
    const badge = document.getElementById('activeFilterCount');
    if (!badge) return;

    const count = Object.values(activeFilters).reduce((sum, set) => sum + set.size, 0);
    badge.textContent = count;
    badge.style.display = count > 0 ? 'inline-block' : 'none';
}

/* ═══════════════════════════════════════════════════════════
   Apply Filters + Search
   ═══════════════════════════════════════════════════════════ */

function applyFiltersAndSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const cards = document.querySelectorAll('.image-card');
    const noResults = document.getElementById('noResults');
    const emptyState = document.getElementById('emptyState');

    let visibleCount = 0;

    cards.forEach(card => {
        let show = true;

        // 1. Check active filters
        for (const [filterName, values] of Object.entries(activeFilters)) {
            if (values.size === 0) continue;

            // Map filter names to data attributes
            let attrName = filterName;
            if (filterName === 'color_palette') attrName = 'color-palette';

            const cardValue = card.dataset[toCamelCase(attrName)] || '';

            // Check if any filter value is contained in the card's attribute
            let matches = false;
            for (const val of values) {
                if (cardValue.includes(val)) {
                    matches = true;
                    break;
                }
            }
            if (!matches) {
                show = false;
                break;
            }
        }

        // 2. Check search query
        if (show && query) {
            const searchableText = [
                card.dataset.description || '',
                card.dataset.tags || '',
                card.dataset.garmentType || '',
                card.dataset.style || '',
                card.dataset.material || '',
                card.dataset.pattern || '',
                card.dataset.occasion || '',
                card.dataset.continent || '',
                card.dataset.country || '',
                card.dataset.annotations || '',
                card.dataset.userTags || '',
            ].join(' ');

            show = searchableText.includes(query);
        }

        card.classList.toggle('hidden', !show);
        if (show) visibleCount++;
    });

    // Show/hide empty states
    if (noResults) {
        noResults.style.display = (cards.length > 0 && visibleCount === 0) ? 'block' : 'none';
    }
    if (emptyState && cards.length > 0) {
        emptyState.style.display = 'none';
    }
}

/* ═══════════════════════════════════════════════════════════
   Utilities
   ═══════════════════════════════════════════════════════════ */

function toCamelCase(str) {
    return str.replace(/[-_]([a-z])/g, (_, c) => c.toUpperCase());
}

function filterDropdown(input) {
    const filter = input.value.toLowerCase().trim();
    const dropdown = input.closest('.filter-dropdown');
    // We get all the chip buttons within this specific dropdown:
    const chips = dropdown.querySelectorAll('.filter-chip');
    
    chips.forEach(chip => {
        const text = chip.textContent.toLowerCase();
        chip.style.display = text.includes(filter) ? 'block' : 'none';
    });
}

// API Base URL
const API_BASE_URL = 'http://localhost:8000';

// Style Concepts Definitions
const STYLE_CONCEPTS = [
    {
        id: 'minimalist',
        title: 'Modern Minimalist',
        tagline: 'Clean lines, effortless elegance',
        description: 'Embrace simplicity with contemporary pieces in soothing neutral tones. This aesthetic features clean silhouettes, quality fabrics, and timeless designs that work for any occasion. Think relaxed beige trousers paired with a soft grey top, perfect for creating a versatile capsule wardrobe.',
        query: 'minimalist casual outfit with clean lines, neutral beige or grey tones, relaxed fit, contemporary style for everyday wear',
        imageUrl: '/static/concept_images/concept_minimalist.png',
        gradient: 'linear-gradient(135deg, #f5f5f0 0%, #e8e8e0 100%)'  // Fallback
    },
    {
        id: 'bohemian',
        title: 'Bohemian Chic',
        tagline: 'Free-spirited, natural flow',
        description: 'Free-spirited style featuring flowing fabrics and earthy tones. Embrace natural textures, relaxed fits, and artisan details perfect for weekend adventures or vacation vibes. Olive tunics, terracotta dresses, and comfortable layers create an effortlessly bohemian look.',
        query: 'bohemian flowing dress or tunic in earthy olive or terracotta, relaxed fit, perfect for casual vacation with natural fabrics',
        imageUrl: '/static/concept_images/concept_bohemian.png',
        gradient: 'linear-gradient(135deg, #d4a574 0%, #a68860 100%)'
    },
    {
        id: 'elegant',
        title: 'Elegant Evening',
        tagline: 'Sophisticated, timeless glamour',
        description: 'Sophisticated pieces for special occasions. Rich jewel tones, refined fabrics, and elegant silhouettes that make a statement at evening events and celebrations. Navy midi dresses and burgundy gowns with refined details elevate any formal occasion.',
        query: 'elegant evening midi dress in navy or burgundy, fitted silhouette, sophisticated for party or evening wear with refined details',
        imageUrl: '/static/concept_images/concept_elegant.png',
        gradient: 'linear-gradient(135deg, #2c3e50 0%, #8b2942 100%)'
    },
    {
        id: 'sporty',
        title: 'Sporty Active',
        tagline: 'Performance meets style',
        description: 'Performance-ready pieces designed for movement. Breathable fabrics, supportive fits, and bold colors keep you comfortable during workouts and active days. Modern athletic wear in vibrant hues combines functionality with contemporary style.',
        query: 'sporty activewear outfit in bright colors, fitted performance leggings and training top, modern athletic style with breathable fabric',
        imageUrl: '/static/concept_images/concept_sporty.png',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    {
        id: 'classic',
        title: 'Classic Work',
        tagline: 'Professional, polished power',
        description: 'Professional wardrobe essentials with timeless appeal. Tailored pieces in neutral tones create polished looks perfect for the office and business meetings. Structured blazers, crisp trousers, and refined tops project confidence and professionalism.',
        query: 'classic work outfit with tailored blazer and trousers in neutral tones, professional elegant style, fitted silhouette for office wear',
        imageUrl: '/static/concept_images/concept_classic.png',
        gradient: 'linear-gradient(135deg, #434343 0%, #000000 100%)'
    },
    {
        id: 'casual',
        title: 'Casual Weekend',
        tagline: 'Comfortable, relaxed vibes',
        description: 'Effortlessly comfortable pieces for relaxed days. Soft fabrics, easy fits, and versatile basics that feel as good as they look for weekend activities. Comfortable jeans, cozy sweaters, and relaxed tees create the perfect laid-back weekend wardrobe.',
        query: 'casual weekend outfit with comfortable jeans and relaxed tee in soft colors, everyday modern style, relaxed fit for lounge and casual',
        imageUrl: '/static/concept_images/concept_casual.png',
        gradient: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)'
    }
];

// View Management
const views = {
    search: document.getElementById('searchView'),
    loading: document.getElementById('loadingView'),
    workbench: document.getElementById('workbenchView'),
    products: document.getElementById('productsView'),
    lookBuilder: document.getElementById('lookBuilderView')
};

function showView(viewName) {
    Object.keys(views).forEach(key => {
        views[key].classList.add('hidden');
    });
    views[viewName].classList.remove('hidden');

    // Update progress indicator
    updateProgressIndicator(viewName);
}

// Loading Overlay Functions (for modal overlay on top of current view)
function showLoadingOverlay() {
    views.loading.classList.remove('hidden');
}

function hideLoadingOverlay() {
    views.loading.classList.add('hidden');
}

// Progress Indicator Management
function updateProgressIndicator(viewName) {
    const progressIndicator = document.getElementById('progressIndicator');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    const step4 = document.getElementById('step4');

    // Hide on search view, show on others
    if (viewName === 'search' || viewName === 'loading') {
        progressIndicator.classList.add('hidden');
        return;
    } else {
        progressIndicator.classList.remove('hidden');
    }

    // Reset all steps
    step1.classList.remove('active', 'completed');
    step2.classList.remove('active', 'completed');
    step3.classList.remove('active', 'completed');
    step4.classList.remove('active', 'completed');

    // Set states based on current view
    if (viewName === 'workbench') {
        step1.classList.add('completed');
        step2.classList.add('active');
    } else if (viewName === 'products') {
        step1.classList.add('completed');
        step2.classList.add('completed');
        step3.classList.add('active');
    } else if (viewName === 'lookBuilder') {
        step1.classList.add('completed');
        step2.classList.add('completed');
        step3.classList.add('completed');
        step4.classList.add('active');
    }
}

// Progress Indicator Navigation
document.getElementById('step1').addEventListener('click', () => {
    if (currentState.query) {
        showView('search');
    }
});

document.getElementById('step2').addEventListener('click', () => {
    if (currentState.conceptHistory.length > 0) {
        showView('workbench');
    }
});

document.getElementById('step3').addEventListener('click', () => {
    if (currentState.products && currentState.products.length > 0) {
        showView('products');
    }
});

document.getElementById('step4').addEventListener('click', () => {
    if (currentState.generatedLook) {
        showView('lookBuilder');
    }
});

// Current State
let currentState = {
    query: '',
    conceptHistory: [],  // Array of {imageUrl, description, timestamp, refinementPrompt}
    currentConceptIndex: 0,
    products: [],
    suggestionCache: {},  // Cache suggestions per concept index
    selectedProducts: [],  // Products selected for creating a look (max 3)
    generatedLook: null  // Generated look data {look_image_url, description, products}
};

// Progress step configurations
const PROGRESS_STEPS = {
    search: [
        { text: "Analyzing your style preferences...", duration: 1000 },
        { text: "Understanding your vision...", duration: 1000 },
        { text: "Creating your concept design...", duration: 0 }, // API call for image
        { text: "Generating style variations...", duration: 0 }, // API call for suggestions
        { text: "Finalizing your style...", duration: 500 }
    ],
    refine: [
        { text: "Interpreting your refinement...", duration: 800 },
        { text: "Adjusting the design...", duration: 0 }, // API call for image
        { text: "Generating style variations...", duration: 0 }, // API call for suggestions
        { text: "Perfecting the details...", duration: 500 }
    ],
    matchProducts: [
        { text: "Analyzing your style concept...", duration: 1000 },
        { text: "Generating style signature...", duration: 1000 },
        { text: "Searching our catalog...", duration: 0 }, // API call
        { text: "Ranking best matches...", duration: 500 }
    ],
    createLook: [
        { text: "Analyzing selected products...", duration: 1000 },
        { text: "Styling your outfit...", duration: 0 }, // API call
        { text: "Finalizing your look...", duration: 800 }
    ]
};

// Progress Steps Helper Functions
function initializeProgressSteps(steps) {
    const container = document.getElementById('progressSteps');
    container.innerHTML = '';

    steps.forEach((step, index) => {
        const stepEl = document.createElement('div');
        stepEl.className = 'progress-step';
        stepEl.id = `progress-step-${index}`;

        const iconEl = document.createElement('div');
        iconEl.className = 'progress-step-icon';
        iconEl.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>';

        const textEl = document.createElement('div');
        textEl.className = 'progress-step-text';
        textEl.textContent = step.text;

        stepEl.appendChild(iconEl);
        stepEl.appendChild(textEl);
        container.appendChild(stepEl);
    });
}

async function runProgressSteps(steps, apiCallIndex, apiCallFn) {
    // Run steps before API call
    for (let i = 0; i < apiCallIndex; i++) {
        const stepEl = document.getElementById(`progress-step-${i}`);
        stepEl.classList.add('active');
        await new Promise(resolve => setTimeout(resolve, steps[i].duration));
        stepEl.classList.remove('active');
        stepEl.classList.add('completed');
    }

    // Run API call step
    const apiStepEl = document.getElementById(`progress-step-${apiCallIndex}`);
    apiStepEl.classList.add('active');
    const result = await apiCallFn();
    apiStepEl.classList.remove('active');
    apiStepEl.classList.add('completed');

    // Run steps after API call
    for (let i = apiCallIndex + 1; i < steps.length; i++) {
        const stepEl = document.getElementById(`progress-step-${i}`);
        stepEl.classList.add('active');
        await new Promise(resolve => setTimeout(resolve, steps[i].duration));
        stepEl.classList.remove('active');
        stepEl.classList.add('completed');
    }

    return result;
}

// Search Functionality
document.getElementById('searchButton').addEventListener('click', handleSearch);
document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSearch();
    }
});

async function handleSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();

    if (!query) {
        alert('Please enter a search query');
        return;
    }

    currentState.query = query;

    // Initialize and show progress steps
    const steps = PROGRESS_STEPS.search;
    initializeProgressSteps(steps);
    showLoadingOverlay();

    try {
        let imageData = null;
        let suggestions = null;

        // Step 1-2: Pre-image generation steps
        for (let i = 0; i < 2; i++) {
            const stepEl = document.getElementById(`progress-step-${i}`);
            stepEl.classList.add('active');
            await new Promise(resolve => setTimeout(resolve, steps[i].duration));
            stepEl.classList.remove('active');
            stepEl.classList.add('completed');
        }

        // Step 3: Generate concept image
        const imageStepEl = document.getElementById(`progress-step-2`);
        imageStepEl.classList.add('active');
        const response = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        imageData = await response.json();
        imageStepEl.classList.remove('active');
        imageStepEl.classList.add('completed');

        // Step 4: Generate style suggestions
        const suggestionsStepEl = document.getElementById(`progress-step-3`);
        suggestionsStepEl.classList.add('active');

        const suggestionsResponse = await fetch(`${API_BASE_URL}/api/suggest-refinements`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: imageData.image_url,
                description: imageData.description,
                query: query
            })
        });

        if (suggestionsResponse.ok) {
            const suggestionsData = await suggestionsResponse.json();
            suggestions = suggestionsData.suggestions || [];
        } else {
            // Use fallback suggestions if API fails
            suggestions = [
                {title: 'Color Variation', description: 'Try a different color palette while maintaining the overall aesthetic'},
                {title: 'Length Adjustment', description: 'Adjust the length for a different silhouette'},
                {title: 'Detail Enhancement', description: 'Add decorative elements or embellishments'},
                {title: 'Silhouette Change', description: 'Modify the overall shape and fit'}
            ];
        }

        suggestionsStepEl.classList.remove('active');
        suggestionsStepEl.classList.add('completed');

        // Step 5: Finalizing
        const finalStepEl = document.getElementById(`progress-step-4`);
        finalStepEl.classList.add('active');
        await new Promise(resolve => setTimeout(resolve, steps[4].duration));
        finalStepEl.classList.remove('active');
        finalStepEl.classList.add('completed');

        // Initialize concept history with first image
        currentState.conceptHistory = [{
            imageUrl: imageData.image_url,
            description: imageData.description,
            timestamp: Date.now(),
            refinementPrompt: null  // Original search
        }];
        currentState.currentConceptIndex = 0;

        // Cache suggestions for this concept
        currentState.suggestionCache[0] = suggestions;

        // Hide loading overlay and show workbench with everything ready
        hideLoadingOverlay();
        showView('workbench');
        displayConceptWithHistory();

    } catch (error) {
        console.error('Search error:', error);
        alert('An error occurred while processing your search. Please try again.');
        hideLoadingOverlay();
        showView('search');
    }
}

// Concept History Display Functions
function displayConceptWithHistory() {
    const current = currentState.conceptHistory[currentState.currentConceptIndex];

    // Update main image and description
    document.getElementById('generatedImage').src = current.imageUrl;
    document.getElementById('imageDescription').textContent = current.description;

    // Clear refinement input
    document.getElementById('refinementInput').value = '';

    // Render thumbnail carousel
    renderHistoryCarousel();

    // Update navigation buttons
    updateHistoryNavigation();

    // Display cached suggestions (already loaded during initial sequence)
    const cachedSuggestions = currentState.suggestionCache[currentState.currentConceptIndex];
    if (cachedSuggestions) {
        displaySuggestions(cachedSuggestions);
    } else {
        // If no cached suggestions (e.g., navigating to old concept), fetch them
        fetchStyleSuggestions(currentState.currentConceptIndex);
    }
}

function renderHistoryCarousel() {
    const track = document.getElementById('historyTrack');
    const countEl = document.getElementById('historyCount');

    track.innerHTML = '';

    currentState.conceptHistory.forEach((concept, index) => {
        const thumbnail = document.createElement('div');
        thumbnail.className = 'history-thumbnail';
        if (index === currentState.currentConceptIndex) {
            thumbnail.classList.add('active');
        }

        const img = document.createElement('img');
        img.src = concept.imageUrl;
        img.alt = `Concept ${index + 1}`;

        // Add tooltip showing refinement prompt
        thumbnail.title = concept.refinementPrompt || 'Original search';

        thumbnail.appendChild(img);
        thumbnail.addEventListener('click', () => navigateToConceptIndex(index));
        track.appendChild(thumbnail);
    });

    // Update counter
    countEl.textContent = `${currentState.currentConceptIndex + 1} of ${currentState.conceptHistory.length}`;

    // Scroll active thumbnail into view
    const activeThumbnail = track.querySelector('.history-thumbnail.active');
    if (activeThumbnail) {
        activeThumbnail.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
}

function navigateToConceptIndex(index) {
    if (index >= 0 && index < currentState.conceptHistory.length) {
        currentState.currentConceptIndex = index;
        displayConceptWithHistory();
    }
}

function updateHistoryNavigation() {
    const prevBtn = document.getElementById('historyPrev');
    const nextBtn = document.getElementById('historyNext');

    prevBtn.disabled = currentState.currentConceptIndex === 0;
    nextBtn.disabled = currentState.currentConceptIndex === currentState.conceptHistory.length - 1;
}

// Navigation button event listeners
document.getElementById('historyPrev').addEventListener('click', () => {
    if (currentState.currentConceptIndex > 0) {
        navigateToConceptIndex(currentState.currentConceptIndex - 1);
    }
});

document.getElementById('historyNext').addEventListener('click', () => {
    if (currentState.currentConceptIndex < currentState.conceptHistory.length - 1) {
        navigateToConceptIndex(currentState.currentConceptIndex + 1);
    }
});

// Style Suggestions Functionality
async function fetchStyleSuggestions(conceptIndex) {
    // Check cache first
    if (currentState.suggestionCache[conceptIndex]) {
        displaySuggestions(currentState.suggestionCache[conceptIndex]);
        return;
    }

    const concept = currentState.conceptHistory[conceptIndex];
    const loadingEl = document.getElementById('suggestionsLoading');
    const chipsContainer = document.getElementById('suggestionsChips');

    // Show loading state
    loadingEl.classList.remove('hidden');
    chipsContainer.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE_URL}/api/suggest-refinements`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: concept.imageUrl,
                description: concept.description,
                query: currentState.query
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const suggestions = data.suggestions || [];

        // Cache the suggestions
        currentState.suggestionCache[conceptIndex] = suggestions;

        // Display suggestions
        displaySuggestions(suggestions);

    } catch (error) {
        console.error('Error fetching suggestions:', error);
        // Display fallback suggestions on error
        const fallbackSuggestions = [
            {title: 'Color Variation', description: 'Try a different color palette while maintaining the overall aesthetic'},
            {title: 'Length Adjustment', description: 'Adjust the length for a different silhouette'},
            {title: 'Detail Enhancement', description: 'Add decorative elements or embellishments'},
            {title: 'Silhouette Change', description: 'Modify the overall shape and fit'}
        ];
        displaySuggestions(fallbackSuggestions);
    } finally {
        // Hide loading state
        loadingEl.classList.add('hidden');
    }
}

function displaySuggestions(suggestions) {
    const chipsContainer = document.getElementById('suggestionsChips');
    chipsContainer.innerHTML = '';

    if (!suggestions || suggestions.length === 0) {
        chipsContainer.innerHTML = '<p style="color: #6b6b6b; font-size: 0.875rem;">No suggestions available</p>';
        return;
    }

    suggestions.forEach(suggestion => {
        const chip = document.createElement('div');
        chip.className = 'suggestion-chip';

        // Create title element
        const title = document.createElement('div');
        title.className = 'suggestion-chip-title';
        title.textContent = suggestion.title || 'Style Variation';

        // Create description element
        const description = document.createElement('div');
        description.className = 'suggestion-chip-description';
        description.textContent = suggestion.description || suggestion;

        chip.appendChild(title);
        chip.appendChild(description);

        // Click handler to populate refinement input with description
        chip.addEventListener('click', () => {
            const refinementInput = document.getElementById('refinementInput');
            refinementInput.value = suggestion.description || suggestion;
            refinementInput.focus();

            // Add visual feedback
            chip.style.transform = 'scale(0.95)';
            setTimeout(() => {
                chip.style.transform = '';
            }, 150);
        });

        chipsContainer.appendChild(chip);
    });
}

// Refinement Functionality
document.getElementById('refineButton').addEventListener('click', handleRefinement);
document.getElementById('refinementInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        handleRefinement();
    }
});

async function handleRefinement() {
    const refinementInput = document.getElementById('refinementInput');
    const refinementPrompt = refinementInput.value.trim();

    if (!refinementPrompt) {
        alert('Please describe how you would like to refine the design');
        return;
    }

    // Initialize and show progress steps
    const steps = PROGRESS_STEPS.refine;
    initializeProgressSteps(steps);
    showLoadingOverlay();

    try {
        let imageData = null;
        let suggestions = null;

        // Step 1: Pre-refinement step
        const preStepEl = document.getElementById(`progress-step-0`);
        preStepEl.classList.add('active');
        await new Promise(resolve => setTimeout(resolve, steps[0].duration));
        preStepEl.classList.remove('active');
        preStepEl.classList.add('completed');

        // Step 2: Refine image
        const imageStepEl = document.getElementById(`progress-step-1`);
        imageStepEl.classList.add('active');

        const currentConcept = currentState.conceptHistory[currentState.currentConceptIndex];
        const response = await fetch(`${API_BASE_URL}/api/refine`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                original_prompt: currentState.query,
                refinement_prompt: refinementPrompt,
                current_image_url: currentConcept.imageUrl
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        imageData = await response.json();
        imageStepEl.classList.remove('active');
        imageStepEl.classList.add('completed');

        // Step 3: Generate style suggestions
        const suggestionsStepEl = document.getElementById(`progress-step-2`);
        suggestionsStepEl.classList.add('active');

        const suggestionsResponse = await fetch(`${API_BASE_URL}/api/suggest-refinements`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: imageData.image_url,
                description: imageData.description,
                query: currentState.query
            })
        });

        if (suggestionsResponse.ok) {
            const suggestionsData = await suggestionsResponse.json();
            suggestions = suggestionsData.suggestions || [];
        } else {
            // Use fallback suggestions if API fails
            suggestions = [
                {title: 'Color Variation', description: 'Try a different color palette while maintaining the overall aesthetic'},
                {title: 'Length Adjustment', description: 'Adjust the length for a different silhouette'},
                {title: 'Detail Enhancement', description: 'Add decorative elements or embellishments'},
                {title: 'Silhouette Change', description: 'Modify the overall shape and fit'}
            ];
        }

        suggestionsStepEl.classList.remove('active');
        suggestionsStepEl.classList.add('completed');

        // Step 4: Finalizing
        const finalStepEl = document.getElementById(`progress-step-3`);
        finalStepEl.classList.add('active');
        await new Promise(resolve => setTimeout(resolve, steps[3].duration));
        finalStepEl.classList.remove('active');
        finalStepEl.classList.add('completed');

        // Add new concept to history
        currentState.conceptHistory.push({
            imageUrl: imageData.image_url,
            description: imageData.description,
            timestamp: Date.now(),
            refinementPrompt: refinementPrompt
        });
        currentState.currentConceptIndex = currentState.conceptHistory.length - 1;

        // Cache suggestions for this concept
        currentState.suggestionCache[currentState.currentConceptIndex] = suggestions;

        // Hide loading overlay and show workbench with everything ready
        hideLoadingOverlay();
        showView('workbench');
        displayConceptWithHistory();

    } catch (error) {
        console.error('Refinement error:', error);
        alert('An error occurred while refining the design. Please try again.');
        hideLoadingOverlay();
        showView('workbench');
    }
}

// Find Products Functionality
document.getElementById('findProductsButton').addEventListener('click', handleFindProducts);

async function handleFindProducts() {
    // Initialize and show progress steps
    const steps = PROGRESS_STEPS.matchProducts;
    initializeProgressSteps(steps);
    showLoadingOverlay();

    try {
        // Get current concept
        const currentConcept = currentState.conceptHistory[currentState.currentConceptIndex];

        // Run progress steps with API call at index 2
        const data = await runProgressSteps(steps, 2, async () => {
            const response = await fetch(`${API_BASE_URL}/api/match-products`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: currentState.query,
                    image_url: currentConcept.imageUrl,
                    description: currentConcept.description
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        });

        currentState.products = data.products;
        displayProducts(data.products, data.match_description);
        hideLoadingOverlay();
        showView('products');

    } catch (error) {
        console.error('Product matching error:', error);
        alert('An error occurred while finding products. Please try again.');
        hideLoadingOverlay();
        showView('workbench');
    }
}

function displayProducts(products, matchDescription) {
    const productsGrid = document.getElementById('productsGrid');
    const productsDescription = document.getElementById('productsDescription');

    // Update concept preview with current concept from history
    const currentConcept = currentState.conceptHistory[currentState.currentConceptIndex];
    const conceptImage = document.getElementById('productsConceptImage');
    const conceptDescription = document.getElementById('productsConceptDescription');

    conceptImage.src = currentConcept.imageUrl;
    conceptDescription.textContent = currentConcept.description || '';

    productsDescription.textContent = matchDescription || 'Here are the products that best match your refined style concept:';

    productsGrid.innerHTML = '';

    if (!products || products.length === 0) {
        productsGrid.innerHTML = '<p>No matching products found. Please try refining your search.</p>';
        return;
    }

    // Check if products have matched_category field (multi-category search)
    const hasCategories = products.some(p => p.matched_category);

    if (hasCategories) {
        // Group products by category
        const productsByCategory = {};
        products.forEach(product => {
            const category = product.matched_category || 'Other';
            if (!productsByCategory[category]) {
                productsByCategory[category] = [];
            }
            productsByCategory[category].push(product);
        });

        // Display products organized by category
        Object.keys(productsByCategory).sort().forEach(category => {
            const categoryProducts = productsByCategory[category];

            // Create category section
            const categorySection = document.createElement('div');
            categorySection.className = 'category-section';

            // Category header
            const categoryHeader = document.createElement('div');
            categoryHeader.className = 'category-header';
            categoryHeader.innerHTML = `
                <h3 class="category-title">${category}</h3>
                <span class="category-count">${categoryProducts.length} item${categoryProducts.length === 1 ? '' : 's'}</span>
            `;
            categorySection.appendChild(categoryHeader);

            // Category products grid
            const categoryGrid = document.createElement('div');
            categoryGrid.className = 'category-products-grid';

            categoryProducts.forEach(product => {
                const productCard = createProductCard(product);
                categoryGrid.appendChild(productCard);
            });

            categorySection.appendChild(categoryGrid);
            productsGrid.appendChild(categorySection);
        });
    } else {
        // Fallback: Display products in single grid (backward compatibility)
        products.forEach(product => {
            const productCard = createProductCard(product);
            productsGrid.appendChild(productCard);
        });
    }
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';

    // Store product data on card element
    card.dataset.productId = product.id;

    // Add click handler to open modal (only when not in selection mode)
    card.addEventListener('click', (e) => {
        // Check if clicking on checkbox
        const checkbox = card.querySelector('.product-selection-checkbox');
        if (checkbox && (e.target === checkbox || checkbox.contains(e.target))) {
            return; // Let checkbox handle its own logic
        }
        showProductModal(product);
    });

    // Add selection checkbox (always visible)
    const selectionOverlay = document.createElement('div');
    selectionOverlay.className = 'product-selection-overlay';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'product-selection-checkbox';
    checkbox.addEventListener('change', (e) => {
        e.stopPropagation();
        toggleProductSelection(product, card);
    });

    selectionOverlay.appendChild(checkbox);

    const img = document.createElement('img');
    img.className = 'product-image';
    img.src = product.image_url || 'https://via.placeholder.com/280x350?text=No+Image';
    img.alt = product.name;

    const info = document.createElement('div');
    info.className = 'product-info';

    // Match badge
    if (product.similarity_score !== undefined) {
        const similarity = document.createElement('div');
        similarity.className = 'product-similarity';
        const percentage = (product.similarity_score * 100).toFixed(0);
        let matchText = 'Good Match';
        if (percentage >= 90) matchText = 'Best Match';
        else if (percentage >= 75) matchText = 'Great Match';
        similarity.textContent = `${matchText} · ${percentage}%`;
        info.appendChild(similarity);
    }

    const name = document.createElement('h3');
    name.className = 'product-name';
    name.textContent = product.name;

    const price = document.createElement('div');
    price.className = 'product-price';

    if (product.price_discounted) {
        price.innerHTML = `
            <span>$${product.price_discounted.toFixed(2)}</span>
            <span style="text-decoration: line-through; color: #6b6b6b; font-size: 0.9rem; margin-left: 0.5rem;">$${product.price_original.toFixed(2)}</span>
        `;
    } else if (product.price) {
        price.textContent = `$${product.price.toFixed(2)}`;
    } else {
        price.textContent = 'Price not available';
    }

    const color = document.createElement('p');
    color.className = 'product-description';
    color.textContent = product.color || '';

    info.appendChild(name);
    info.appendChild(color);
    info.appendChild(price);

    card.appendChild(selectionOverlay);
    card.appendChild(img);
    card.appendChild(info);

    return card;
}

// Product Modal Functionality
function showProductModal(product) {
    const modal = document.getElementById('productModal');

    // Debug: Log the product object to see what data we're receiving
    console.log('Product data:', product);
    console.log('Fabric:', product.fabric);
    console.log('Fit:', product.fit);
    console.log('Pattern:', product.pattern);

    // Set image
    document.getElementById('modalImage').src = product.image_url || 'https://via.placeholder.com/400x500?text=No+Image';

    // Set match badge
    const matchBadge = document.getElementById('modalMatchBadge');
    if (product.similarity_score !== undefined) {
        const percentage = (product.similarity_score * 100).toFixed(0);
        let matchText = 'Good Match';
        if (percentage >= 90) matchText = 'Best Match';
        else if (percentage >= 75) matchText = 'Great Match';
        matchBadge.textContent = `${matchText} · ${percentage}%`;
        matchBadge.style.display = 'block';
    } else {
        matchBadge.style.display = 'none';
    }

    // Set basic info
    document.getElementById('modalProductName').textContent = product.name || 'Product';
    document.getElementById('modalBrand').textContent = product.brand || '';

    // Set price
    const modalPrice = document.getElementById('modalPrice');
    const modalPriceOriginal = document.getElementById('modalPriceOriginal');

    if (product.price_discounted) {
        modalPrice.textContent = `$${product.price_discounted.toFixed(2)}`;
        modalPriceOriginal.textContent = `$${product.price_original.toFixed(2)}`;
        modalPriceOriginal.style.display = 'inline';
    } else if (product.price) {
        modalPrice.textContent = `$${product.price.toFixed(2)}`;
        modalPriceOriginal.style.display = 'none';
    } else {
        modalPrice.textContent = 'Price not available';
        modalPriceOriginal.style.display = 'none';
    }

    // Set description
    document.getElementById('modalDescription').textContent = product.description || 'No description available.';

    // Set detail fields
    document.getElementById('modalCategory').textContent = product.subcategory || product.category || 'N/A';
    document.getElementById('modalColor').textContent = product.secondary_color
        ? `${product.color}, ${product.secondary_color}`
        : (product.color || 'N/A');
    document.getElementById('modalFabric').textContent = product.fabric || 'N/A';
    document.getElementById('modalFit').textContent = product.fit || 'N/A';
    document.getElementById('modalPattern').textContent = product.pattern || 'N/A';
    document.getElementById('modalSeason').textContent = product.season || 'N/A';

    // Optional fields - show/hide if they exist
    const sleeveItem = document.getElementById('modalSleeveItem');
    const neckItem = document.getElementById('modalNeckItem');
    const occasionItem = document.getElementById('modalOccasionItem');
    const styleItem = document.getElementById('modalStyleItem');

    if (product.sleeve_length) {
        document.getElementById('modalSleeve').textContent = product.sleeve_length;
        sleeveItem.style.display = 'flex';
    } else {
        sleeveItem.style.display = 'none';
    }

    if (product.neck_style) {
        document.getElementById('modalNeck').textContent = product.neck_style;
        neckItem.style.display = 'flex';
    } else {
        neckItem.style.display = 'none';
    }

    if (product.occasion) {
        document.getElementById('modalOccasion').textContent = product.occasion;
        occasionItem.style.display = 'flex';
    } else {
        occasionItem.style.display = 'none';
    }

    if (product.style) {
        document.getElementById('modalStyle').textContent = product.style;
        styleItem.style.display = 'flex';
    } else {
        styleItem.style.display = 'none';
    }

    // Show modal
    modal.classList.remove('hidden');
}

function hideProductModal() {
    document.getElementById('productModal').classList.add('hidden');
}

// Modal event listeners
document.getElementById('modalClose').addEventListener('click', hideProductModal);
document.getElementById('modalBackdrop').addEventListener('click', hideProductModal);

// Keyboard navigation for concept history and modal
document.addEventListener('keydown', (e) => {
    // Close modals on Escape key
    if (e.key === 'Escape') {
        const productModal = document.getElementById('productModal');
        const basketModal = document.getElementById('basketModal');

        if (!basketModal.classList.contains('hidden')) {
            hideBasketModal();
            return;
        }

        if (!productModal.classList.contains('hidden')) {
            hideProductModal();
            return;
        }
    }

    // Arrow key navigation for concept history (only on workbench view)
    if (!views.workbench.classList.contains('hidden')) {
        if (e.key === 'ArrowLeft' && currentState.currentConceptIndex > 0) {
            e.preventDefault();
            navigateToConceptIndex(currentState.currentConceptIndex - 1);
        } else if (e.key === 'ArrowRight' &&
                   currentState.currentConceptIndex < currentState.conceptHistory.length - 1) {
            e.preventDefault();
            navigateToConceptIndex(currentState.currentConceptIndex + 1);
        }
    }
});

// Navigation
document.getElementById('backButton').addEventListener('click', () => {
    showView('search');
});

document.getElementById('backToWorkbenchButton').addEventListener('click', () => {
    showView('workbench');
});

document.getElementById('backToProductsButton').addEventListener('click', () => {
    showView('products');
});

// Product Selection for Look Creation
// Checkboxes are now always visible, no need for enable/disable functions

function toggleProductSelection(product, cardElement) {
    const productId = product.id;
    const index = currentState.selectedProducts.findIndex(p => p.id === productId);

    if (index >= 0) {
        // Deselect product
        currentState.selectedProducts.splice(index, 1);
        cardElement.classList.remove('selected');
    } else {
        // Check if we can select more (max 3)
        if (currentState.selectedProducts.length >= 3) {
            alert('You can select a maximum of 3 products to create a look');
            // Uncheck the checkbox
            const checkbox = cardElement.querySelector('.product-selection-checkbox');
            checkbox.checked = false;
            return;
        }

        // Select product
        currentState.selectedProducts.push(product);
        cardElement.classList.add('selected');
    }

    updateSelectionBar();
}

function updateSelectionBar() {
    const selectionBar = document.getElementById('selectionBar');
    const selectionCount = document.getElementById('selectionCount');
    const createLookButton = document.getElementById('createLookButton');

    const count = currentState.selectedProducts.length;

    if (count === 0) {
        selectionBar.classList.add('hidden');
    } else {
        selectionBar.classList.remove('hidden');
        selectionCount.textContent = `${count} item${count === 1 ? '' : 's'} selected`;

        // Enable/disable create look button
        if (count >= 2 && count <= 3) {
            createLookButton.disabled = false;
        } else {
            createLookButton.disabled = true;
        }
    }
}

function clearSelection() {
    currentState.selectedProducts = [];

    // Uncheck all checkboxes and remove selected class
    document.querySelectorAll('.product-card').forEach(card => {
        card.classList.remove('selected');
        const checkbox = card.querySelector('.product-selection-checkbox');
        if (checkbox) {
            checkbox.checked = false;
        }
    });

    updateSelectionBar();
}

// Selection Bar Event Listeners
document.getElementById('clearSelectionButton').addEventListener('click', clearSelection);
document.getElementById('createLookButton').addEventListener('click', handleCreateLook);

// Create Look Functionality
async function handleCreateLook() {
    if (currentState.selectedProducts.length < 2 || currentState.selectedProducts.length > 3) {
        alert('Please select 2-3 products to create a look');
        return;
    }

    // Initialize and show progress steps
    const steps = PROGRESS_STEPS.createLook;
    initializeProgressSteps(steps);
    showLoadingOverlay();

    try {
        // Run progress steps with API call at index 1
        const data = await runProgressSteps(steps, 1, async () => {
            const response = await fetch(`${API_BASE_URL}/api/create-look`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    products: currentState.selectedProducts
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        });

        // Store generated look
        currentState.generatedLook = data;

        // Display the look
        displayGeneratedLook(data);

        // Hide loading overlay and show look builder view
        hideLoadingOverlay();
        showView('lookBuilder');

    } catch (error) {
        console.error('Look creation error:', error);
        alert('An error occurred while creating your look. Please try again.');
        hideLoadingOverlay();
        showView('products');
    }
}

function displayGeneratedLook(lookData) {
    // Set look image
    document.getElementById('lookImage').src = lookData.look_image_url;

    // Set description
    document.getElementById('lookDescription').textContent = lookData.description;

    // Display selected products
    const productsGrid = document.getElementById('lookProductsGrid');
    productsGrid.innerHTML = '';

    lookData.products.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'look-product-card';

        const img = document.createElement('img');
        img.src = product.image_url || 'https://via.placeholder.com/150x200?text=No+Image';
        img.alt = product.name;
        img.className = 'look-product-image';

        const name = document.createElement('div');
        name.className = 'look-product-name';
        name.textContent = product.name;

        const price = document.createElement('div');
        price.className = 'look-product-price';
        if (product.price_discounted) {
            price.textContent = `$${product.price_discounted.toFixed(2)}`;
        } else if (product.price) {
            price.textContent = `$${product.price.toFixed(2)}`;
        }

        productCard.appendChild(img);
        productCard.appendChild(name);
        productCard.appendChild(price);

        // Add click handler to show modal
        productCard.addEventListener('click', () => showProductModal(product));

        productsGrid.appendChild(productCard);
    });
}

// Look Builder Actions
document.getElementById('tryDifferentCombinationButton').addEventListener('click', () => {
    // Go back to products view with selection cleared
    clearSelection();
    showView('products');
});

document.getElementById('startNewSearchButton').addEventListener('click', () => {
    // Reset state
    currentState.selectedProducts = [];
    currentState.generatedLook = null;
    showView('search');
});

// Add to Basket Functionality
document.getElementById('addToBasketButton').addEventListener('click', () => {
    if (!currentState.generatedLook) {
        alert('No look to add to basket');
        return;
    }
    showBasketModal();
});

function showBasketModal() {
    const modal = document.getElementById('basketModal');
    const lookDescription = document.getElementById('basketLookDescription');
    const productsGrid = document.getElementById('basketProductsGrid');

    // Set look description
    lookDescription.textContent = currentState.generatedLook.description || 'Your styled look has been added to your basket!';

    // Clear and populate products grid
    productsGrid.innerHTML = '';

    currentState.generatedLook.products.forEach(product => {
        const productItem = document.createElement('div');
        productItem.className = 'basket-product-item';

        const img = document.createElement('img');
        img.src = product.image_url || 'https://via.placeholder.com/100x120?text=No+Image';
        img.alt = product.name;
        img.className = 'basket-product-thumbnail';

        const name = document.createElement('div');
        name.className = 'basket-product-name';
        name.textContent = product.name;

        productItem.appendChild(img);
        productItem.appendChild(name);

        productsGrid.appendChild(productItem);
    });

    // Show modal
    modal.classList.remove('hidden');
}

function hideBasketModal() {
    document.getElementById('basketModal').classList.add('hidden');
}

// Basket Modal Event Listeners
document.getElementById('basketModalClose').addEventListener('click', hideBasketModal);
document.getElementById('basketModalBackdrop').addEventListener('click', hideBasketModal);

document.getElementById('returnToConceptButton').addEventListener('click', () => {
    hideBasketModal();
    showView('workbench');
});

document.getElementById('createNewLookButton').addEventListener('click', () => {
    hideBasketModal();
    // Reset state
    currentState.selectedProducts = [];
    currentState.generatedLook = null;
    showView('search');
});

// Style Concept Modal Functionality
function showConceptModal(concept) {
    const modal = document.getElementById('conceptModal');

    // Set concept image (use actual image or fallback to gradient)
    const conceptImage = document.getElementById('conceptModalImage');
    if (concept.imageUrl) {
        conceptImage.style.backgroundImage = `url('${concept.imageUrl}')`;
        conceptImage.style.backgroundSize = 'cover';
        conceptImage.style.backgroundPosition = 'center';
    } else {
        conceptImage.style.background = concept.gradient;
    }

    // Set concept details
    document.getElementById('conceptModalTitle').textContent = concept.title;
    document.getElementById('conceptModalTagline').textContent = concept.tagline;
    document.getElementById('conceptModalDescription').textContent = concept.description;

    // Store concept data for selection
    modal.dataset.conceptId = concept.id;

    // Show modal
    modal.classList.remove('hidden');
}

function hideConceptModal() {
    document.getElementById('conceptModal').classList.add('hidden');
}

function selectConcept() {
    const modal = document.getElementById('conceptModal');
    const conceptId = modal.dataset.conceptId;
    const concept = STYLE_CONCEPTS.find(c => c.id === conceptId);

    if (!concept) {
        console.error('Concept not found');
        return;
    }

    // Hide modal
    hideConceptModal();

    // Set query and trigger search
    const searchInput = document.getElementById('searchInput');
    searchInput.value = concept.query;

    // Use the existing handleSearch function
    handleSearch();
}

// Toggle Button Functionality
function initializeToggleButtons() {
    const conceptsButton = document.getElementById('conceptsToggleButton');
    const uploadButton = document.getElementById('uploadToggleButton');
    const conceptsContent = document.getElementById('conceptsContent');
    const uploadContent = document.getElementById('uploadContent');

    let activeContent = null;
    let activeButton = null;

    conceptsButton.addEventListener('click', () => {
        if (activeContent === conceptsContent) {
            // Close if already open
            conceptsContent.classList.remove('show');
            conceptsContent.classList.add('hidden');
            conceptsButton.classList.remove('active');
            activeContent = null;
            activeButton = null;
        } else {
            // Close any open content
            if (activeContent) {
                activeContent.classList.remove('show');
                activeContent.classList.add('hidden');
            }
            if (activeButton) {
                activeButton.classList.remove('active');
            }

            // Open concepts
            conceptsContent.classList.remove('hidden');
            setTimeout(() => conceptsContent.classList.add('show'), 10);
            conceptsButton.classList.add('active');
            activeContent = conceptsContent;
            activeButton = conceptsButton;
        }
    });

    uploadButton.addEventListener('click', () => {
        if (activeContent === uploadContent) {
            // Close if already open
            uploadContent.classList.remove('show');
            uploadContent.classList.add('hidden');
            uploadButton.classList.remove('active');
            activeContent = null;
            activeButton = null;
        } else {
            // Close any open content
            if (activeContent) {
                activeContent.classList.remove('show');
                activeContent.classList.add('hidden');
            }
            if (activeButton) {
                activeButton.classList.remove('active');
            }

            // Open upload
            uploadContent.classList.remove('hidden');
            setTimeout(() => uploadContent.classList.add('show'), 10);
            uploadButton.classList.add('active');
            activeContent = uploadContent;
            activeButton = uploadButton;
        }
    });
}

// Image Upload Functionality
let uploadedImageData = null;

function initializeImageUpload() {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('styleImageInput');
    const preview = document.getElementById('uploadPreview');
    const previewImage = document.getElementById('uploadPreviewImage');
    const removeButton = document.getElementById('uploadRemoveButton');
    const descriptionSection = document.getElementById('uploadDescriptionSection');
    const searchButton = document.getElementById('searchByImageButton');

    // Click to upload
    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change handler
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleImageFile(file);
        }
    });

    // Drag and drop handlers
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleImageFile(file);
        } else {
            alert('Please upload an image file (PNG, JPG, or WEBP)');
        }
    });

    // Remove uploaded image
    removeButton.addEventListener('click', (e) => {
        e.stopPropagation();
        removeUploadedImage();
    });

    // Search by image button
    searchButton.addEventListener('click', handleSearchByImage);
}

function handleImageFile(file) {
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }

    // Validate file type
    if (!['image/png', 'image/jpeg', 'image/jpg', 'image/webp'].includes(file.type)) {
        alert('Please upload a PNG, JPG, or WEBP image');
        return;
    }

    // Read file and convert to base64
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadedImageData = e.target.result;

        // Show preview
        const dropzone = document.getElementById('uploadDropzone');
        const preview = document.getElementById('uploadPreview');
        const previewImage = document.getElementById('uploadPreviewImage');
        const descriptionSection = document.getElementById('uploadDescriptionSection');
        const searchButton = document.getElementById('searchByImageButton');

        previewImage.src = uploadedImageData;
        dropzone.classList.add('hidden');
        preview.classList.remove('hidden');
        descriptionSection.classList.remove('hidden');
        searchButton.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}

function removeUploadedImage() {
    uploadedImageData = null;

    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('styleImageInput');
    const preview = document.getElementById('uploadPreview');
    const descriptionSection = document.getElementById('uploadDescriptionSection');
    const descriptionInput = document.getElementById('uploadDescriptionInput');
    const searchButton = document.getElementById('searchByImageButton');

    fileInput.value = '';
    descriptionInput.value = '';
    dropzone.classList.remove('hidden');
    preview.classList.add('hidden');
    descriptionSection.classList.add('hidden');
    searchButton.classList.add('hidden');
}

async function handleSearchByImage() {
    if (!uploadedImageData) {
        alert('Please upload an image first');
        return;
    }

    const descriptionInput = document.getElementById('uploadDescriptionInput');
    const additionalDescription = descriptionInput.value.trim();

    // Initialize and show progress steps
    const steps = PROGRESS_STEPS.search;
    initializeProgressSteps(steps);
    showLoadingOverlay();

    try {
        let imageData = null;
        let suggestions = null;

        // Step 1-2: Pre-image generation steps
        for (let i = 0; i < 2; i++) {
            const stepEl = document.getElementById(`progress-step-${i}`);
            stepEl.classList.add('active');
            await new Promise(resolve => setTimeout(resolve, steps[i].duration));
            stepEl.classList.remove('active');
            stepEl.classList.add('completed');
        }

        // Step 3: Generate concept from uploaded image
        const imageStepEl = document.getElementById(`progress-step-2`);
        imageStepEl.classList.add('active');

        const response = await fetch(`${API_BASE_URL}/api/search-by-image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_data: uploadedImageData,
                additional_description: additionalDescription
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        imageData = await response.json();
        imageStepEl.classList.remove('active');
        imageStepEl.classList.add('completed');

        // Step 4: Generate style suggestions
        const suggestionsStepEl = document.getElementById(`progress-step-3`);
        suggestionsStepEl.classList.add('active');

        const suggestionsResponse = await fetch(`${API_BASE_URL}/api/suggest-refinements`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: imageData.image_url,
                description: imageData.description,
                query: imageData.analyzed_style || 'custom uploaded style'
            })
        });

        if (suggestionsResponse.ok) {
            const suggestionsData = await suggestionsResponse.json();
            suggestions = suggestionsData.suggestions || [];
        } else {
            // Use fallback suggestions if API fails
            suggestions = [
                {title: 'Color Variation', description: 'Try a different color palette while maintaining the overall aesthetic'},
                {title: 'Length Adjustment', description: 'Adjust the length for a different silhouette'},
                {title: 'Detail Enhancement', description: 'Add decorative elements or embellishments'},
                {title: 'Silhouette Change', description: 'Modify the overall shape and fit'}
            ];
        }

        suggestionsStepEl.classList.remove('active');
        suggestionsStepEl.classList.add('completed');

        // Step 5: Finalizing
        const finalStepEl = document.getElementById(`progress-step-4`);
        finalStepEl.classList.add('active');
        await new Promise(resolve => setTimeout(resolve, steps[4].duration));
        finalStepEl.classList.remove('active');
        finalStepEl.classList.add('completed');

        // Set query from analyzed style
        currentState.query = imageData.analyzed_style || 'custom uploaded style';

        // Initialize concept history with first image
        currentState.conceptHistory = [{
            imageUrl: imageData.image_url,
            description: imageData.description,
            timestamp: Date.now(),
            refinementPrompt: null  // Original upload
        }];
        currentState.currentConceptIndex = 0;

        // Cache suggestions for this concept
        currentState.suggestionCache[0] = suggestions;

        // Clear uploaded image and close upload content
        removeUploadedImage();
        const uploadContent = document.getElementById('uploadContent');
        const uploadButton = document.getElementById('uploadToggleButton');
        if (uploadContent.classList.contains('show')) {
            uploadContent.classList.remove('show');
            uploadContent.classList.add('hidden');
            uploadButton.classList.remove('active');
        }

        // Hide loading overlay and show workbench with everything ready
        hideLoadingOverlay();
        showView('workbench');
        displayConceptWithHistory();

    } catch (error) {
        console.error('Image search error:', error);
        alert('An error occurred while processing your image. Please try again.');
        hideLoadingOverlay();
        showView('search');
    }
}

// Initialize concept cards on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize toggle buttons
    initializeToggleButtons();

    // Initialize image upload
    initializeImageUpload();

    const conceptsGrid = document.getElementById('styleConceptsGrid');

    if (!conceptsGrid) return;

    STYLE_CONCEPTS.forEach(concept => {
        const card = document.createElement('div');
        card.className = 'concept-card';
        card.addEventListener('click', () => showConceptModal(concept));

        // Use <img> tag if imageUrl exists, otherwise use gradient background
        if (concept.imageUrl) {
            const img = document.createElement('img');
            img.className = 'concept-card-image';
            img.src = concept.imageUrl;
            img.alt = concept.title;
            // Add error handler to fallback to gradient if image fails
            img.onerror = function() {
                const div = document.createElement('div');
                div.className = 'concept-card-image';
                div.style.background = concept.gradient;
                this.replaceWith(div);
            };
            card.appendChild(img);
        } else {
            const imageDiv = document.createElement('div');
            imageDiv.className = 'concept-card-image';
            imageDiv.style.background = concept.gradient;
            card.appendChild(imageDiv);
        }

        const info = document.createElement('div');
        info.className = 'concept-card-info';

        const title = document.createElement('h3');
        title.className = 'concept-card-title';
        title.textContent = concept.title;

        const tagline = document.createElement('p');
        tagline.className = 'concept-card-tagline';
        tagline.textContent = concept.tagline;

        info.appendChild(title);
        info.appendChild(tagline);

        card.appendChild(info);

        conceptsGrid.appendChild(card);
    });

    // Attach modal event listeners
    const conceptModalClose = document.getElementById('conceptModalClose');
    const conceptModalBackdrop = document.getElementById('conceptModalBackdrop');
    const selectConceptButton = document.getElementById('selectConceptButton');

    if (conceptModalClose) {
        conceptModalClose.addEventListener('click', hideConceptModal);
    }
    if (conceptModalBackdrop) {
        conceptModalBackdrop.addEventListener('click', hideConceptModal);
    }
    if (selectConceptButton) {
        selectConceptButton.addEventListener('click', selectConcept);
    }

    // ESC key to close concept modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const conceptModal = document.getElementById('conceptModal');
            if (conceptModal && !conceptModal.classList.contains('hidden')) {
                hideConceptModal();
            }
        }
    });
});

import Fuse from 'fuse.js';
import { IconInfo } from '../types.js';

interface SearchableIcon {
    name: string;
    tags: string;
    category: string;
    featured: boolean;
    version: string;
    searchableText: {
        name: string;
        tags: string;
        category: string;
        all: string;
    };
}

interface SearchResult {
    item: SearchableIcon;
    score: number;
}

/**
 * Prepares an icon for searching by creating searchable text fields
 */
function prepareIconForSearch(icon: IconInfo): SearchableIcon {
    // Process tags once for efficiency
    const processedTags = 
        icon.tags
            ?.split(',')
            .map((tag: string) => tag.trim())
            .filter((tag: string) => tag) || [];

    const baseSearchText = {
        name: icon.name.toLowerCase(),
        tags: processedTags.join(' ').toLowerCase(),
        category: icon.category?.toLowerCase() || '',
        all: [
            icon.name,
            icon.name.replace(/-/g, ' '), // Add version with hyphens replaced by spaces
            icon.name.replace(/-/g, ''),  // Add version with hyphens removed
            // Add individual parts of hyphenated names
            ...(icon.name.includes('-') ? icon.name.split('-') : []),
            ...processedTags,
            icon.category,
            ...processedTags.flatMap((tag: string) => tag.split(/[\s-]/))
        ]
            .filter(Boolean)  // Remove any empty strings
            .join(' ')
            .toLowerCase(),
    };

    return {
        ...icon,
        searchableText: baseSearchText,
    };
}

/**
 * Process search terms and handle special cases like hyphenated words
 */
function processSearchTerms(search: string): string[] {
    // Split by commas first to handle multiple search terms
    const searchParts = search.split(',').map(part => part.trim());
    
    const allTerms = new Set<string>();
    
    for (const part of searchParts) {
        const normalizedSearch = part.toLowerCase().replace(/-/g, ' ');
        const searchTerms = normalizedSearch
            .split(' ')
            .filter(term => term.length > 0);
        
        // Special case: if we have terms like "chart" and "up", also add "chart-up" as a search term
        if (searchTerms.length > 1) {
            for (let i = 0; i < searchTerms.length - 1; i++) {
                allTerms.add(`${searchTerms[i]}-${searchTerms[i+1]}`);
            }
        }
        
        // Add all individual terms
        searchTerms.forEach(term => allTerms.add(term));
    }
    
    return Array.from(allTerms);
}

/**
 * Perform fuzzy search on icons using Fuse.js
 */
export function searchIcons(icons: IconInfo[], searchQuery: string): IconInfo[] {
    if (!searchQuery || !icons?.length) {
        return [];
    }

    // Split search query by commas
    const searchQueries = searchQuery.split(',').map(q => q.trim()).filter(q => q);
    
    // Prepare icons for searching
    const searchableIcons = icons.map(prepareIconForSearch);

    // Initialize Fuse with our configuration
    const fuse = new Fuse(searchableIcons, {
        keys: [
            { name: 'searchableText.name', weight: 2.0 },    // Highest priority for name matches
            { name: 'searchableText.tags', weight: 1.5 },    // High priority for tag matches
            { name: 'searchableText.category', weight: 0.8 }, // Lower priority for category
            { name: 'searchableText.all', weight: 0.5 },     // Lowest priority for general text
        ],
        includeScore: true,
        threshold: 0.2,
        shouldSort: true,
        findAllMatches: true,
        ignoreLocation: false,
        location: 0,
        distance: 600,
        minMatchCharLength: 2,
        useExtendedSearch: true,
    });

    // Store all results in a Map to deduplicate
    const allResults = new Map<string, { item: IconInfo; score: number }>();

    // Search for each comma-separated query
    for (const query of searchQueries) {
        const searchTerms = processSearchTerms(query);
        
        // Initialize results with all icons and zero scores for this query
        let queryResults: SearchResult[] = searchableIcons.map(icon => ({
            item: icon,
            score: 0,
        }));

        // Search for each term and intersect results while keeping scores
        for (const term of searchTerms) {
            const termResults = fuse.search(term);
            const termScores = new Map(termResults.map(r => [(r.item as SearchableIcon).searchableText.name, r.score || 0]));

            queryResults = queryResults
                .filter(r => termResults.some(tr => (tr.item as SearchableIcon).searchableText.name === r.item.searchableText.name))
                .map(r => {
                    const nameWithSpaces = r.item.searchableText.name;
                    const nameWithoutHyphens = r.item.searchableText.name.replace(/-/g, '');
                    
                    const nameWords = r.item.searchableText.name.split(/[\s-]/);
                    
                    // Check for exact word matches (much stronger boost)
                    const exactWordMatch = 
                        nameWords.includes(term) || 
                        r.item.searchableText.name === term ||
                        nameWithoutHyphens === term;
                    
                    // Check for exact matches in different name formats
                    const exactMatchInName = 
                        r.item.searchableText.name.includes(term) || 
                        nameWithoutHyphens.includes(term);
                    
                    // Check for exact matches in tags
                    const exactMatchInTags = r.item.searchableText.tags.includes(term);
                    
                    const baseScore = termScores.get(r.item.searchableText.name) || 0;

                    // Apply bonuses for exact matches (reduce score since lower is better)
                    const finalScore =
                        baseScore *
                        (exactWordMatch ? 0.1  // 90% score reduction for exact word match
                            : exactMatchInName ? 0.3  // 70% score reduction for exact name match
                            : exactMatchInTags ? 0.5  // 50% score reduction for exact tag match
                            : 1);

                    return {
                        item: r.item,
                        score: r.score + finalScore,
                    };
                });
        }

        // Add results to the overall results map, keeping the best score for each icon
        for (const result of queryResults) {
            const existingResult = allResults.get(result.item.name);
            if (!existingResult || result.score < existingResult.score) {
                allResults.set(result.item.name, {
                    item: {
                        name: result.item.name,
                        tags: result.item.tags,
                        category: result.item.category,
                        featured: result.item.featured,
                        version: result.item.version,
                    },
                    score: result.score
                });
            }
        }
    }

    // Convert map to array and sort by score
    return Array.from(allResults.values())
        .sort((a, b) => a.score - b.score)
        .map(result => result.item);
} 
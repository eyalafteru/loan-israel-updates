/**
 * KeywordDensityAnalyzer - Advanced Hebrew SEO Keyword Density Module
 * 
 * Features:
 * - Hebrew-specific text normalization (niqqud removal, prefix handling)
 * - Zone-weighted density scoring (H1 x3, H2-H6 x2, Body x1)
 * - AI-ready fix suggestions with Claude Code integration
 * - Visual highlighting of keyword occurrences
 */

class KeywordDensityAnalyzer {
    constructor(htmlContent, keyword, options = {}) {
        this.htmlContent = htmlContent;
        this.keyword = keyword;
        this.options = {
            optimalRange: [1.5, 2.5],
            warningRange: [1.0, 3.0],
            useNLP: false, // Set to true when NLP service is available
            ...options
        };
        
        // Zone weights for SEO importance
        this.zoneWeights = {
            title: 3,
            metaDescription: 2,
            h1: 3,
            h2: 2,
            h3: 1.5,
            h4: 1.5,
            h5: 1.5,
            h6: 1.5,
            body: 1
        };
        
        // Hebrew prefixes for variation matching
        this.hebrewPrefixes = ['ה', 'ב', 'ל', 'מ', 'ו', 'כ', 'ש', 'וה', 'וב', 'ול', 'שה', 'שב', 'של'];
        
        // Cache for parsed content
        this._parsedContent = null;
        this._analysisResult = null;
    }
    
    /**
     * Normalize Hebrew text for analysis
     * - Removes niqqud (vowel marks)
     * - Normalizes whitespace
     * - Removes punctuation
     */
    normalizeHebrew(text) {
        if (!text) return '';
        return text
            .replace(/[\u0591-\u05C7]/g, '')  // Remove niqqud
            .replace(/[^\u0590-\u05FF\sa-zA-Z0-9]/g, ' ')  // Keep Hebrew, English, numbers
            .replace(/\s+/g, ' ')
            .trim();
    }
    
    /**
     * Extract Hebrew text only (for word counting)
     */
    extractHebrewWords(text) {
        const normalized = this.normalizeHebrew(text);
        return normalized.split(/\s+/).filter(word => 
            word.length > 0 && /[\u0590-\u05FF]/.test(word)
        );
    }
    
    /**
     * Generate Hebrew variations of a keyword
     */
    getKeywordVariations(keyword) {
        const normalized = this.normalizeHebrew(keyword);
        const words = normalized.split(/\s+/);
        const variations = new Set([normalized]);
        
        if (words.length === 1) {
            const word = words[0];
            // Add prefixed versions
            this.hebrewPrefixes.forEach(prefix => {
                variations.add(prefix + word);
            });
            
            // Common plural forms
            if (word.endsWith('ה')) {
                variations.add(word.slice(0, -1) + 'ות'); // הלוואה -> הלוואות
                variations.add(word.slice(0, -1) + 'ת');  // הלוואה -> הלוואת
            }
            variations.add(word + 'ים');
            variations.add(word + 'ות');
            
            // With article
            if (!word.startsWith('ה')) {
                variations.add('ה' + word);
            }
        } else {
            // Multi-word: add prefix to first word
            const firstWord = words[0];
            const rest = words.slice(1).join(' ');
            
            this.hebrewPrefixes.slice(0, 7).forEach(prefix => {
                if (!firstWord.startsWith(prefix)) {
                    variations.add(prefix + firstWord + ' ' + rest);
                }
            });
        }
        
        return Array.from(variations);
    }
    
    /**
     * Parse HTML content into segments
     */
    parseHTML() {
        if (this._parsedContent) return this._parsedContent;
        
        const parser = new DOMParser();
        const doc = parser.parseFromString(this.htmlContent, 'text/html');
        
        // Extract title
        const titleEl = doc.querySelector('title');
        const title = titleEl ? titleEl.textContent.trim() : '';
        
        // Extract meta description
        const metaDesc = doc.querySelector('meta[name="description"]');
        const metaDescription = metaDesc ? metaDesc.getAttribute('content') || '' : '';
        
        // Extract headings
        const headings = {
            h1: Array.from(doc.querySelectorAll('h1')).map(el => ({
                text: el.textContent.trim(),
                html: el.innerHTML
            })),
            h2: Array.from(doc.querySelectorAll('h2')).map(el => ({
                text: el.textContent.trim(),
                html: el.innerHTML
            })),
            h3: Array.from(doc.querySelectorAll('h3')).map(el => ({
                text: el.textContent.trim(),
                html: el.innerHTML
            })),
            h4: Array.from(doc.querySelectorAll('h4')).map(el => ({
                text: el.textContent.trim(),
                html: el.innerHTML
            })),
            h5: Array.from(doc.querySelectorAll('h5')).map(el => ({
                text: el.textContent.trim(),
                html: el.innerHTML
            })),
            h6: Array.from(doc.querySelectorAll('h6')).map(el => ({
                text: el.textContent.trim(),
                html: el.innerHTML
            }))
        };
        
        // Extract body text (excluding scripts, styles, headings)
        const clone = doc.body.cloneNode(true);
        
        // Remove elements we don't want in body text
        const removeSelectors = ['script', 'style', 'noscript', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
        removeSelectors.forEach(sel => {
            clone.querySelectorAll(sel).forEach(el => el.remove());
        });
        
        const bodyText = clone.textContent || '';
        
        // Get full text for general analysis
        const fullText = doc.body ? doc.body.textContent : '';
        
        this._parsedContent = {
            title,
            metaDescription,
            headings,
            bodyText: bodyText.trim(),
            fullText: fullText.trim(),
            doc
        };
        
        return this._parsedContent;
    }
    
    /**
     * Count keyword occurrences in text
     */
    countOccurrences(text, variations = null) {
        const normalizedText = this.normalizeHebrew(text);
        const keywordVariations = variations || this.getKeywordVariations(this.keyword);
        
        let totalCount = 0;
        const variationCounts = {};
        const positions = [];
        
        keywordVariations.forEach(variation => {
            try {
                const regex = new RegExp(variation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
                const matches = [...normalizedText.matchAll(regex)];
                const count = matches.length;
                
                if (count > 0) {
                    variationCounts[variation] = count;
                    totalCount += count;
                    
                    matches.forEach(match => {
                        positions.push({
                            start: match.index,
                            end: match.index + match[0].length,
                            variation: variation,
                            matchedText: match[0]
                        });
                    });
                }
            } catch (e) {
                console.warn('Regex error for variation:', variation, e);
            }
        });
        
        return { totalCount, variationCounts, positions };
    }
    
    /**
     * Calculate weighted density score
     */
    calculateWeightedDensity() {
        const parsed = this.parseHTML();
        const variations = this.getKeywordVariations(this.keyword);
        
        // Analyze each zone
        const zones = {};
        
        // Title
        const titleResult = this.countOccurrences(parsed.title, variations);
        zones.title = {
            text: parsed.title,
            count: titleResult.totalCount,
            found: titleResult.totalCount > 0,
            weight: this.zoneWeights.title,
            weightedCount: titleResult.totalCount * this.zoneWeights.title
        };
        
        // Meta Description
        const metaResult = this.countOccurrences(parsed.metaDescription, variations);
        zones.metaDescription = {
            text: parsed.metaDescription,
            count: metaResult.totalCount,
            found: metaResult.totalCount > 0,
            weight: this.zoneWeights.metaDescription,
            weightedCount: metaResult.totalCount * this.zoneWeights.metaDescription
        };
        
        // Headings by level
        ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(level => {
            const headingsOfLevel = parsed.headings[level] || [];
            const analyzedHeadings = headingsOfLevel.map(h => {
                const result = this.countOccurrences(h.text, variations);
                return {
                    text: h.text,
                    count: result.totalCount,
                    found: result.totalCount > 0,
                    weight: this.zoneWeights[level],
                    weightedCount: result.totalCount * this.zoneWeights[level]
                };
            });
            
            zones[level] = {
                items: analyzedHeadings,
                totalCount: analyzedHeadings.reduce((sum, h) => sum + h.count, 0),
                foundCount: analyzedHeadings.filter(h => h.found).length,
                totalItems: analyzedHeadings.length,
                weightedCount: analyzedHeadings.reduce((sum, h) => sum + h.weightedCount, 0)
            };
        });
        
        // Body text
        const bodyResult = this.countOccurrences(parsed.bodyText, variations);
        const bodyWords = this.extractHebrewWords(parsed.bodyText);
        zones.body = {
            count: bodyResult.totalCount,
            wordCount: bodyWords.length,
            weight: this.zoneWeights.body,
            weightedCount: bodyResult.totalCount * this.zoneWeights.body,
            positions: bodyResult.positions,
            variationCounts: bodyResult.variationCounts
        };
        
        // Calculate total weighted score
        let totalWeightedCount = zones.title.weightedCount + zones.metaDescription.weightedCount + zones.body.weightedCount;
        ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(level => {
            totalWeightedCount += zones[level].weightedCount;
        });
        
        // Total weighted words
        let totalWeightedWords = zones.body.wordCount * this.zoneWeights.body;
        totalWeightedWords += this.extractHebrewWords(parsed.title).length * this.zoneWeights.title;
        totalWeightedWords += this.extractHebrewWords(parsed.metaDescription).length * this.zoneWeights.metaDescription;
        
        ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(level => {
            parsed.headings[level].forEach(h => {
                totalWeightedWords += this.extractHebrewWords(h.text).length * this.zoneWeights[level];
            });
        });
        
        // Calculate densities
        const weightedDensity = totalWeightedWords > 0 
            ? (totalWeightedCount / totalWeightedWords * 100) 
            : 0;
        
        const simpleDensity = zones.body.wordCount > 0
            ? (zones.body.count / zones.body.wordCount * 100)
            : 0;
        
        return {
            zones,
            totalWeightedCount,
            totalWeightedWords,
            weightedDensity: Math.round(weightedDensity * 100) / 100,
            simpleDensity: Math.round(simpleDensity * 100) / 100,
            totalOccurrences: zones.title.count + zones.metaDescription.count + zones.body.count +
                ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].reduce((sum, l) => sum + zones[l].totalCount, 0),
            totalWords: zones.body.wordCount
        };
    }
    
    /**
     * Calculate overall score (0-100)
     */
    calculateScore(density) {
        const [optimalMin, optimalMax] = this.options.optimalRange;
        const [warningMin, warningMax] = this.options.warningRange;
        
        if (density >= optimalMin && density <= optimalMax) {
            return 100; // Ideal
        } else if (density >= warningMin && density < optimalMin) {
            // Low but acceptable
            return 60 + ((density - warningMin) / (optimalMin - warningMin)) * 30;
        } else if (density > optimalMax && density <= warningMax) {
            // High but acceptable
            return 60 + ((warningMax - density) / (warningMax - optimalMax)) * 30;
        } else if (density < warningMin) {
            // Too thin
            return Math.max(0, 60 * (density / warningMin));
        } else {
            // Stuffing
            return Math.max(0, 60 - ((density - warningMax) * 20));
        }
    }
    
    /**
     * Get status based on density
     */
    getStatus(density) {
        const [optimalMin, optimalMax] = this.options.optimalRange;
        const [warningMin, warningMax] = this.options.warningRange;
        
        if (density >= optimalMin && density <= optimalMax) {
            return { code: 'ideal', label: 'אידיאלי', color: '#10b981', icon: '✅' };
        } else if (density >= warningMin && density <= warningMax) {
            if (density < optimalMin) {
                return { code: 'low', label: 'נמוך', color: '#f59e0b', icon: '⚠️' };
            } else {
                return { code: 'high', label: 'גבוה', color: '#f59e0b', icon: '⚠️' };
            }
        } else if (density < warningMin) {
            return { code: 'too_thin', label: 'דליל מדי', color: '#ef4444', icon: '🔴' };
        } else {
            return { code: 'stuffing', label: 'ספאם מילות מפתח', color: '#ef4444', icon: '🔴' };
        }
    }
    
    /**
     * Generate suggestions for fixing density issues
     */
    generateSuggestions(analysisResult) {
        const suggestions = [];
        const { zones, weightedDensity } = analysisResult;
        const status = this.getStatus(weightedDensity);
        const [optimalMin, optimalMax] = this.options.optimalRange;
        
        // Title checks
        if (!zones.title.found && zones.title.text) {
            suggestions.push({
                type: 'missing_title',
                severity: 'high',
                message: `מילת המפתח "${this.keyword}" חסרה בכותרת העמוד`,
                location: 'title',
                currentText: zones.title.text,
                action: 'add_keyword'
            });
        }
        
        // Meta description checks
        if (!zones.metaDescription.found && zones.metaDescription.text) {
            suggestions.push({
                type: 'missing_meta',
                severity: 'medium',
                message: `מילת המפתח חסרה בתיאור המטא`,
                location: 'meta_description',
                currentText: zones.metaDescription.text,
                action: 'add_keyword'
            });
        }
        
        // H1 checks
        if (zones.h1.totalItems === 0) {
            suggestions.push({
                type: 'missing_h1',
                severity: 'high',
                message: 'חסרה כותרת H1 בעמוד',
                location: 'h1',
                action: 'create_h1'
            });
        } else if (zones.h1.foundCount === 0) {
            suggestions.push({
                type: 'keyword_missing_h1',
                severity: 'high',
                message: `מילת המפתח חסרה ב-H1`,
                location: 'h1',
                currentText: zones.h1.items[0]?.text,
                action: 'add_keyword'
            });
        }
        
        // H2 checks
        if (zones.h2.totalItems > 0 && zones.h2.foundCount === 0) {
            suggestions.push({
                type: 'keyword_missing_h2',
                severity: 'medium',
                message: `מילת המפתח לא מופיעה באף כותרת H2`,
                location: 'h2',
                action: 'add_keyword'
            });
        } else if (zones.h2.totalItems > 2 && zones.h2.foundCount < Math.ceil(zones.h2.totalItems / 3)) {
            suggestions.push({
                type: 'low_h2_coverage',
                severity: 'low',
                message: `מילת המפתח מופיעה רק ב-${zones.h2.foundCount} מתוך ${zones.h2.totalItems} כותרות H2`,
                location: 'h2',
                action: 'add_keyword'
            });
        }
        
        // Density-based suggestions
        if (status.code === 'too_thin') {
            const targetCount = Math.ceil(zones.body.wordCount * optimalMin / 100);
            const addCount = targetCount - zones.body.count;
            suggestions.push({
                type: 'add_occurrences',
                severity: 'high',
                message: `הוסף ${addCount} מופעים של מילת המפתח להגעה לצפיפות אופטימלית`,
                location: 'body',
                currentCount: zones.body.count,
                targetCount: targetCount,
                action: 'increase_density'
            });
        } else if (status.code === 'stuffing') {
            const targetCount = Math.floor(zones.body.wordCount * optimalMax / 100);
            const removeCount = zones.body.count - targetCount;
            suggestions.push({
                type: 'remove_occurrences',
                severity: 'high',
                message: `הפחת ${removeCount} מופעים של מילת המפתח למניעת ספאם`,
                location: 'body',
                currentCount: zones.body.count,
                targetCount: targetCount,
                action: 'decrease_density'
            });
        }
        
        // Check for keyword clustering (too many in first/last paragraphs)
        // This is a simplified check - in production would parse paragraphs
        if (zones.body.positions && zones.body.positions.length > 5) {
            const first30Percent = Math.floor(zones.body.wordCount * 0.3);
            const earlyPositions = zones.body.positions.filter(p => p.start < first30Percent);
            if (earlyPositions.length > zones.body.positions.length * 0.6) {
                suggestions.push({
                    type: 'clustering',
                    severity: 'medium',
                    message: 'מילת המפתח מרוכזת יותר מדי בתחילת התוכן - פזר לאורך הטקסט',
                    location: 'body',
                    action: 'redistribute'
                });
            }
        }
        
        return suggestions;
    }
    
    /**
     * Main analysis function
     */
    analyze() {
        if (this._analysisResult) return this._analysisResult;
        
        const densityResult = this.calculateWeightedDensity();
        const score = this.calculateScore(densityResult.weightedDensity);
        const status = this.getStatus(densityResult.weightedDensity);
        const suggestions = this.generateSuggestions(densityResult);
        
        this._analysisResult = {
            keyword: this.keyword,
            variations: this.getKeywordVariations(this.keyword),
            totalWords: densityResult.totalWords,
            totalOccurrences: densityResult.totalOccurrences,
            simpleDensity: densityResult.simpleDensity,
            weightedDensity: densityResult.weightedDensity,
            score: Math.round(score),
            status,
            breakdown: densityResult.zones,
            suggestions,
            optimalRange: this.options.optimalRange,
            timestamp: new Date().toISOString()
        };
        
        return this._analysisResult;
    }
    
    /**
     * Generate highlighted HTML preview with keyword occurrences marked
     */
    generateHighlightedPreview(maxLength = 2000) {
        const parsed = this.parseHTML();
        const variations = this.getKeywordVariations(this.keyword);
        let previewText = parsed.bodyText.substring(0, maxLength);
        
        // Sort variations by length (longest first) to avoid partial replacements
        const sortedVariations = variations.sort((a, b) => b.length - a.length);
        
        sortedVariations.forEach(variation => {
            try {
                const regex = new RegExp(`(${variation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
                previewText = previewText.replace(regex, '<mark class="keyword-highlight">$1</mark>');
            } catch (e) {
                console.warn('Highlight error:', e);
            }
        });
        
        return previewText + (parsed.bodyText.length > maxLength ? '...' : '');
    }
    
    /**
     * Generate report JSON for API/export
     */
    generateReport() {
        return this.analyze();
    }
}


/**
 * Fix Prompt Templates for Claude Code integration
 */
const KeywordDensityFixPrompts = {
    stuffing: `הפחת את צפיפות מילת המפתח "{keyword}" מ-{currentDensity}% ל-{targetDensity}%.
הסר {removeCount} מופעים מגוף התוכן.
עדיפות להסרה: פסקאות פתיחה וסיום.
שמור על קריאות טבעית.
אל תשנה כותרות.`,

    missingTitle: `הוסף את מילת המפתח "{keyword}" לכותרת העמוד.
כותרת נוכחית: "{currentTitle}"
שמור על אורך דומה ומשמעות.
הכותרת צריכה להיות אטרקטיבית לקליקים.`,

    missingMeta: `הוסף את מילת המפתח "{keyword}" לתיאור המטא.
תיאור נוכחי: "{currentMeta}"
שמור על אורך של עד 155 תווים.
התיאור צריך להיות אטרקטיבי לקליקים.`,

    missingH1: `שכתב את כותרת ה-H1 כך שתכלול את מילת המפתח "{keyword}".
כותרת נוכחית: "{currentH1}"
שמור על אורך דומה ומשמעות.`,

    missingH2: `הוסף את מילת המפתח "{keyword}" לכותרת H2 הבאה:
"{currentH2}"
או צור כותרת H2 חדשה שמכילה את המילה.`,

    tooThin: `הוסף {addCount} מופעים של מילת המפתח "{keyword}" לתוכן.
מיקומים מומלצים:
- פסקת הפתיחה
- לפחות כותרת H2 אחת
- פסקת הסיום
השתמש בווריאציות טבעיות של המילה.
שמור על קריאות טבעית.`,

    clustering: `פזר את מופעי מילת המפתח "{keyword}" בתוכן.
כרגע יש ריכוז גבוה מדי בחלק אחד של הטקסט.
הזז חלק מהמופעים לפסקאות אחרות לאורך העמוד.`,

    createH1: `צור כותרת H1 חדשה לעמוד שמכילה את מילת המפתח "{keyword}".
הכותרת צריכה להיות ברורה ומתארת את תוכן העמוד.`
};

/**
 * Generate fix prompt from template
 */
function generateDensityFixPrompt(type, data) {
    const template = KeywordDensityFixPrompts[type];
    if (!template) {
        console.error('Unknown fix type:', type);
        return '';
    }
    
    let prompt = template;
    
    // Replace all placeholders
    Object.keys(data).forEach(key => {
        const placeholder = new RegExp(`\\{${key}\\}`, 'g');
        prompt = prompt.replace(placeholder, data[key]);
    });
    
    return prompt;
}

/**
 * Render Keyword Density UI Component
 */
function renderKeywordDensityUI(analysisResult, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Container not found:', containerId);
        return;
    }
    
    const { keyword, totalWords, totalOccurrences, weightedDensity, score, status, breakdown, suggestions, optimalRange } = analysisResult;
    
    // Generate summary cards HTML
    const summaryCardsHTML = `
        <div class="kd-summary-cards">
            <div class="kd-card kd-score-card" style="border-color: ${status.color}">
                <div class="kd-card-icon">${status.icon}</div>
                <div class="kd-card-value" style="color: ${status.color}">${score}</div>
                <div class="kd-card-label">ציון כללי</div>
            </div>
            <div class="kd-card">
                <div class="kd-card-icon">📊</div>
                <div class="kd-card-value">${weightedDensity}%</div>
                <div class="kd-card-label">צפיפות משוקללת</div>
                <div class="kd-card-hint">טווח מומלץ: ${optimalRange[0]}-${optimalRange[1]}%</div>
            </div>
            <div class="kd-card">
                <div class="kd-card-icon">🔢</div>
                <div class="kd-card-value">${totalOccurrences}/${totalWords}</div>
                <div class="kd-card-label">מופעים/מילים</div>
            </div>
            <div class="kd-card kd-status-card" style="background: ${status.color}20; border-color: ${status.color}">
                <div class="kd-card-value" style="color: ${status.color}">${status.label}</div>
                <div class="kd-card-label">סטטוס</div>
            </div>
        </div>
    `;
    
    // Generate zone breakdown HTML
    const zonesHTML = `
        <div class="kd-zones">
            <h4>📍 פילוח לפי אזורים</h4>
            
            <!-- Title & Meta -->
            <div class="kd-zone-row">
                <span class="kd-zone-label">🏷️ כותרת עמוד</span>
                <span class="kd-zone-status ${breakdown.title.found ? 'found' : 'missing'}">
                    ${breakdown.title.found ? '✅ נמצא' : '❌ חסר'}
                </span>
                ${!breakdown.title.found && breakdown.title.text ? 
                    `<button class="kd-fix-btn" onclick="fixKeywordIssue('missingTitle', ${JSON.stringify({keyword, currentTitle: breakdown.title.text}).replace(/"/g, '&quot;')})">🔧 תקן</button>` : ''
                }
            </div>
            
            <div class="kd-zone-row">
                <span class="kd-zone-label">📝 תיאור מטא</span>
                <span class="kd-zone-status ${breakdown.metaDescription.found ? 'found' : 'missing'}">
                    ${breakdown.metaDescription.found ? '✅ נמצא' : '❌ חסר'}
                </span>
                ${!breakdown.metaDescription.found && breakdown.metaDescription.text ? 
                    `<button class="kd-fix-btn" onclick="fixKeywordIssue('missingMeta', ${JSON.stringify({keyword, currentMeta: breakdown.metaDescription.text}).replace(/"/g, '&quot;')})">🔧 תקן</button>` : ''
                }
            </div>
            
            <!-- H1 -->
            <div class="kd-zone-row">
                <span class="kd-zone-label">📌 H1</span>
                <span class="kd-zone-count">${breakdown.h1.foundCount}/${breakdown.h1.totalItems}</span>
                <span class="kd-zone-status ${breakdown.h1.foundCount > 0 ? 'found' : 'missing'}">
                    ${breakdown.h1.foundCount > 0 ? '✅' : '❌'}
                </span>
            </div>
            
            <!-- H2 -->
            <div class="kd-zone-row">
                <span class="kd-zone-label">📌 H2</span>
                <span class="kd-zone-count">${breakdown.h2.foundCount}/${breakdown.h2.totalItems}</span>
                <span class="kd-zone-status ${breakdown.h2.foundCount > 0 ? 'found' : breakdown.h2.totalItems > 0 ? 'missing' : 'neutral'}">
                    ${breakdown.h2.foundCount > 0 ? '✅' : breakdown.h2.totalItems > 0 ? '⚠️' : '-'}
                </span>
            </div>
            
            <!-- Body -->
            <div class="kd-zone-row">
                <span class="kd-zone-label">📄 גוף התוכן</span>
                <span class="kd-zone-count">${breakdown.body.count} מופעים</span>
                <div class="kd-density-bar">
                    <div class="kd-density-fill" style="width: ${Math.min(weightedDensity / 5 * 100, 100)}%; background: ${status.color}"></div>
                    <span class="kd-density-optimal" style="left: ${optimalRange[0] / 5 * 100}%; width: ${(optimalRange[1] - optimalRange[0]) / 5 * 100}%"></span>
                </div>
            </div>
        </div>
    `;
    
    // Generate suggestions HTML
    let suggestionsHTML = '';
    if (suggestions.length > 0) {
        const suggestionItems = suggestions.map(s => `
            <div class="kd-suggestion kd-suggestion-${s.severity}">
                <div class="kd-suggestion-icon">${s.severity === 'high' ? '🔴' : s.severity === 'medium' ? '🟡' : '🟢'}</div>
                <div class="kd-suggestion-text">${s.message}</div>
                <button class="kd-fix-btn" onclick="fixKeywordIssue('${s.type}', ${JSON.stringify({keyword, ...s}).replace(/"/g, '&quot;')})">
                    🔧 תקן עם Claude
                </button>
            </div>
        `).join('');
        
        suggestionsHTML = `
            <div class="kd-suggestions">
                <h4>💡 הצעות לשיפור</h4>
                ${suggestionItems}
            </div>
        `;
    }
    
    // Combine all HTML
    container.innerHTML = `
        <div class="kd-module">
            <div class="kd-header">
                <h3>🔍 ניתוח צפיפות מילת מפתח</h3>
                <span class="kd-keyword">"${keyword}"</span>
            </div>
            ${summaryCardsHTML}
            ${zonesHTML}
            ${suggestionsHTML}
        </div>
    `;
}

/**
 * Fix keyword issue by sending to Claude
 */
function fixKeywordIssue(issueType, data) {
    const prompt = generateDensityFixPrompt(issueType, data);
    
    if (!prompt) {
        console.error('Could not generate fix prompt');
        return;
    }
    
    // Check if showPromptPreview exists (from dashboard.html)
    if (typeof showPromptPreview === 'function') {
        showPromptPreview(prompt, `תיקון: ${data.message || issueType}`);
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(prompt).then(() => {
            alert('הפרומפט הועתק ללוח. הדבק אותו ב-Claude Code.');
        });
    }
}

/**
 * ============================================
 * SpamAnalyzer - Header & Emphasis Spam Detection
 * ============================================
 * 
 * Detects over-optimization in:
 * - Headers (H1-H6): Repetitive patterns, keyword stuffing
 * - Emphasis tags (<strong>, <b>, <em>): Bold spam, isolated tagging
 */

class SpamAnalyzer {
    constructor(htmlContent, keyword) {
        this.htmlContent = htmlContent;
        this.keyword = keyword;
        
        // Thresholds for spam detection
        this.thresholds = {
            // Header thresholds
            exactMatchRatio: 0.6,      // 60% of headers with exact match = spam
            startsWithRatio: 0.5,      // 50% of headers starting with keyword = spam
            minHeadersForAnalysis: 3,  // Min headers needed for pattern detection
            
            // Emphasis thresholds
            boldRatio: {
                safe: 0.2,             // 0-20% = natural
                warning: 0.4,          // 21-40% = borderline
                spam: 1.0              // 41%+ = spam
            },
            contextRatio: {
                isolated: 1.2,         // Ratio <= 1.2 = isolated (bad)
                contextual: 2.0        // Ratio > 2.0 = contextual (good)
            },
            clusterWindow: 50,         // Words in sliding window
            maxClusterOccurrences: 2   // Max keyword bolds in window
        };
        
        // Hebrew prefixes for variation matching
        this.hebrewPrefixes = ['ה', 'ב', 'ל', 'מ', 'ו', 'כ', 'ש', 'וה', 'וב', 'ול', 'שה', 'שב', 'של'];
        
        this._doc = null;
    }
    
    /**
     * Parse HTML content
     */
    parseHTML() {
        if (this._doc) return this._doc;
        
        const parser = new DOMParser();
        this._doc = parser.parseFromString(this.htmlContent, 'text/html');
        return this._doc;
    }
    
    /**
     * Normalize Hebrew text
     */
    normalizeHebrew(text) {
        if (!text) return '';
        return text
            .replace(/[\u0591-\u05C7]/g, '')
            .replace(/[^\u0590-\u05FF\sa-zA-Z0-9]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }
    
    /**
     * Get keyword variations for matching
     */
    getKeywordVariations() {
        const normalized = this.normalizeHebrew(this.keyword);
        const words = normalized.split(/\s+/);
        const variations = new Set([normalized]);
        
        if (words.length === 1) {
            const word = words[0];
            this.hebrewPrefixes.forEach(prefix => {
                variations.add(prefix + word);
            });
            if (word.endsWith('ה')) {
                variations.add(word.slice(0, -1) + 'ות');
                variations.add(word.slice(0, -1) + 'ת');
            }
            variations.add(word + 'ים');
            variations.add(word + 'ות');
            if (!word.startsWith('ה')) {
                variations.add('ה' + word);
            }
        }
        
        return Array.from(variations);
    }
    
    /**
     * Check if text contains keyword (exact or variation)
     */
    containsKeyword(text) {
        const normalizedText = this.normalizeHebrew(text);
        const variations = this.getKeywordVariations();
        
        return variations.some(variation => {
            try {
                const regex = new RegExp(variation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
                return regex.test(normalizedText);
            } catch (e) {
                return false;
            }
        });
    }
    
    /**
     * Check if text starts with keyword
     */
    startsWithKeyword(text) {
        const normalizedText = this.normalizeHebrew(text);
        const variations = this.getKeywordVariations();
        
        return variations.some(variation => {
            const normalizedVariation = this.normalizeHebrew(variation);
            return normalizedText.startsWith(normalizedVariation) || 
                   normalizedText.startsWith(normalizedVariation + ' ');
        });
    }
    
    /**
     * Analyze headers for spam patterns
     */
    analyzeHeaders() {
        const doc = this.parseHTML();
        const headers = [];
        const issues = [];
        
        // Collect all headers
        ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach((tag, index) => {
            doc.querySelectorAll(tag).forEach((el, i) => {
                headers.push({
                    tag: tag.toUpperCase(),
                    level: index + 1,
                    text: el.textContent.trim(),
                    id: `${tag}-${i}`,
                    hasKeyword: this.containsKeyword(el.textContent),
                    startsWithKeyword: this.startsWithKeyword(el.textContent)
                });
            });
        });
        
        // Get subheaders (H2-H6) for pattern analysis
        const subheaders = headers.filter(h => h.level > 1);
        const h1s = headers.filter(h => h.level === 1);
        
        // Metrics
        const totalHeaders = headers.length;
        const headersWithKeyword = headers.filter(h => h.hasKeyword).length;
        const headersStartingWithKeyword = headers.filter(h => h.startsWithKeyword).length;
        
        const exactMatchRatio = subheaders.length > 0 
            ? subheaders.filter(h => h.hasKeyword).length / subheaders.length 
            : 0;
        const startsWithRatio = subheaders.length > 0 
            ? subheaders.filter(h => h.startsWithKeyword).length / subheaders.length 
            : 0;
        
        // H1 Isolation Rule - check if H1 is only the keyword
        let h1IsolationIssue = false;
        if (h1s.length > 0) {
            const h1Text = this.normalizeHebrew(h1s[0].text);
            const keywordNormalized = this.normalizeHebrew(this.keyword);
            // Check if H1 is basically just the keyword (with possible prefix)
            const h1Words = h1Text.split(/\s+/).length;
            const keywordWords = keywordNormalized.split(/\s+/).length;
            
            if (this.containsKeyword(h1Text) && h1Words <= keywordWords + 1) {
                h1IsolationIssue = true;
                issues.push({
                    type: 'H1_ISOLATION',
                    severity: 'medium',
                    message: `כותרת H1 מכילה רק את מילת המפתח ללא הקשר נוסף`,
                    affectedTags: [h1s[0].id],
                    currentText: h1s[0].text,
                    suggestion: 'הרחב את כותרת ה-H1 עם מילים נוספות'
                });
            }
        }
        
        // Check for exact match saturation (only if enough headers)
        if (subheaders.length >= this.thresholds.minHeadersForAnalysis) {
            if (exactMatchRatio > this.thresholds.exactMatchRatio) {
                const affectedHeaders = subheaders.filter(h => h.hasKeyword);
                issues.push({
                    type: 'REPETITIVE_PATTERN',
                    severity: 'high',
                    message: `${Math.round(exactMatchRatio * 100)}% מכותרות המשנה מכילות את מילת המפתח - זה נראה כספאם`,
                    affectedTags: affectedHeaders.map(h => h.id),
                    suggestion: 'גוון את הכותרות עם ביטויים שונים'
                });
            }
            
            // Check for leading keyword pattern
            if (startsWithRatio > this.thresholds.startsWithRatio) {
                const affectedHeaders = subheaders.filter(h => h.startsWithKeyword);
                issues.push({
                    type: 'LEADING_KEYWORD',
                    severity: 'medium',
                    message: `${Math.round(startsWithRatio * 100)}% מהכותרות מתחילות במילת המפתח`,
                    affectedTags: affectedHeaders.map(h => h.id),
                    suggestion: 'מקם את מילת המפתח במיקומים שונים בכותרות'
                });
            }
        }
        
        // Calculate header spam score (0 = pure spam, 100 = perfect)
        const headerSpamScore = Math.max(0, Math.min(100, 
            100 - (exactMatchRatio * 30) - (startsWithRatio * 20) - (h1IsolationIssue ? 10 : 0)
        ));
        
        // Determine status
        let status = 'good';
        if (headerSpamScore < 50) status = 'critical';
        else if (headerSpamScore < 70) status = 'warning';
        
        return {
            status,
            score: Math.round(headerSpamScore),
            metrics: {
                totalHeaders,
                subheaderCount: subheaders.length,
                headersWithKeyword,
                exactMatchRatio: Math.round(exactMatchRatio * 100) / 100,
                startsWithKeywordRatio: Math.round(startsWithRatio * 100) / 100,
                h1IsolationIssue
            },
            headers,
            issues
        };
    }
    
    /**
     * Analyze emphasis tags for spam patterns
     */
    analyzeEmphasis() {
        const doc = this.parseHTML();
        const issues = [];
        const variations = this.getKeywordVariations();
        
        // Find all emphasis elements
        const emphasisTags = [...doc.querySelectorAll('strong, b, em')];
        
        // Count total keyword occurrences in body text
        const bodyText = doc.body ? doc.body.textContent : '';
        let totalKeywordCount = 0;
        variations.forEach(variation => {
            try {
                const regex = new RegExp(variation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
                const matches = bodyText.match(regex);
                totalKeywordCount += matches ? matches.length : 0;
            } catch (e) {}
        });
        
        // Analyze each emphasis tag
        const emphasisAnalysis = [];
        let boldedKeywordCount = 0;
        let isolatedBoldCount = 0;
        
        emphasisTags.forEach((el, index) => {
            const innerText = el.textContent.trim();
            const containsKw = this.containsKeyword(innerText);
            
            if (containsKw) {
                boldedKeywordCount++;
                
                // Calculate context ratio
                const keywordLen = this.normalizeHebrew(this.keyword).length;
                const tagLen = this.normalizeHebrew(innerText).length;
                const contextRatio = tagLen / keywordLen;
                
                const isIsolated = contextRatio <= this.thresholds.contextRatio.isolated;
                if (isIsolated) {
                    isolatedBoldCount++;
                }
                
                emphasisAnalysis.push({
                    index,
                    tag: el.tagName.toLowerCase(),
                    text: innerText,
                    contextRatio: Math.round(contextRatio * 100) / 100,
                    isIsolated,
                    quality: isIsolated ? 'poor' : (contextRatio > this.thresholds.contextRatio.contextual ? 'good' : 'acceptable')
                });
            }
        });
        
        // Calculate bold ratio
        const boldRatio = totalKeywordCount > 0 
            ? boldedKeywordCount / totalKeywordCount 
            : 0;
        
        // Calculate context quality score
        const contextScore = boldedKeywordCount > 0
            ? Math.round((1 - (isolatedBoldCount / boldedKeywordCount)) * 100)
            : 100;
        
        // Detect clusters (multiple bolded keywords in small text area)
        const clusters = this.detectBoldClusters(doc, variations);
        
        // Determine status and issues
        let status = 'good';
        
        if (boldRatio > this.thresholds.boldRatio.warning) {
            status = boldRatio > this.thresholds.boldRatio.spam * 0.6 ? 'critical' : 'warning';
            issues.push({
                type: 'HIGH_BOLD_RATIO',
                severity: 'high',
                message: `${Math.round(boldRatio * 100)}% ממופעי מילת המפתח מודגשים - גבוה מדי`,
                boldedCount: boldedKeywordCount,
                totalCount: totalKeywordCount,
                suggestion: 'הסר הדגשות מחלק ממופעי מילת המפתח'
            });
        }
        
        if (isolatedBoldCount > 0 && isolatedBoldCount >= boldedKeywordCount * 0.5) {
            issues.push({
                type: 'ISOLATED_BOLD',
                severity: 'medium',
                message: `${isolatedBoldCount} מתוך ${boldedKeywordCount} הדגשות הן מבודדות (רק מילת המפתח ללא הקשר)`,
                isolatedCount: isolatedBoldCount,
                suggestion: 'הרחב את ההדגשות לכלול משפטים שלמים או ביטויים ארוכים יותר'
            });
        }
        
        clusters.forEach(cluster => {
            issues.push({
                type: 'BOLD_CLUSTER',
                severity: 'medium',
                message: `ריכוז גבוה של הדגשות בפסקה ${cluster.paragraphIndex + 1}: ${cluster.count} מופעים`,
                paragraphIndex: cluster.paragraphIndex,
                suggestion: 'פזר את ההדגשות לאורך התוכן'
            });
        });
        
        // Calculate emphasis spam score
        const emphasisSpamScore = Math.max(0, Math.min(100,
            100 - (boldRatio * 50) - ((1 - contextScore / 100) * 30) - (clusters.length * 10)
        ));
        
        return {
            status,
            score: Math.round(emphasisSpamScore),
            metrics: {
                totalKeywords: totalKeywordCount,
                boldedKeywords: boldedKeywordCount,
                boldRatio: Math.round(boldRatio * 100) / 100,
                isolatedBoldCount
            },
            contextQuality: {
                score: contextScore,
                explanation: contextScore < 50 
                    ? 'רוב ההדגשות הן תגיות מבודדות ללא הקשר סביב'
                    : contextScore < 80 
                        ? 'חלק מההדגשות מבודדות - כדאי להרחיב'
                        : 'ההדגשות כוללות הקשר טוב'
            },
            emphasisDetails: emphasisAnalysis,
            clustersDetected: clusters,
            issues
        };
    }
    
    /**
     * Detect clusters of bolded keywords
     */
    detectBoldClusters(doc, variations) {
        const clusters = [];
        const paragraphs = doc.querySelectorAll('p, div.content, article, section');
        
        paragraphs.forEach((para, pIndex) => {
            const text = para.textContent;
            const words = text.split(/\s+/);
            
            // Sliding window approach
            if (words.length >= this.thresholds.clusterWindow) {
                // Check for bolded keywords in this paragraph
                const boldElements = para.querySelectorAll('strong, b, em');
                let boldedKeywordsInPara = 0;
                
                boldElements.forEach(el => {
                    if (this.containsKeyword(el.textContent)) {
                        boldedKeywordsInPara++;
                    }
                });
                
                if (boldedKeywordsInPara > this.thresholds.maxClusterOccurrences) {
                    clusters.push({
                        paragraphIndex: pIndex,
                        count: boldedKeywordsInPara,
                        message: `ריכוז גבוה בפסקה ${pIndex + 1} (${boldedKeywordsInPara} מופעים)`
                    });
                }
            }
        });
        
        return clusters;
    }
    
    /**
     * Main spam analysis function
     */
    analyze() {
        const headersAnalysis = this.analyzeHeaders();
        const emphasisAnalysis = this.analyzeEmphasis();
        
        // Calculate overall risk score (0 = safe, 100 = pure spam)
        const riskScore = Math.max(0, Math.min(100,
            ((100 - headersAnalysis.score) * 0.4) + ((100 - emphasisAnalysis.score) * 0.6)
        ));
        
        // Determine overall risk level
        let overallRisk = 'Low';
        if (riskScore > 60) overallRisk = 'High';
        else if (riskScore > 30) overallRisk = 'Medium';
        
        return {
            overall_spam_risk: overallRisk,
            risk_score: Math.round(riskScore),
            headers_analysis: headersAnalysis,
            emphasis_analysis: emphasisAnalysis,
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * Generate actionable fix suggestions
     */
    generateFixSuggestions() {
        const analysis = this.analyze();
        const suggestions = [];
        
        // Header fixes
        analysis.headers_analysis.issues.forEach(issue => {
            if (issue.type === 'REPETITIVE_PATTERN' || issue.type === 'LEADING_KEYWORD') {
                suggestions.push({
                    type: 'humanize_headers',
                    severity: issue.severity,
                    title: '🎨 Humanize Headers',
                    description: issue.message,
                    action: 'שכתב כותרות כמו "ביטוח רכב זול" ל-"איך מוצאים פוליסה במחיר טוב?"',
                    affectedTags: issue.affectedTags
                });
            }
        });
        
        // Emphasis fixes
        if (analysis.emphasis_analysis.metrics.isolatedBoldCount > 0) {
            suggestions.push({
                type: 'expand_bolds',
                severity: 'medium',
                title: '📝 Expand Bolds',
                description: `${analysis.emphasis_analysis.metrics.isolatedBoldCount} הדגשות מבודדות`,
                action: 'הרחב את ההדגשות לכלול את כל המשפט במקום רק מילת המפתח'
            });
        }
        
        if (analysis.emphasis_analysis.metrics.boldRatio > this.thresholds.boldRatio.warning) {
            const currentRatio = analysis.emphasis_analysis.metrics.boldRatio;
            const targetRatio = this.thresholds.boldRatio.safe;
            const toRemove = Math.ceil(analysis.emphasis_analysis.metrics.boldedKeywords * (1 - targetRatio / currentRatio));
            
            suggestions.push({
                type: 'unbold_randomly',
                severity: 'high',
                title: '🔓 Unbold Randomly',
                description: `יחס הדגשות גבוה: ${Math.round(currentRatio * 100)}%`,
                action: `הסר הדגשה מ-${toRemove} מופעים להגעה ליחס תקין של ${Math.round(targetRatio * 100)}%`,
                removeCount: toRemove
            });
        }
        
        return suggestions;
    }
}


/**
 * Fix Prompt Templates for Spam Issues
 */
const SpamFixPrompts = {
    humanize_headers: `שכתב את הכותרות הבאות כך שלא יכילו את מילת המפתח "{keyword}" באופן חוזר:

כותרות לשכתוב:
{headersList}

הנחיות:
- גוון את הניסוח בכל כותרת
- השתמש במילים נרדפות ובשאלות
- שמור על המשמעות המקורית
- אל תמקם את מילת המפתח בתחילת כל כותרת`,

    expand_bolds: `הרחב את ההדגשות הבאות לכלול את כל המשפט או ביטוי ארוך יותר:

הדגשות מבודדות שנמצאו:
{boldsList}

הנחיות:
- במקום להדגיש רק "{keyword}", הדגש את כל המשפט שמכיל אותה
- דוגמה: במקום <strong>ביטוח רכב</strong> -> <strong>השוואת מחירי ביטוח רכב יכולה לחסוך לך אלפי שקלים</strong>`,

    unbold_randomly: `הסר הדגשות ({removeCount} מופעים) ממילת המפתח "{keyword}" בתוכן.

הנחיות:
- הסר הדגשות באופן אקראי לאורך הטקסט
- שמור על הדגשות בכותרות ובמשפטים חשובים
- עדיפות להסרה: הדגשות מבודדות (רק המילה עצמה)
- היעד: הגעה ליחס של כ-20% הדגשות ממופעי מילת המפתח`,

    h1_isolation: `הרחב את כותרת ה-H1 כך שתכלול יותר ממילת המפתח בלבד:

כותרת נוכחית: "{currentH1}"

הנחיות:
- הוסף מילות הקשר ותיאור
- דוגמה: "ביטוח רכב" -> "מדריך מקיף לביטוח רכב: השוואת מחירים וטיפים"
- שמור על הכותרת קצרה ואטרקטיבית`
};


/**
 * Render Spam Analysis UI Component
 */
function renderSpamAnalysisUI(spamResult, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Container not found:', containerId);
        return;
    }
    
    const { overall_spam_risk, risk_score, headers_analysis, emphasis_analysis } = spamResult;
    
    // Risk color mapping
    const riskColors = {
        'Low': '#10b981',
        'Medium': '#f59e0b',
        'High': '#ef4444'
    };
    
    const riskColor = riskColors[overall_spam_risk] || '#6b7280';
    
    // Generate HTML
    let html = `
        <div class="spam-module">
            <div class="spam-header">
                <h3>🛡️ ניתוח ספאם בכותרות והדגשות</h3>
                <div class="spam-risk-badge" style="background: ${riskColor}20; color: ${riskColor}; border: 1px solid ${riskColor};">
                    ${overall_spam_risk === 'Low' ? '✅' : overall_spam_risk === 'Medium' ? '⚠️' : '🔴'} 
                    סיכון: ${overall_spam_risk === 'Low' ? 'נמוך' : overall_spam_risk === 'Medium' ? 'בינוני' : 'גבוה'}
                </div>
            </div>
            
            <div class="spam-summary-cards">
                <div class="spam-card" style="border-color: ${riskColor}">
                    <div class="spam-card-value" style="color: ${riskColor}">${risk_score}</div>
                    <div class="spam-card-label">ציון סיכון</div>
                    <div class="spam-card-hint">0 = בטוח, 100 = ספאם</div>
                </div>
                <div class="spam-card" style="border-color: ${headers_analysis.status === 'good' ? '#10b981' : headers_analysis.status === 'warning' ? '#f59e0b' : '#ef4444'}">
                    <div class="spam-card-value">${headers_analysis.score}</div>
                    <div class="spam-card-label">ציון כותרות</div>
                </div>
                <div class="spam-card" style="border-color: ${emphasis_analysis.status === 'good' ? '#10b981' : emphasis_analysis.status === 'warning' ? '#f59e0b' : '#ef4444'}">
                    <div class="spam-card-value">${emphasis_analysis.score}</div>
                    <div class="spam-card-label">ציון הדגשות</div>
                </div>
            </div>
    `;
    
    // Headers Analysis Section
    html += `
            <div class="spam-section">
                <h4>📑 ניתוח כותרות</h4>
                <div class="spam-metrics">
                    <div class="spam-metric">
                        <span class="spam-metric-label">סה"כ כותרות:</span>
                        <span class="spam-metric-value">${headers_analysis.metrics.totalHeaders}</span>
                    </div>
                    <div class="spam-metric">
                        <span class="spam-metric-label">יחס התאמה מדויקת:</span>
                        <span class="spam-metric-value ${headers_analysis.metrics.exactMatchRatio > 0.6 ? 'bad' : 'good'}">
                            ${Math.round(headers_analysis.metrics.exactMatchRatio * 100)}%
                        </span>
                    </div>
                    <div class="spam-metric">
                        <span class="spam-metric-label">מתחילות במילת מפתח:</span>
                        <span class="spam-metric-value ${headers_analysis.metrics.startsWithKeywordRatio > 0.5 ? 'bad' : 'good'}">
                            ${Math.round(headers_analysis.metrics.startsWithKeywordRatio * 100)}%
                        </span>
                    </div>
                </div>
    `;
    
    // Header issues
    if (headers_analysis.issues.length > 0) {
        html += `<div class="spam-issues">`;
        headers_analysis.issues.forEach(issue => {
            html += `
                <div class="spam-issue spam-issue-${issue.severity}">
                    <div class="spam-issue-icon">${issue.severity === 'high' ? '🔴' : '🟡'}</div>
                    <div class="spam-issue-content">
                        <div class="spam-issue-message">${issue.message}</div>
                        <div class="spam-issue-suggestion">${issue.suggestion}</div>
                    </div>
                    <button class="spam-fix-btn" onclick="fixSpamIssue('${issue.type}', ${JSON.stringify({keyword: spamResult.keyword || '', ...issue}).replace(/"/g, '&quot;')})">
                        🔧 תקן
                    </button>
                </div>
            `;
        });
        html += `</div>`;
    }
    html += `</div>`;
    
    // Emphasis Analysis Section
    html += `
            <div class="spam-section">
                <h4>💪 ניתוח הדגשות</h4>
                <div class="spam-metrics">
                    <div class="spam-metric">
                        <span class="spam-metric-label">מופעים כללי:</span>
                        <span class="spam-metric-value">${emphasis_analysis.metrics.totalKeywords}</span>
                    </div>
                    <div class="spam-metric">
                        <span class="spam-metric-label">מודגשים:</span>
                        <span class="spam-metric-value">${emphasis_analysis.metrics.boldedKeywords}</span>
                    </div>
                    <div class="spam-metric">
                        <span class="spam-metric-label">יחס הדגשה:</span>
                        <span class="spam-metric-value ${emphasis_analysis.metrics.boldRatio > 0.4 ? 'bad' : emphasis_analysis.metrics.boldRatio > 0.2 ? 'warning' : 'good'}">
                            ${Math.round(emphasis_analysis.metrics.boldRatio * 100)}%
                        </span>
                    </div>
                    <div class="spam-metric">
                        <span class="spam-metric-label">הדגשות מבודדות:</span>
                        <span class="spam-metric-value ${emphasis_analysis.metrics.isolatedBoldCount > 0 ? 'warning' : 'good'}">
                            ${emphasis_analysis.metrics.isolatedBoldCount}
                        </span>
                    </div>
                </div>
                
                <div class="spam-context-quality">
                    <div class="spam-context-bar">
                        <div class="spam-context-fill" style="width: ${emphasis_analysis.contextQuality.score}%; background: ${emphasis_analysis.contextQuality.score > 70 ? '#10b981' : emphasis_analysis.contextQuality.score > 40 ? '#f59e0b' : '#ef4444'}"></div>
                    </div>
                    <div class="spam-context-label">איכות הקשר: ${emphasis_analysis.contextQuality.score}% - ${emphasis_analysis.contextQuality.explanation}</div>
                </div>
    `;
    
    // Emphasis issues
    if (emphasis_analysis.issues.length > 0) {
        html += `<div class="spam-issues">`;
        emphasis_analysis.issues.forEach(issue => {
            html += `
                <div class="spam-issue spam-issue-${issue.severity}">
                    <div class="spam-issue-icon">${issue.severity === 'high' ? '🔴' : '🟡'}</div>
                    <div class="spam-issue-content">
                        <div class="spam-issue-message">${issue.message}</div>
                        <div class="spam-issue-suggestion">${issue.suggestion}</div>
                    </div>
                    <button class="spam-fix-btn" onclick="fixSpamIssue('${issue.type}', ${JSON.stringify({keyword: spamResult.keyword || '', ...issue}).replace(/"/g, '&quot;')})">
                        🔧 תקן
                    </button>
                </div>
            `;
        });
        html += `</div>`;
    }
    html += `</div>`;
    
    html += `</div>`;
    
    container.innerHTML = html;
}


/**
 * Fix spam issue by generating prompt
 */
function fixSpamIssue(issueType, data) {
    // Map issue types to fix prompts
    const promptMap = {
        'REPETITIVE_PATTERN': 'humanize_headers',
        'LEADING_KEYWORD': 'humanize_headers',
        'H1_ISOLATION': 'h1_isolation',
        'HIGH_BOLD_RATIO': 'unbold_randomly',
        'ISOLATED_BOLD': 'expand_bolds',
        'BOLD_CLUSTER': 'expand_bolds'
    };
    
    const promptType = promptMap[issueType];
    const template = SpamFixPrompts[promptType];
    
    if (!template) {
        console.error('Unknown spam fix type:', issueType);
        return;
    }
    
    // Parse data if needed
    let issueData = data;
    if (typeof data === 'string') {
        try {
            issueData = JSON.parse(data.replace(/&quot;/g, '"'));
        } catch (e) {
            issueData = { keyword: data };
        }
    }
    
    // Generate prompt
    let prompt = template;
    Object.keys(issueData).forEach(key => {
        const placeholder = new RegExp(`\\{${key}\\}`, 'g');
        const value = issueData[key] !== undefined ? String(issueData[key]) : '';
        prompt = prompt.replace(placeholder, value);
    });
    
    // Use existing preview function if available
    if (typeof showPromptPreview === 'function') {
        showPromptPreview(prompt, `תיקון ספאם: ${issueData.message || issueType}`);
    } else {
        navigator.clipboard.writeText(prompt).then(() => {
            alert('הפרומפט הועתק ללוח.');
        });
    }
}


// Export for use as module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        KeywordDensityAnalyzer, 
        SpamAnalyzer,
        KeywordDensityFixPrompts, 
        SpamFixPrompts,
        generateDensityFixPrompt, 
        renderKeywordDensityUI,
        renderSpamAnalysisUI,
        fixSpamIssue
    };
}


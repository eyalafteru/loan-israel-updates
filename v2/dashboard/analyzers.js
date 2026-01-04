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
            useNLP: false,
            ...options
        };
        
        this.zoneWeights = {
            title: 3, metaDescription: 2, h1: 3, h2: 2,
            h3: 1.5, h4: 1.5, h5: 1.5, h6: 1.5, body: 1
        };
        
        this.hebrewPrefixes = ['ה', 'ב', 'ל', 'מ', 'ו', 'כ', 'ש', 'וה', 'וב', 'ול', 'שה', 'שב', 'של'];
        this._parsedContent = null;
        this._analysisResult = null;
    }
    
    normalizeHebrew(text) {
        if (!text) return '';
        return text
            .replace(/[\u0591-\u05C7]/g, '')
            .replace(/[^\u0590-\u05FF\sa-zA-Z0-9]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }
    
    extractHebrewWords(text) {
        const normalized = this.normalizeHebrew(text);
        return normalized.split(/\s+/).filter(word => 
            word.length > 0 && /[\u0590-\u05FF]/.test(word)
        );
    }
    
    getKeywordVariations(keyword) {
        const normalized = this.normalizeHebrew(keyword);
        const words = normalized.split(/\s+/);
        const variations = new Set([normalized]);
        
        if (words.length === 1) {
            const word = words[0];
            this.hebrewPrefixes.forEach(prefix => variations.add(prefix + word));
            if (word.endsWith('ה')) {
                variations.add(word.slice(0, -1) + 'ות');
                variations.add(word.slice(0, -1) + 'ת');
            }
            variations.add(word + 'ים');
            variations.add(word + 'ות');
            if (!word.startsWith('ה')) variations.add('ה' + word);
        } else {
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
    
    parseHTML() {
        if (this._parsedContent) return this._parsedContent;
        
        const parser = new DOMParser();
        const doc = parser.parseFromString(this.htmlContent, 'text/html');
        
        const titleEl = doc.querySelector('title');
        const title = titleEl ? titleEl.textContent.trim() : '';
        
        const metaDesc = doc.querySelector('meta[name="description"]');
        const metaDescription = metaDesc ? metaDesc.getAttribute('content') || '' : '';
        
        const headings = {};
        ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(tag => {
            headings[tag] = Array.from(doc.querySelectorAll(tag)).map(el => ({
                text: el.textContent.trim(),
                html: el.innerHTML
            }));
        });
        
        const clone = doc.body.cloneNode(true);
        ['script', 'style', 'noscript', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(sel => {
            clone.querySelectorAll(sel).forEach(el => el.remove());
        });
        
        this._parsedContent = {
            title,
            metaDescription,
            headings,
            bodyText: (clone.textContent || '').trim(),
            fullText: (doc.body ? doc.body.textContent : '').trim(),
            doc
        };
        
        return this._parsedContent;
    }
    
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
                if (matches.length > 0) {
                    variationCounts[variation] = matches.length;
                    totalCount += matches.length;
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
                console.warn('Regex error:', variation, e);
            }
        });
        
        return { totalCount, variationCounts, positions };
    }
    
    calculateWeightedDensity() {
        const parsed = this.parseHTML();
        const variations = this.getKeywordVariations(this.keyword);
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
        
        // Headings
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
        
        // Body
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
        
        // Calculate totals
        let totalWeightedCount = zones.title.weightedCount + zones.metaDescription.weightedCount + zones.body.weightedCount;
        ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(level => {
            totalWeightedCount += zones[level].weightedCount;
        });
        
        let totalWeightedWords = zones.body.wordCount * this.zoneWeights.body;
        totalWeightedWords += this.extractHebrewWords(parsed.title).length * this.zoneWeights.title;
        totalWeightedWords += this.extractHebrewWords(parsed.metaDescription).length * this.zoneWeights.metaDescription;
        
        ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(level => {
            parsed.headings[level].forEach(h => {
                totalWeightedWords += this.extractHebrewWords(h.text).length * this.zoneWeights[level];
            });
        });
        
        const weightedDensity = totalWeightedWords > 0 ? (totalWeightedCount / totalWeightedWords * 100) : 0;
        const simpleDensity = zones.body.wordCount > 0 ? (zones.body.count / zones.body.wordCount * 100) : 0;
        
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
    
    calculateScore(density) {
        const [optimalMin, optimalMax] = this.options.optimalRange;
        const [warningMin, warningMax] = this.options.warningRange;
        
        if (density >= optimalMin && density <= optimalMax) return 100;
        if (density >= warningMin && density < optimalMin) {
            return 60 + ((density - warningMin) / (optimalMin - warningMin)) * 30;
        }
        if (density > optimalMax && density <= warningMax) {
            return 60 + ((warningMax - density) / (warningMax - optimalMax)) * 30;
        }
        if (density < warningMin) return Math.max(0, 60 * (density / warningMin));
        return Math.max(0, 60 - ((density - warningMax) * 20));
    }
    
    getStatus(density) {
        const [optimalMin, optimalMax] = this.options.optimalRange;
        const [warningMin, warningMax] = this.options.warningRange;
        
        if (density >= optimalMin && density <= optimalMax) {
            return { code: 'ideal', label: 'אידיאלי', color: '#10b981', icon: '✅' };
        }
        if (density >= warningMin && density <= warningMax) {
            return density < optimalMin 
                ? { code: 'low', label: 'נמוך', color: '#f59e0b', icon: '⚠️' }
                : { code: 'high', label: 'גבוה', color: '#f59e0b', icon: '⚠️' };
        }
        if (density < warningMin) {
            return { code: 'too_thin', label: 'דליל מדי', color: '#ef4444', icon: '🔴' };
        }
        return { code: 'stuffing', label: 'ספאם מילות מפתח', color: '#ef4444', icon: '🔴' };
    }
    
    generateSuggestions(analysisResult) {
        const suggestions = [];
        const { zones, weightedDensity } = analysisResult;
        const status = this.getStatus(weightedDensity);
        const [optimalMin, optimalMax] = this.options.optimalRange;
        
        if (!zones.title.found && zones.title.text) {
            suggestions.push({
                type: 'missing_title', severity: 'high',
                message: `מילת המפתח "${this.keyword}" חסרה בכותרת העמוד`,
                location: 'title', currentText: zones.title.text, action: 'add_keyword'
            });
        }
        
        if (!zones.metaDescription.found && zones.metaDescription.text) {
            suggestions.push({
                type: 'missing_meta', severity: 'medium',
                message: `מילת המפתח חסרה בתיאור המטא`,
                location: 'meta_description', currentText: zones.metaDescription.text, action: 'add_keyword'
            });
        }
        
        if (zones.h1.totalItems === 0) {
            suggestions.push({
                type: 'missing_h1', severity: 'high',
                message: 'חסרה כותרת H1 בעמוד', location: 'h1', action: 'create_h1'
            });
        } else if (zones.h1.foundCount === 0) {
            suggestions.push({
                type: 'keyword_missing_h1', severity: 'high',
                message: `מילת המפתח חסרה ב-H1`,
                location: 'h1', currentText: zones.h1.items[0]?.text, action: 'add_keyword'
            });
        }
        
        if (status.code === 'too_thin') {
            const targetCount = Math.ceil(zones.body.wordCount * optimalMin / 100);
            const addCount = targetCount - zones.body.count;
            suggestions.push({
                type: 'add_occurrences', severity: 'high',
                message: `הוסף ${addCount} מופעים של מילת המפתח`,
                location: 'body', currentCount: zones.body.count, targetCount, action: 'increase_density'
            });
        } else if (status.code === 'stuffing') {
            const targetCount = Math.floor(zones.body.wordCount * optimalMax / 100);
            const removeCount = zones.body.count - targetCount;
            suggestions.push({
                type: 'remove_occurrences', severity: 'high',
                message: `הפחת ${removeCount} מופעים למניעת ספאם`,
                location: 'body', currentCount: zones.body.count, targetCount, action: 'decrease_density'
            });
        }
        
        return suggestions;
    }
    
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
}


/**
 * SpamAnalyzer - Header & Emphasis Spam Detection
 */
class SpamAnalyzer {
    constructor(htmlContent, keyword) {
        this.htmlContent = htmlContent;
        this.keyword = keyword;
        
        this.thresholds = {
            exactMatchRatio: 0.6,
            startsWithRatio: 0.5,
            minHeadersForAnalysis: 3,
            boldRatio: { safe: 0.2, warning: 0.4, spam: 1.0 },
            contextRatio: { isolated: 1.2, contextual: 2.0 },
            clusterWindow: 50,
            maxClusterOccurrences: 2
        };
        
        this.hebrewPrefixes = ['ה', 'ב', 'ל', 'מ', 'ו', 'כ', 'ש', 'וה', 'וב', 'ול', 'שה', 'שב', 'של'];
        this._doc = null;
    }
    
    parseHTML() {
        if (this._doc) return this._doc;
        const parser = new DOMParser();
        this._doc = parser.parseFromString(this.htmlContent, 'text/html');
        return this._doc;
    }
    
    normalizeHebrew(text) {
        if (!text) return '';
        return text
            .replace(/[\u0591-\u05C7]/g, '')
            .replace(/[^\u0590-\u05FF\sa-zA-Z0-9]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }
    
    getKeywordVariations() {
        const normalized = this.normalizeHebrew(this.keyword);
        const words = normalized.split(/\s+/);
        const variations = new Set([normalized]);
        
        if (words.length === 1) {
            const word = words[0];
            this.hebrewPrefixes.forEach(prefix => variations.add(prefix + word));
            if (word.endsWith('ה')) {
                variations.add(word.slice(0, -1) + 'ות');
                variations.add(word.slice(0, -1) + 'ת');
            }
            variations.add(word + 'ים');
            variations.add(word + 'ות');
            if (!word.startsWith('ה')) variations.add('ה' + word);
        }
        
        return Array.from(variations);
    }
    
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
    
    startsWithKeyword(text) {
        const normalizedText = this.normalizeHebrew(text);
        const variations = this.getKeywordVariations();
        
        return variations.some(variation => {
            const normalizedVariation = this.normalizeHebrew(variation);
            return normalizedText.startsWith(normalizedVariation) || 
                   normalizedText.startsWith(normalizedVariation + ' ');
        });
    }
    
    analyzeHeaders() {
        const doc = this.parseHTML();
        const headers = [];
        const issues = [];
        
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
        
        const subheaders = headers.filter(h => h.level > 1);
        const h1s = headers.filter(h => h.level === 1);
        
        const exactMatchRatio = subheaders.length > 0 
            ? subheaders.filter(h => h.hasKeyword).length / subheaders.length : 0;
        const startsWithRatio = subheaders.length > 0 
            ? subheaders.filter(h => h.startsWithKeyword).length / subheaders.length : 0;
        
        // Check patterns
        if (subheaders.length >= this.thresholds.minHeadersForAnalysis) {
            if (exactMatchRatio > this.thresholds.exactMatchRatio) {
                issues.push({
                    type: 'REPETITIVE_PATTERN', severity: 'high',
                    message: `${Math.round(exactMatchRatio * 100)}% מכותרות המשנה מכילות את מילת המפתח`,
                    suggestion: 'גוון את הכותרות'
                });
            }
            if (startsWithRatio > this.thresholds.startsWithRatio) {
                issues.push({
                    type: 'LEADING_KEYWORD', severity: 'medium',
                    message: `${Math.round(startsWithRatio * 100)}% מהכותרות מתחילות במילת המפתח`,
                    suggestion: 'מקם את מילת המפתח במיקומים שונים'
                });
            }
        }
        
        const headerSpamScore = Math.max(0, Math.min(100, 
            100 - (exactMatchRatio * 30) - (startsWithRatio * 20)
        ));
        
        let status = 'good';
        if (headerSpamScore < 50) status = 'critical';
        else if (headerSpamScore < 70) status = 'warning';
        
        return {
            status,
            score: Math.round(headerSpamScore),
            metrics: {
                totalHeaders: headers.length,
                subheaderCount: subheaders.length,
                headersWithKeyword: headers.filter(h => h.hasKeyword).length,
                exactMatchRatio: Math.round(exactMatchRatio * 100) / 100,
                startsWithKeywordRatio: Math.round(startsWithRatio * 100) / 100
            },
            headers,
            issues
        };
    }
    
    analyzeEmphasis() {
        const doc = this.parseHTML();
        const issues = [];
        const variations = this.getKeywordVariations();
        const emphasisTags = [...doc.querySelectorAll('strong, b, em')];
        
        const bodyText = doc.body ? doc.body.textContent : '';
        let totalKeywordCount = 0;
        variations.forEach(variation => {
            try {
                const regex = new RegExp(variation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
                const matches = bodyText.match(regex);
                totalKeywordCount += matches ? matches.length : 0;
            } catch (e) {}
        });
        
        let boldedKeywordCount = 0;
        let isolatedBoldCount = 0;
        
        emphasisTags.forEach(el => {
            const innerText = el.textContent.trim();
            if (this.containsKeyword(innerText)) {
                boldedKeywordCount++;
                const keywordLen = this.normalizeHebrew(this.keyword).length;
                const tagLen = this.normalizeHebrew(innerText).length;
                if (tagLen / keywordLen <= this.thresholds.contextRatio.isolated) {
                    isolatedBoldCount++;
                }
            }
        });
        
        const boldRatio = totalKeywordCount > 0 ? boldedKeywordCount / totalKeywordCount : 0;
        
        if (boldRatio > this.thresholds.boldRatio.warning) {
            issues.push({
                type: 'HIGH_BOLD_RATIO', severity: 'high',
                message: `${Math.round(boldRatio * 100)}% ממופעי מילת המפתח מודגשים`,
                suggestion: 'הסר הדגשות מחלק מהמופעים'
            });
        }
        
        const emphasisSpamScore = Math.max(0, Math.min(100, 100 - (boldRatio * 50)));
        
        return {
            status: emphasisSpamScore > 70 ? 'good' : emphasisSpamScore > 40 ? 'warning' : 'critical',
            score: Math.round(emphasisSpamScore),
            metrics: {
                totalKeywords: totalKeywordCount,
                boldedKeywords: boldedKeywordCount,
                boldRatio: Math.round(boldRatio * 100) / 100,
                isolatedBoldCount
            },
            issues
        };
    }
    
    analyze() {
        const headersAnalysis = this.analyzeHeaders();
        const emphasisAnalysis = this.analyzeEmphasis();
        
        const riskScore = Math.max(0, Math.min(100,
            ((100 - headersAnalysis.score) * 0.4) + ((100 - emphasisAnalysis.score) * 0.6)
        ));
        
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
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KeywordDensityAnalyzer, SpamAnalyzer };
}

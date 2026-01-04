// ========================================
// אלגוריתם מתקדם לזיהוי תוכן AI - גרסה 3.0 PRO
// כולל: Pseudo-Perplexity, N-gram Analysis, Zipf's Law, Vocabulary Fingerprint
// ========================================

/**
 * 📚 תוכן עניינים - מפת הקוד (Code Map)
 * =============================================================================
 * 
 * 1. 📥 הכנה וניקוי ראשוני
 *    - extractHebrewContent() ..... חילוץ טקסט נקי מ-HTML, הסרת סקריפטים ו-Schema
 *    - cleanText ................... הטקסט שעליו מתבצע הניתוח (ללא תגיות)
 * 
 * 2. 📖 מילונים והגדרות (Dictionaries & Config)
 *    - aiPhrases ................... ביטויים מסגירים של AI ("בסיכומו של דבר", "חשוב לציין")
 *    - claudePhrases ............... ביטויים ייחודיים למודל Claude
 *    - formalToCasualMap ........... מילון להנמכת משלב (מילים גבוהות -> שפה יומיומית)
 *    - hebrewStopWords ............. מילות עצירה (לניתוח סטטיסטי)
 * 
 * 3. 🧠 מנוע ניתוח (Analysis Engine)
 *    - analyzeText() ............... הפונקציה הראשית שמנהלת את כל הבדיקות
 *    - checkProSignals() ........... זיהוי תבניות מורכבות (חזרתיות, מבנה דידקטי)
 *    - calculatePerplexity() ....... חישוב מורכבות הטקסט (סימולציה)
 *    - analyzeNgrams() ............. זיהוי רצפי מילים נפוצים של מכונות
 *    - checkZipfLaw() .............. בדיקת התפלגות מילים טבעית
 * 
 * 4. 🧹 מנוע ניקוי והאנשה (Humanization Engine)
 *    - basicCleanText() ............ [חדש!] ניקוי טכני שרץ תמיד (אימוג'ים, שפות זרות, תווים)
 *    - humanizeText() .............. [חדש!] מנוע השכתוב (רץ רק אם הציון גבוה)
 *    - addHumanTouches() ........... הוספת "רעש אנושי" (סלנג, גיוון פתיחות, משפטים קצרים)
 * 
 * 5. ⚙️ לוגיקה ראשית (Main Execution)
 *    - [סוף הקובץ] ................. קריאה ל-basicCleanText -> בדיקת ציון -> הפעלת humanizeText -> יצירת דוחות
 * 
 * =============================================================================
 */

const rawInput = $input.first().json.content.raw;

const rawText = typeof rawInput === 'string'
  ? rawInput
  : (typeof rawInput === 'object' && rawInput !== null
    ? JSON.stringify(rawInput)
    : ''
  );

// ========================================
// 🔧 ניקוי מתקדם - חילוץ תוכן עברי בלבד
// ========================================

function extractHebrewContent(html) {
  let text = html;
  
  // 1. הסרת JSON-LD Schema - מזהה את הפתיחה והסגירה
  const jsonLdStart = text.indexOf('application/ld+json');
  if (jsonLdStart > -1) {
    // מחפש את כל הסקריפטים מסוג json-ld ומסיר אותם
    let result = '';
    let i = 0;
    let jsonLoopLimit = 0;
    while (i < text.length && jsonLoopLimit < 100) {
      jsonLoopLimit++;
      const scriptStart = text.indexOf('<script', i);
      if (scriptStart === -1) {
        result += text.substring(i);
        break;
      }
      const scriptEnd = text.indexOf('</script>', scriptStart);
      if (scriptEnd === -1) {
        result += text.substring(i);
        break;
      }
      const scriptContent = text.substring(scriptStart, scriptEnd + 9);
      if (scriptContent.indexOf('application/ld+json') === -1) {
        result += text.substring(i, scriptEnd + 9);
      } else {
        result += text.substring(i, scriptStart);
      }
      i = scriptEnd + 9;
    }
    text = result;
  }
  
  // 2. הסרת כל ה-scripts שנשארו
  let scriptSafetyCounter = 0;
  while (text.indexOf('<script') > -1 && scriptSafetyCounter < 100) {
    scriptSafetyCounter++;
    const start = text.indexOf('<script');
    const end = text.indexOf('</script>', start);
    if (end > -1) {
      text = text.substring(0, start) + ' ' + text.substring(end + 9);
    } else {
      break;
    }
  }
  
  // 3. הסרת styles
  let styleSafetyCounter = 0;
  while (text.indexOf('<style') > -1 && styleSafetyCounter < 100) {
    styleSafetyCounter++;
    const start = text.indexOf('<style');
    const end = text.indexOf('</style>', start);
    if (end > -1) {
      text = text.substring(0, start) + ' ' + text.substring(end + 8);
    } else {
      break;
    }
  }
  
  // 4. הסרת WordPress shortcodes כמו [awg postid="32400"]
  text = text.replace(/\[[^\]]+\]/g, '');
  
  // 5. הסרת תגיות HTML אבל שמירת התוכן
  text = text.replace(/<[^>]+>/g, ' ');
  
  // 6. ניקוי HTML entities
  text = text.replace(/&nbsp;/g, ' ');
  text = text.replace(/&amp;/g, '&');
  text = text.replace(/&lt;/g, '<');
  text = text.replace(/&gt;/g, '>');
  text = text.replace(/&quot;/g, '"');
  text = text.replace(/&#39;/g, "'");
  text = text.replace(/&[#\w]+;/gi, ' ');
  
  // 7. הסרת URLs
  text = text.replace(/https?:\/\/[^\s]+/g, '');
  
  // 8. הסרת כתובות אימייל
  text = text.replace(/[\w.-]+@[\w.-]+\.\w+/g, '');
  
  // 9. הסרת מספרי טלפון בינלאומיים
  text = text.replace(/\+972[\d\s-]+/g, '');
  
  // 10. הסרת JSON שנשאר (סוגריים מסולסלים)
  text = text.replace(/\{[^{}]*\}/g, '');
  
  // 11. ניקוי רווחים מיותרים
  text = text.replace(/\s+/g, ' ').trim();
  
  return text;
}

// ניקוי HTML וחילוץ תוכן עברי בלבד
const cleanText = extractHebrewContent(rawText);

// סף מינימום מוגדל ל-200 תווים לניתוח מהימן יותר
if (cleanText.length < 200) {
  return [
    {
      json: {
        score: 0,
        confidence: 'נמוכה',
        explanation: 'הטקסט קצר מדי לניתוח מהימן (פחות מ-200 תווים).',
        issues: ['טקסט קצר'],
        summary: '• הארך את הטקסט ליותר מ-200 תווים כדי לבצע ניתוח תקף.',
        rawText,
        cleanText
      }
    }
  ];
}

// ----------------------------------------------------------------------------------------------
// מילות עצירה בעברית - לסינון בניתוחים
// ----------------------------------------------------------------------------------------------
const hebrewStopWords = new Set([
  'את', 'של', 'על', 'עם', 'אל', 'מן', 'או', 'גם', 'רק', 'כי', 'אם', 'לא',
  'הוא', 'היא', 'הם', 'הן', 'אני', 'אתה', 'את', 'אנחנו', 'אתם', 'אתן',
  'זה', 'זאת', 'זו', 'אלה', 'אלו', 'כל', 'כך', 'יש', 'אין', 'היה', 'היתה',
  'להיות', 'יהיה', 'תהיה', 'עוד', 'כבר', 'אז', 'פה', 'שם', 'מה', 'מי',
  'איך', 'למה', 'מתי', 'איפה', 'כמה', 'אשר', 'לו', 'לה', 'להם', 'להן',
  'בו', 'בה', 'בהם', 'בהן', 'ממנו', 'ממנה', 'מהם', 'מהן', 'שלו', 'שלה'
]);

/**
 * 🆕 מילים "ריקות" (Fluff) ש-AI משתמש בהן כדי למרוח זמן
 */
const fluffWords = new Set([
  'בבחינת', 'במידה ו', 'על מנת', 'באמצעות', 'במסגרת', 'בהקשר ל',
  'מבחינת', 'בנוגע ל', 'באופן של', 'בצורה של', 'תהליך של',
  'נושא של', 'עניין של', 'היבט של', 'סוג של', 'כלומר',
  'דהיינו', 'רוצה לומר', 'זאת אומרת', 'משמע', 'בו זמנית',
  'יחד עם זאת', 'אף על פי כן', 'חרף העובדה', 'בסופו של יום',
  'כפי שצויין', 'כאמור לעיל', 'יש לציין', 'חשוב להדגיש'
]);

/**
 * 🆕 מילות קישור "אנושיות" (שבירת פורמליות)
 */
// 🔥 תיקון: הסרנו מחברים עם " - " כי זה סימן GPT!
const humanConnectors = [
  'הנה,', 'ועוד דבר:', 'משהו נוסף:', 'גם כדאי לדעת ש', 'ובנוסף,',
  'מעניין ש', 'שווה לציין ש', 'עוד נקודה חשובה:', 'וגם,', 'דרך אגב,'
];

/**
 * 🕵️‍♂️ ניתוח דחיסות סמנטית (Fluff Detection)
 * בודק יחס בין מילים משמעותיות לבין "מריחת זמן"
 */
function analyzeSemanticDensity(text) {
  const words = text.split(/\s+/);
  let fluffCount = 0;
  
  words.forEach(word => {
    const cleanWord = word.replace(/[.,!?;:]/g, '');
    if (fluffWords.has(cleanWord)) {
      fluffCount++;
    }
  });
  
  const densityScore = 1 - (fluffCount / (words.length || 1));
  
  return {
    score: densityScore,
    isFluffy: densityScore < 0.95,
    fluffCount: fluffCount
  };
}

// ----------------------------------------------------------------------------------------------
// פונקציות PRO לזיהוי AI ברמה גבוהה
// ----------------------------------------------------------------------------------------------

/**
 * מילון תדירות מילים בעברית - המילים הכי נפוצות
 * משמש לחישוב Pseudo-Perplexity
 */
const hebrewWordFrequency = {
  // Top 100 מילים נפוצות בעברית (ציון 1-100, 100 = הכי נפוץ)
  'של': 100, 'את': 99, 'על': 98, 'עם': 97, 'אל': 96, 'הוא': 95, 'היא': 94,
  'לא': 93, 'זה': 92, 'אני': 91, 'כל': 90, 'מה': 89, 'יש': 88, 'אם': 87,
  'או': 86, 'גם': 85, 'היה': 84, 'כי': 83, 'הם': 82, 'אבל': 81, 'עוד': 80,
  'רק': 79, 'כמו': 78, 'אחד': 77, 'בין': 76, 'אחרי': 75, 'לפני': 74, 'כך': 73,
  'מי': 72, 'איך': 71, 'למה': 70, 'מתי': 69, 'היכן': 68, 'כמה': 67, 'הרבה': 66,
  'קצת': 65, 'יותר': 64, 'פחות': 63, 'טוב': 62, 'רע': 61, 'חדש': 60, 'ישן': 59,
  'גדול': 58, 'קטן': 57, 'יפה': 56, 'חשוב': 55, 'צריך': 54, 'רוצה': 53, 'יכול': 52,
  'חייב': 51, 'אפשר': 50, 'בגלל': 49, 'בשביל': 48, 'לכן': 47, 'אולי': 46, 'בטח': 45,
  // מילים פחות נפוצות
  'אסטרטגיה': 5, 'פרדיגמה': 3, 'אונטולוגיה': 2, 'אפיסטמולוגי': 1,
  'דיכוטומיה': 2, 'הוליסטי': 3, 'סינרגיה': 4, 'אופטימיזציה': 5
};

/**
 * ביגרמים (צמדי מילים) נפוצים ב-AI
 * AI נוטה להשתמש בצמדים "בטוחים"
 */
const aiBigrams = [
  'ניתן לומר', 'חשוב לציין', 'יש לזכור', 'ראוי להזכיר', 'מן הראוי',
  'באופן כללי', 'באופן משמעותי', 'באופן ניכר', 'באופן מובהק',
  'לאור זאת', 'בהתאם לכך', 'כתוצאה מכך', 'בנוסף לכך', 'מעבר לכך',
  'חשוב להדגיש', 'חשוב להבין', 'חשוב לזכור', 'יש להניח', 'יש לקחת',
  'במידה רבה', 'במידה מסוימת', 'בצורה משמעותית', 'בצורה ניכרת',
  'לסיכום ניתן', 'בסופו של', 'בשורה התחתונה', 'ניתן להסיק',
  'כפי שצוין', 'כפי שהוזכר', 'כאמור לעיל', 'כמו שנאמר'
];

/**
 * טריגרמים (שלשות מילים) שמזהות AI
 */
const aiTrigrams = [
  'ניתן לומר כי', 'חשוב לציין כי', 'יש לזכור כי', 'ראוי לציין כי',
  'באופן כללי ניתן', 'לאור האמור לעיל', 'בהתאם לנאמר לעיל',
  'כפי שניתן לראות', 'כפי שהוסבר לעיל', 'כמו שצוין קודם',
  'על מנת להבין', 'על מנת לבחון', 'בכדי להבין את'
];

/**
 * 🔥 Pseudo-Perplexity Analysis
 * מחשב כמה הטקסט "צפוי" - AI כותב טקסט צפוי יותר
 */
function analyzePseudoPerplexity(text) {
  const words = text.match(/[\u0590-\u05FF]+/g) || [];
  if (words.length < 10) {
    return { perplexityScore: 0.5, isLowPerplexity: false };
  }
  
  let totalFrequencyScore = 0;
  let knownWordCount = 0;
  let rareWordCount = 0;
  let veryCommonCount = 0;
  
  words.forEach(word => {
    const freq = hebrewWordFrequency[word] || 0;
    if (freq > 0) {
      totalFrequencyScore += freq;
      knownWordCount++;
      if (freq > 70) veryCommonCount++;
    } else {
      // מילה לא ברשימה - יכולה להיות נדירה או ספציפית
      rareWordCount++;
    }
  });
  
  // חישוב יחסים
  const avgFrequency = knownWordCount > 0 ? totalFrequencyScore / knownWordCount : 50;
  const commonRatio = veryCommonCount / words.length;
  const rareRatio = rareWordCount / words.length;
  
  // AI נוטה להשתמש במילים נפוצות יותר (avgFrequency גבוה)
  // ובפחות מילים נדירות (rareRatio נמוך)
  
  // ציון: 0 = אנושי מאוד, 1 = AI מאוד
  let perplexityScore = 0;
  
  if (avgFrequency > 55) perplexityScore += 0.3;
  else if (avgFrequency > 45) perplexityScore += 0.15;
  
  if (commonRatio > 0.3) perplexityScore += 0.25;
  else if (commonRatio > 0.2) perplexityScore += 0.1;
  
  if (rareRatio < 0.15) perplexityScore += 0.25;
  else if (rareRatio < 0.25) perplexityScore += 0.1;
  
  // נרמול ל-0-1
  perplexityScore = Math.min(1, perplexityScore);
  
  return {
    perplexityScore,
    avgWordFrequency: avgFrequency,
    commonWordRatio: commonRatio,
    rareWordRatio: rareRatio,
    isLowPerplexity: perplexityScore > 0.5, // מעל 0.5 = חשוד כ-AI
    analysis: perplexityScore > 0.6 ? 'טקסט צפוי מאוד - חשוד כ-AI' :
              perplexityScore > 0.4 ? 'טקסט עם רמת צפיות בינונית' :
              'טקסט עם מילים מגוונות - אנושי יותר'
  };
}

/**
 * 🔥 N-gram Analysis
 * בודק צמדים ושלשות מילים אופייניים ל-AI
 */
function analyzeNgrams(text) {
  const lowerText = text.toLowerCase();
  
  // ספירת bigrams
  let bigramHits = [];
  aiBigrams.forEach(bigram => {
    const count = (lowerText.match(new RegExp(bigram, 'g')) || []).length;
    if (count > 0) {
      bigramHits.push({ bigram, count });
    }
  });
  
  // ספירת trigrams
  let trigramHits = [];
  aiTrigrams.forEach(trigram => {
    const count = (lowerText.match(new RegExp(trigram, 'g')) || []).length;
    if (count > 0) {
      trigramHits.push({ trigram, count });
    }
  });
  
  // חישוב ציון
  const bigramScore = bigramHits.reduce((sum, h) => sum + h.count * 3, 0);
  const trigramScore = trigramHits.reduce((sum, h) => sum + h.count * 5, 0);
  const totalScore = bigramScore + trigramScore;
  
  // נרמול לפי אורך הטקסט
  const words = text.split(/\s+/).length;
  const normalizedScore = totalScore / Math.max(words / 50, 1);
  
  return {
    bigramHits,
    trigramHits,
    bigramCount: bigramHits.length,
    trigramCount: trigramHits.length,
    rawScore: totalScore,
    normalizedScore: Math.min(normalizedScore, 30),
    isAIPattern: normalizedScore > 5,
    analysis: normalizedScore > 10 ? 'שימוש מוגזם בדפוסי AI' :
              normalizedScore > 5 ? 'נמצאו מספר דפוסי AI' :
              'דפוסי כתיבה טבעיים'
  };
}

/**
 * 🔥 Zipf's Law Analysis
 * חוק זיפף: בטקסט טבעי, המילה הנפוצה ביותר מופיעה פי 2 מהשנייה, פי 3 מהשלישית, וכו'
 * AI נוטה לחרוג מחוק זה
 */
function analyzeZipfLaw(text) {
  const words = text.match(/[\u0590-\u05FF]+/g) || [];
  if (words.length < 50) {
    return { zipfDeviation: 0, followsZipf: true };
  }
  
  // ספירת תדירות מילים
  const freq = {};
  words.forEach(w => {
    const lower = w.toLowerCase();
    if (!hebrewStopWords.has(lower)) {
      freq[lower] = (freq[lower] || 0) + 1;
    }
  });
  
  // מיון לפי תדירות
  const sorted = Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20); // Top 20
  
  if (sorted.length < 5) {
    return { zipfDeviation: 0, followsZipf: true };
  }
  
  // חישוב סטייה מחוק זיפף
  const topFreq = sorted[0][1];
  let totalDeviation = 0;
  let comparisons = 0;
  
  for (let i = 1; i < Math.min(sorted.length, 10); i++) {
    const expectedFreq = topFreq / (i + 1);
    const actualFreq = sorted[i][1];
    const deviation = Math.abs(actualFreq - expectedFreq) / expectedFreq;
    totalDeviation += deviation;
    comparisons++;
  }
  
  const avgDeviation = totalDeviation / comparisons;
  
  // AI בדרך כלל יש סטייה נמוכה יותר מזיפף (יותר מדי "מושלם")
  // או סטייה גבוהה מאוד (שימוש חריג במילים)
  
  return {
    zipfDeviation: avgDeviation,
    topWords: sorted.slice(0, 5).map(([word, count]) => ({ word, count })),
    followsZipf: avgDeviation > 0.3 && avgDeviation < 1.5,
    isTooUniform: avgDeviation < 0.2, // חשוד - AI יותר מדי אחיד
    isTooRandom: avgDeviation > 2.0, // חשוד - AI לפעמים חריג
    analysis: avgDeviation < 0.2 ? 'התפלגות מילים אחידה מדי - חשוד' :
              avgDeviation > 2.0 ? 'התפלגות מילים חריגה' :
              'התפלגות מילים טבעית'
  };
}

/**
 * 🔥 Vocabulary Fingerprint
 * AI משתמש בסט מילים צפוי יותר מאשר אנושיים
 */
function analyzeVocabularyFingerprint(text) {
  const words = text.match(/[\u0590-\u05FF]+/g) || [];
  if (words.length < 30) {
    return { vocabularyScore: 0.5, isLimitedVocab: false };
  }
  
  const uniqueWords = new Set(words.map(w => w.toLowerCase()));
  const totalWords = words.length;
  
  // Type-Token Ratio (TTR)
  const ttr = uniqueWords.size / totalWords;
  
  // Hapax Legomena - מילים שמופיעות פעם אחת בלבד
  const freq = {};
  words.forEach(w => {
    const lower = w.toLowerCase();
    freq[lower] = (freq[lower] || 0) + 1;
  });
  
  const hapaxCount = Object.values(freq).filter(f => f === 1).length;
  const hapaxRatio = hapaxCount / uniqueWords.size;
  
  // מילים ארוכות (סימן לאוצר מילים עשיר)
  const longWords = words.filter(w => w.length > 6).length;
  const longWordRatio = longWords / totalWords;
  
  // חישוב ציון
  let vocabScore = 0;
  
  // TTR נמוך = מילים חוזרות הרבה = AI
  if (ttr < 0.3) vocabScore += 0.3;
  else if (ttr < 0.4) vocabScore += 0.15;
  else if (ttr > 0.6) vocabScore -= 0.1; // אנושי
  
  // Hapax נמוך = פחות מילים ייחודיות = AI
  if (hapaxRatio < 0.4) vocabScore += 0.25;
  else if (hapaxRatio > 0.6) vocabScore -= 0.1;
  
  // מעט מילים ארוכות = AI משתמש במילים "בטוחות"
  if (longWordRatio < 0.1) vocabScore += 0.2;
  else if (longWordRatio > 0.2) vocabScore -= 0.1;
  
  vocabScore = Math.max(0, Math.min(1, vocabScore + 0.3));

  return {
    vocabularyScore: vocabScore,
    typeTokenRatio: ttr,
    hapaxRatio,
    longWordRatio,
    uniqueWordCount: uniqueWords.size,
    isLimitedVocab: vocabScore > 0.5,
    analysis: vocabScore > 0.6 ? 'אוצר מילים מוגבל - אופייני ל-AI' :
              vocabScore < 0.3 ? 'אוצר מילים עשיר - אנושי' :
              'אוצר מילים בינוני'
  };
}

/**
 * 🔥 Repetition Pattern Analysis
 * AI חוזר על מבנים דומים יותר מאנושיים
 */
function analyzeRepetitionPatterns(text) {
  const sentences = text.split(/[.!?]\s+/).filter(s => s.trim().length > 0);
  if (sentences.length < 5) {
    return { repetitionScore: 0, hasRepetitiveStructure: false };
  }
  
  // ניתוח מבנה משפט (לפי מילה ראשונה ואחרונה)
  const structures = sentences.map(s => {
    const words = s.trim().split(/\s+/);
    return {
      firstWord: words[0]?.toLowerCase() || '',
      lastWord: words[words.length - 1]?.toLowerCase() || '',
      wordCount: words.length,
      // קטגוריית אורך
      lengthCategory: words.length < 8 ? 'short' : words.length < 15 ? 'medium' : 'long'
    };
  });
  
  // ספירת חזרות על מבנים
  let structureRepetitions = 0;
  let lengthPatternRepetitions = 0;
  
  for (let i = 1; i < structures.length; i++) {
    // אותה מילה ראשונה
    if (structures[i].firstWord === structures[i-1].firstWord) {
      structureRepetitions++;
    }
    // אותה קטגוריית אורך
    if (structures[i].lengthCategory === structures[i-1].lengthCategory) {
      lengthPatternRepetitions++;
    }
  }
  
  // רצפים של אורכים דומים
  let consecutiveSimilarLength = 0;
  let maxConsecutive = 0;
  for (let i = 1; i < structures.length; i++) {
    const diff = Math.abs(structures[i].wordCount - structures[i-1].wordCount);
    if (diff <= 3) {
      consecutiveSimilarLength++;
      maxConsecutive = Math.max(maxConsecutive, consecutiveSimilarLength);
    } else {
      consecutiveSimilarLength = 0;
    }
  }
  
  // חישוב ציון
  const structureRepRate = structureRepetitions / (sentences.length - 1);
  const lengthRepRate = lengthPatternRepetitions / (sentences.length - 1);
  
  let repetitionScore = 0;
  if (structureRepRate > 0.3) repetitionScore += 15;
  else if (structureRepRate > 0.2) repetitionScore += 8;
  
  if (lengthRepRate > 0.6) repetitionScore += 12;
  else if (lengthRepRate > 0.4) repetitionScore += 6;
  
  if (maxConsecutive >= 4) repetitionScore += 10;
  else if (maxConsecutive >= 3) repetitionScore += 5;
  
  return {
    repetitionScore,
    structureRepetitionRate: structureRepRate,
    lengthPatternRate: lengthRepRate,
    maxConsecutiveSimilarLength: maxConsecutive,
    hasRepetitiveStructure: repetitionScore > 15,
    analysis: repetitionScore > 20 ? 'מבנה חזרתי מאוד - אופייני ל-AI' :
              repetitionScore > 10 ? 'יש דפוסי חזרה' :
              'מבנה מגוון - אנושי'
  };
}

/**
 * 🔥 Sentence Rhythm Analysis
 * אנושיים כותבים עם "קצב" משתנה, AI יותר מונוטוני
 */
function analyzeSentenceRhythm(text) {
  const sentences = text.split(/[.!?]\s+/).filter(s => s.trim().length > 0);
  if (sentences.length < 5) {
    return { rhythmScore: 0.5, hasNaturalRhythm: true };
  }
  
  const lengths = sentences.map(s => s.split(/\s+/).length);
  
  // חישוב "מומנטום" - שינויים דרמטיים באורך
  const changes = [];
  for (let i = 1; i < lengths.length; i++) {
    changes.push(lengths[i] - lengths[i-1]);
  }
  
  // סטיית תקן של השינויים
  const avgChange = changes.reduce((a, b) => a + b, 0) / changes.length;
  const changeVariance = changes.reduce((sum, c) => sum + Math.pow(c - avgChange, 2), 0) / changes.length;
  const changeStdDev = Math.sqrt(changeVariance);
  
  // ספירת "קפיצות דרמטיות" (שינוי של יותר מ-8 מילים)
  const dramaticChanges = changes.filter(c => Math.abs(c) > 8).length;
  const dramaticRatio = dramaticChanges / changes.length;
  
  // ספירת "רצפים מונוטוניים" (3+ משפטים ברצף עם אורך דומה)
  let monotoneSequences = 0;
  let currentSequence = 1;
  for (let i = 1; i < lengths.length; i++) {
    if (Math.abs(lengths[i] - lengths[i-1]) <= 2) {
      currentSequence++;
      if (currentSequence >= 3) monotoneSequences++;
    } else {
      currentSequence = 1;
    }
  }
  
  // חישוב ציון קצב
  let rhythmScore = 0.5; // התחלה ניטרלית
  
  // סטיית תקן נמוכה = מונוטוני = AI
  if (changeStdDev < 3) rhythmScore += 0.25;
  else if (changeStdDev > 6) rhythmScore -= 0.15;
  
  // מעט קפיצות דרמטיות = AI
  if (dramaticRatio < 0.1) rhythmScore += 0.15;
  else if (dramaticRatio > 0.25) rhythmScore -= 0.1;
  
  // הרבה רצפים מונוטוניים = AI
  if (monotoneSequences > 2) rhythmScore += 0.2;
  
  rhythmScore = Math.max(0, Math.min(1, rhythmScore));
  
  return {
    rhythmScore,
    changeStdDev,
    dramaticChangeRatio: dramaticRatio,
    monotoneSequences,
    hasNaturalRhythm: rhythmScore < 0.5,
    analysis: rhythmScore > 0.65 ? 'קצב מונוטוני - אופייני ל-AI' :
              rhythmScore < 0.35 ? 'קצב דינמי - אנושי' :
              'קצב בינוני'
  };
}

/**
 * 🔥 Special Characters Analysis
 * AI משתמש בתווים מיוחדים "מפוארים" במקום פשוטים
 */
function analyzeSpecialCharacters(text) {
  let specialCharScore = 0;
  const findings = [];
  
  // דאשים מפוארים
  const enDashCount = (text.match(/–/g) || []).length;
  const emDashCount = (text.match(/—/g) || []).length;
  const totalFancyDashes = enDashCount + emDashCount;
  
  if (totalFancyDashes > 0) {
    specialCharScore += Math.min(totalFancyDashes * 2, 15);
    findings.push({ type: 'דאשים מפוארים', count: totalFancyDashes });
  }
  
  // 🆕 מקפים עם רווחים באמצע משפט " - " - סימן מובהק ל-GPT!
  // 🔥 חשוב: לא לספור bullet points - רק מקפים באמצע משפט
  // Pattern: מילה + רווח + מקף + רווח + מילה
  const gptDashPattern = /\S - \S/g;
  const gptDashMatches = text.match(gptDashPattern) || [];
  const gptDashCount = gptDashMatches.length;
  if (gptDashCount > 0) {
    // 🔥 עונש גבוה מאוד - כל מקף עם רווחים מעלה את הציון ב-5 נקודות (ללא הגבלה!)
    specialCharScore += gptDashCount * 5;
    findings.push({ type: 'מקפים GPT ( - )', count: gptDashCount });
  }
  
  // מרכאות מיוחדות (לא רגילות)
  const fancyQuotes = (text.match(/[""''«»„]/g) || []).length;
  if (fancyQuotes > 0) {
    specialCharScore += Math.min(fancyQuotes, 10);
    findings.push({ type: 'מרכאות מיוחדות', count: fancyQuotes });
  }
  
  // רווחים מיוחדים
  const specialSpaces = (text.match(/[ ​‌‍]/g) || []).length;
  if (specialSpaces > 0) {
    specialCharScore += Math.min(specialSpaces * 3, 12);
    findings.push({ type: 'רווחים מיוחדים', count: specialSpaces });
  }
  
  // Ellipsis character
  const ellipsisChar = (text.match(/…/g) || []).length;
  if (ellipsisChar > 0) {
    specialCharScore += ellipsisChar * 2;
    findings.push({ type: 'תו שלוש נקודות', count: ellipsisChar });
  }
  
  // Bullets
  const bullets = (text.match(/[•·]/g) || []).length;
  if (bullets > 3) {
    specialCharScore += Math.min(bullets, 8);
    findings.push({ type: 'נקודות תבליט', count: bullets });
  }
  
  // 🆕 שפות זרות (זיהוי AI חזק)
  // AI לפעמים "הוזה" תווים בערבית/רוסית/סינית
  const foreignChars = (text.match(/[\u0400-\u04FF\u4E00-\u9FFF\u0600-\u06FF]/g) || []).length;
  if (foreignChars > 0) {
      // עונש כבד על תווים זרים (זה סימן מובהק ל-AI או זבל)
      // כל תו מעלה את הציון ב-15 נקודות (לפי בקשת משתמש: "תוו בערבית מעלה ציון ב 15 נקודות")
      specialCharScore += foreignChars * 15; 
      findings.push({ type: 'תווים בשפה זרה', count: foreignChars });
  }
  
  return {
    specialCharScore,
    enDashCount,
    emDashCount,
    fancyQuotes,
    specialSpaces,
    findings,
    hasAICharacters: specialCharScore > 8,
    analysis: specialCharScore > 15 ? 'הרבה תווים מיוחדים - סימן AI!' :
              specialCharScore > 8 ? 'נמצאו תווים מפוארים' :
              specialCharScore > 3 ? 'מעט תווים מיוחדים' :
              'תווים רגילים'
  };
}

/**
 * 🔥 Excessive Quotes Analysis
 * AI משתמש במרכאות הרבה יותר מאנושיים
 */
function analyzeExcessiveQuotes(text) {
  const words = text.split(/\s+/).length;
  
  // ספירת כל סוגי המרכאות
  const allQuotes = text.match(/["״׳'"«»„""]/g) || [];
  const quoteCount = allQuotes.length;
  const quoteRatio = (quoteCount / 2) / words; // חלקי 2 כי כל מילה במרכאות = 2 מרכאות
  
  // ספירת מילים שAI אוהב לשים במרכאות
  let unnecessaryQuotes = 0;
  wordsAIQuotesUnnecessarily.forEach(word => {
    const patterns = [
      new RegExp(`["״]${word}["״]`, 'gi'),
      new RegExp(`["״]ה${word}["״]`, 'gi'),
    ];
    patterns.forEach(pattern => {
      const matches = text.match(pattern);
      if (matches) {
        unnecessaryQuotes += matches.length;
      }
    });
  });
  
  // מרכאות כפולות
  const doubleQuotes = (text.match(/""|\\"\\"|״״/g) || []).length;
  
  // חישוב ציון
  let quoteScore = 0;
  
  // יחס מרכאות גבוה
  if (quoteRatio > 0.08) quoteScore += 15;
  else if (quoteRatio > 0.05) quoteScore += 10;
  else if (quoteRatio > 0.03) quoteScore += 5;
  
  // מרכאות מיותרות
  if (unnecessaryQuotes > 5) quoteScore += 12;
  else if (unnecessaryQuotes > 2) quoteScore += 6;
  else if (unnecessaryQuotes > 0) quoteScore += 3;
  
  // מרכאות כפולות
  if (doubleQuotes > 0) quoteScore += doubleQuotes * 3;
  
  return {
    quoteScore,
    totalQuotes: quoteCount,
    quoteRatio: (quoteRatio * 100).toFixed(1) + '%',
    unnecessaryQuotes,
    doubleQuotes,
    isExcessiveQuotes: quoteScore > 10,
    analysis: quoteScore > 15 ? 'שימוש מוגזם במרכאות - סימן AI ברור!' :
              quoteScore > 8 ? 'יותר מדי מרכאות - חשוד' :
              quoteScore > 3 ? 'מעט מרכאות מיותרות' :
              'שימוש רגיל במרכאות'
  };
}

/**
 * 🔥 Connector Words Density
 * AI משתמש יותר מדי במילות חיבור "מושלמות"
 */
function analyzeConnectorDensity(text) {
  const words = text.split(/\s+/).length;
  
  // מחברים "מושלמים" שAI אוהב
  const perfectConnectors = [
    'בנוסף', 'כמו כן', 'יתר על כן', 'מעבר לכך', 'יתרה מזאת',
    'לעומת זאת', 'מאידך', 'מנגד', 'אולם', 'ברם',
    'לפיכך', 'משכך', 'אי לכך', 'בשל כך', 'כתוצאה מכך',
    'לסיכום', 'בסופו של דבר', 'בשורה התחתונה'
  ];
  
  // מחברים טבעיים שאנושיים משתמשים
  const naturalConnectors = [
    'אז', 'אבל', 'וגם', 'או', 'כי', 'בגלל', 'למה',
    'נו', 'טוב', 'בקיצור', 'סתם', 'ככה', 'פשוט'
  ];
  
  let perfectCount = 0;
  let naturalCount = 0;
  
  perfectConnectors.forEach(c => {
    const matches = (text.match(new RegExp(`\\b${c}\\b`, 'g')) || []).length;
    perfectCount += matches;
  });
  
  naturalConnectors.forEach(c => {
    const matches = (text.match(new RegExp(`\\b${c}\\b`, 'g')) || []).length;
    naturalCount += matches;
  });
  
  const perfectDensity = (perfectCount / words) * 100;
  const naturalDensity = (naturalCount / words) * 100;
  const ratio = naturalCount > 0 ? perfectCount / naturalCount : perfectCount;
  
  let connectorScore = 0;
  if (perfectDensity > 2) connectorScore += 15;
  else if (perfectDensity > 1) connectorScore += 8;
  
  if (ratio > 2) connectorScore += 10;
  else if (ratio > 1) connectorScore += 5;
  
  if (naturalDensity < 0.5 && perfectDensity > 0.5) connectorScore += 8;

  return {
    connectorScore,
    perfectConnectorCount: perfectCount,
    naturalConnectorCount: naturalCount,
    perfectDensity,
    naturalDensity,
    ratio,
    isOverlyFormal: connectorScore > 15,
    analysis: connectorScore > 20 ? 'שימוש מוגזם במחברים פורמליים - AI' :
              connectorScore > 10 ? 'מחברים פורמליים מעט גבוה' :
              naturalDensity > perfectDensity ? 'שפה טבעית - אנושי' :
              'מאוזן'
  };
}

/**
 * ניתוח Burstiness - מדד חשוב לזיהוי AI
 * AI נוטה לכתיבה "חלקה" יותר, בעוד אנושיים כותבים ב"פרצים"
 */
function analyzeBurstiness(text) {
  const sentences = text.split(/[.!?]\s+/).filter(s => s.trim().length > 0);
  if (sentences.length < 3) {
    return { burstinessScore: 0.5, isHumanLike: true };
  }

  const lengths = sentences.map(s => s.split(/\s+/).length);
  
  // חישוב הבדלים בין משפטים סמוכים
  const differences = [];
  for (let i = 1; i < lengths.length; i++) {
    differences.push(Math.abs(lengths[i] - lengths[i-1]));
  }
  
  // ממוצע ההבדלים
  const avgDiff = differences.reduce((a, b) => a + b, 0) / differences.length;
  
  // חישוב "פרצים" - קפיצות גדולות באורך
  const bursts = differences.filter(d => d > avgDiff * 1.5).length;
  const burstRatio = bursts / differences.length;
  
  // AI בדרך כלל יש burstiness נמוך (פחות מ-0.2)
  // אנושיים יש burstiness גבוה יותר (0.3-0.6)
    return {
    burstinessScore: burstRatio,
    avgDifference: avgDiff,
    burstCount: bursts,
    isHumanLike: burstRatio > 0.25,
    analysis: burstRatio < 0.15 ? 'אחידות חשודה - אופיינית ל-AI' :
              burstRatio > 0.4 ? 'שונות גבוהה - אופיינית לאנושי' :
              'שונות בינונית'
  };
}

/**
 * ניתוח סטטיסטי של סגנון הכתיבה - הועבר מחוץ לפונקציה אחרת!
 */
function analyzeStyleStatistics(text) {
  const paragraphs = text.split(/\n\s*\n|\r\n\s*\r\n/).filter(p => p.trim().length > 0);
  const sentences = text.split(/[.!?]\s+/).filter(s => s.trim().length > 0);
  const words = text.split(/\s+/).filter(w => w.trim().length > 0);
  
  if (words.length === 0) {
    return { averages: {}, standardDeviations: {}, entropy: {}, analysis: 'טקסט ריק' };
  }
  
  // מדדים בסיסיים
  const avgWordLength = words.reduce((sum, word) => sum + word.length, 0) / words.length;
  const avgSentenceLength = words.length / (sentences.length || 1);
  const avgParagraphLength = sentences.length / (paragraphs.length || 1);
  
  // חישוב התפלגות אורכי מילים
  const wordLengthDist = {};
  words.forEach(word => {
    const len = word.length;
    wordLengthDist[len] = (wordLengthDist[len] || 0) + 1;
  });
  
  // חישוב סטיות תקן
  const wordLengthVariance = words.reduce((sum, word) => 
    sum + Math.pow(word.length - avgWordLength, 2), 0) / words.length;
  const wordLengthStdDev = Math.sqrt(wordLengthVariance);
  
  const sentenceLengths = sentences.map(s => s.split(/\s+/).filter(Boolean).length);
  const sentenceLengthVariance = sentenceLengths.reduce((sum, len) => 
    sum + Math.pow(len - avgSentenceLength, 2), 0) / (sentenceLengths.length || 1);
  const sentenceLengthStdDev = Math.sqrt(sentenceLengthVariance);
  
  // מדד אנתרופיה - מגוון אורכי מילים
  let wordLengthEntropy = 0;
  for (const len in wordLengthDist) {
    const p = wordLengthDist[len] / words.length;
    wordLengthEntropy -= p * Math.log(p) / Math.log(2);
  }
  const maxPossibleEntropy = Math.log(Object.keys(wordLengthDist).length) / Math.log(2) || 1;
  const normalizedWordEntropy = wordLengthEntropy / maxPossibleEntropy;
  
  // ניתוח
  let analysis = "";
  if (sentenceLengthStdDev < 3) {
    analysis += "אחידות גבוהה מדי באורכי משפטים - אופיינית ל-AI. ";
  } else if (sentenceLengthStdDev > 8) {
    analysis += "שונות גבוהה באורכי משפטים - אופיינית לכתיבה אנושית. ";
  }
  
  if (normalizedWordEntropy < 0.7) {
    analysis += "גיוון נמוך באורכי מילים - יכול להעיד על AI. ";
  }
  
  if (avgParagraphLength > 5) {
    analysis += "פסקאות ארוכות - לפעמים אופייני ל-AI. ";
  }
  
  return {
    averages: {
      wordLength: parseFloat(avgWordLength.toFixed(2)),
      sentenceLength: parseFloat(avgSentenceLength.toFixed(2)),
      paragraphLength: parseFloat(avgParagraphLength.toFixed(2))
    },
    standardDeviations: {
      wordLength: parseFloat(wordLengthStdDev.toFixed(2)),
      sentenceLength: parseFloat(sentenceLengthStdDev.toFixed(2))
    },
    entropy: {
      wordLength: parseFloat(normalizedWordEntropy.toFixed(3))
    },
    analysis
  };
}

/**
 * מזהה כמה משפטים הם "פשוטים", "מחוברים" או "מורכבים"
 */
function analyzeSentenceComplexity(text) {
  const sentences = text.split(/[.!?]\s+/).filter(s => s.trim().length > 0);
  let simpleCount = 0;
  let compoundCount = 0;
  let complexCount = 0;

  const compoundWords = ['אך', 'אבל', 'ואולם', 'ומשום כך', 'ולכן', 'או', 'וגם'];
  const subordinators = ['ש', 'אשר', 'כי', 'כאשר', 'כש', 'אם', 'למרות ש', 'בגלל ש', 'מאחר ש', 'משום ש', 'כדי ש'];

  sentences.forEach(sentence => {
    const lower = sentence.toLowerCase();
    const hasCompound = compoundWords.some(w => lower.includes(` ${w} `) || lower.includes(` ${w},`));
    const hasComplex = subordinators.some(w => lower.includes(` ${w}`) || lower.startsWith(w + ' '));

    if (!hasCompound && !hasComplex) {
      simpleCount++;
    } else if (hasCompound && !hasComplex) {
      compoundCount++;
    } else {
      complexCount++;
    }
  });

  const total = simpleCount + compoundCount + complexCount || 1;
  return {
    simple: simpleCount,
    compound: compoundCount,
    complex: complexCount,
    complexRatio: parseFloat((complexCount / total).toFixed(2)),
    totalSentences: total
  };
}

/**
 * זיהוי משפטים בגוף פסיבי
 */
function analyzePassiveVoice(text) {
  const sentences = text.split(/[.!?]\s+/).filter(s => s.trim().length > 0);

  const passivePatterns = [
    /\bנכתב\b/, /\bנאמר\b/, /\bנבדק\b/, /\bנאסף\b/, /\bבוצע\b/,
    /\bנשלח\b/, /\bנתקבל\b/, /\bנחקר\b/, /\bנוסד\b/, /\bנחשב\b/,
    /\bנשמר\b/, /\bנעשה\b/, /\bהוחלט\b/, /\bהוסכם\b/, /\bהוקם\b/,
    /\bהוגדר\b/, /\bהוכרז\b/, /\bהופעל\b/, /\bנטען כי\b/,
    /\bמקובל לחשוב\b/, /\bמוסכם כי\b/, /\bיש להניח\b/,
    /\bיש להדגיש\b/, /\bראוי לציין\b/, /\bניתן לומר\b/,
    /\bניתן לראות\b/, /\bניתן להסיק\b/, /\bנדרש\b/,
    /נמצא כי/, /הובא לידיעתנו/, /התקבלה החלטה/,
    /נערכה בחינה/, /בוצע ניתוח/, /נלקח בחשבון/
  ];

  let passiveCount = 0;
  let passiveInstances = {};
  
  sentences.forEach(sentence => {
    for (let pattern of passivePatterns) {
      if (pattern.test(sentence)) {
        passiveCount++;
        const patternStr = pattern.source;
        passiveInstances[patternStr] = (passiveInstances[patternStr] || 0) + 1;
        break;
      }
    }
  });

  const total = sentences.length || 1;
  return {
    passiveCount,
    passiveInstances,
    totalSentences: total,
    passiveRatio: parseFloat((passiveCount / total).toFixed(2))
  };
}

/**
 * ניתוח מורפולוגי מורחב לעברית
 */
function analyzeAdvancedHebrewGrammar(text) {
  const words = text.split(/\s+/).map(w => w.trim()).filter(Boolean);
  
  const results = {
    definiteArticles: 0,
    firstPersonSingular: 0,
    secondPersonSingular: 0,
    thirdPersonSingular: 0,
    firstPersonPlural: 0,
    masculinePlural: 0,
    femininePlural: 0,
    constructForms: 0,
    prepositionPrefixes: 0
  };
  
  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    
    if (/^ה[\u0590-\u05FF]{2,}/.test(word)) {
      results.definiteArticles++;
    }
    
    if (/ים$/.test(word) && word.length > 3) {
      results.masculinePlural++;
    }
    if (/ות$/.test(word) && word.length > 3) {
      results.femininePlural++;
    }
    
    if (/י$/.test(word) && word.length > 2 && !hebrewStopWords.has(word)) {
      results.firstPersonSingular++;
    }
    if (/נו$/.test(word) && word.length > 3) {
      results.firstPersonPlural++;
    }
    
    if (/^[בלכמו][\u0590-\u05FF]{2,}/.test(word)) {
      results.prepositionPrefixes++;
    }
  }
  
  const totalWords = words.length || 1;
  results.definiteArticleRatio = results.definiteArticles / totalWords;
  results.possessiveSuffixRatio = (results.firstPersonSingular + results.firstPersonPlural) / totalWords;
  results.pluralRatio = (results.masculinePlural + results.femininePlural) / totalWords;
  
  let analysis = "";
  if (results.definiteArticleRatio < 0.03) {
    analysis += "שימוש נמוך בתווית היידוע - אופייני לכתיבת AI. ";
  }
  if (results.possessiveSuffixRatio < 0.01) {
    analysis += "כמעט ללא כינויי שייכות - כתיבה פחות אישית. ";
  }
  
  return { ...results, analysis };
}

/**
 * ניתוח קוהרנטיות סמנטית - תוקן! הוסר Math.random()
 */
function analyzeSemanticCoherence(text) {
  const paragraphs = text.split(/\n\s*\n|\r\n\s*\r\n/).filter(p => p.trim().length > 0);
  let forcedConnections = 0;
  let abruptTopicChanges = 0;
  
  const transitionWords = ['בכל מקרה', 'לסיכום', 'מצד שני', 'אף על פי כן', 'בניגוד לכך', 
                           'עם זאת', 'יחד עם זאת', 'לעומת זאת', 'מאידך'];

  // חילוץ מילות מפתח מכל פסקה (ללא מילות עצירה)
  const paragraphKeywords = paragraphs.map(p => {
    const words = p.match(/[\u0590-\u05FF]{3,}/g) || [];
    const filtered = words.filter(w => !hebrewStopWords.has(w));
    const freq = {};
    filtered.forEach(w => { freq[w] = (freq[w] || 0) + 1; });
    return Object.entries(freq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([word]) => word);
  });

  paragraphs.forEach((p, i) => {
    const firstSentence = p.split(/[.!?]/)[0]?.trim() || '';
    if (i > 0) {
      // בדיקת מילות חיבור מאולצות
      const hasTransition = transitionWords.some(w => firstSentence.includes(w));
      if (hasTransition) {
        forcedConnections++;
      }
      
      // בדיקת חפיפה בין פסקאות סמוכות - במקום random!
      if (paragraphKeywords[i-1] && paragraphKeywords[i]) {
        const prevKeywords = paragraphKeywords[i-1];
        const currKeywords = paragraphKeywords[i];
        const overlap = currKeywords.filter(w => prevKeywords.includes(w)).length;
        
        // אם אין כמעט חפיפה - זו קפיצה נושאית
        if (overlap === 0 && currKeywords.length > 0 && prevKeywords.length > 0) {
          abruptTopicChanges++;
        }
      }
    }
  });

  return {
    forcedConnections,
    abruptTopicChanges,
    paragraphCount: paragraphs.length,
    analysis: forcedConnections > 2 ? 'שימוש מוגזם במילות מעבר' :
              abruptTopicChanges > 2 ? 'קפיצות נושא תכופות' : 'קוהרנטיות סבירה'
  };
}

/**
 * ניתוח עקביות תוכן
 */
function analyzeContentConsistency(text) {
  const paragraphs = text.split(/\n\s*\n|\r\n\s*\r\n/).filter(p => p.trim().length > 0);
  
  if (paragraphs.length < 2) {
    return { logicalJumps: 0, topicConsistency: 1, analysis: "טקסט קצר מדי" };
  }
  
  const paragraphKeywords = paragraphs.map(p => {
    const words = p.match(/[\u0590-\u05FF]{3,}/g) || [];
    const filtered = words.filter(w => !hebrewStopWords.has(w));
    const freq = {};
    filtered.forEach(w => { freq[w] = (freq[w] || 0) + 1; });
    return Object.entries(freq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([word]) => word);
  });
  
  let consistencyScores = [];
  for (let i = 1; i < paragraphKeywords.length; i++) {
    const prevKeywords = paragraphKeywords[i-1];
    const currKeywords = paragraphKeywords[i];
    
    let overlapping = 0;
    currKeywords.forEach(word => {
      if (prevKeywords.includes(word)) overlapping++;
    });
    
    const overlapScore = overlapping / Math.max(currKeywords.length, 1);
    consistencyScores.push(overlapScore);
  }
  
  const avgConsistency = consistencyScores.length > 0 
    ? consistencyScores.reduce((sum, score) => sum + score, 0) / consistencyScores.length
    : 1;
  
  const logicalJumps = consistencyScores.filter(score => score < 0.1).length;
  
  return {
    logicalJumps,
    topicConsistency: parseFloat(avgConsistency.toFixed(2)),
    consistencyByParagraph: consistencyScores,
    analysis: avgConsistency < 0.2 ? "קפיצות תוכן משמעותיות" : "עקביות סבירה"
  };
}

/**
 * ניתוח רגשי מתקדם
 */
function analyzeAdvancedEmotionFlow(text) {
  const positiveWords = ['נפלא', 'נהדר', 'מלהיב', 'חיובי', 'מרגש', 'אדיר', 'מצוין', 
                         'מדהים', 'אהבתי', 'שמחתי', 'התרגשתי', 'כיף', 'משמח'];
  const negativeWords = ['איום', 'נורא', 'גרוע', 'שלילי', 'מתסכל', 'מרגיז', 
                         'מאכזב', 'עצוב', 'מבאס', 'נמאס', 'מעצבן', 'מטריד'];

  const tokens = text.split(/\s+/).filter(Boolean);

  let lastValence = 0;
  let emotionalShifts = 0;
  let positiveCount = 0;
  let negativeCount = 0;
  
  tokens.forEach((word) => {
    let currentValence = 0;
    if (positiveWords.some(p => word.includes(p))) {
      currentValence = 1;
      positiveCount++;
    }
    if (negativeWords.some(p => word.includes(p))) {
      currentValence = -1;
      negativeCount++;
    }
    if (currentValence !== 0 && lastValence !== 0 && currentValence !== lastValence) {
      emotionalShifts++;
    }
    if (currentValence !== 0) {
      lastValence = currentValence;
    }
  });

  // זיהוי אירוניה/הומור
  const ironyPatterns = ['איזה קטע', 'באירוניה', 'סרקזם', 'ברצינות?', 'כאילו', 
                         'לא באמת', 'ממש לא', 'בטח שכן', 'ברור לגמרי'];
  let ironyIndicators = ironyPatterns.filter(p => text.includes(p)).length;

  return {
    emotionalShifts,
    positiveCount,
    negativeCount,
    ironyIndicators,
    emotionalBalance: positiveCount - negativeCount,
    hasEmotionalVariety: emotionalShifts > 0 || (positiveCount > 0 && negativeCount > 0)
  };
}

/**
 * ניתוח היבטים תרבותיים ישראליים
 */
function analyzeCulturalReferences(text) {
  const localCultureWords = [
    // ביטויים יומיומיים
    "יהיה בסדר", "סמוך", "אחלה", "לא נורא", "יאללה", "מה הקטע", 
    "מת על זה", "סבבה", "מה נשמע", "תכלס", "אחי", "גבר", "מגניב",
    // מושגים ישראליים
    "מילואים", "על האש", "חומוס", "יום הזיכרון", "פסיכומטרי", "בגרויות",
    "גיוס", "שחרור", "טרמפ", "עולים חדשים", "טיול אחרי צבא",
    // תוכניות ומותגים
    "האח הגדול", "הישרדות", "ארץ נהדרת", "במבה", "ביסלי", "תנובה",
    // מקומות
    "תל אביב", "ירושלים", "כנרת", "ים המלח", "גוש דן", "הצפון",
    // מושגים עכשוויים
    "יוקר המחייה", "מדד", "התייקרויות", "קופת חולים"
  ];
  
  const hits = localCultureWords.filter(w => text.includes(w));
  return {
    culturalHits: hits,
    culturalCount: hits.length,
    hasCulturalContext: hits.length >= 2
  };
}

/**
 * ניתוח סלנג עכשווי
 */
function analyzeRecency(text) {
  const newSlang = [
    "קרינג'", "ליטרלי", "וויבס", "מוד", "טריגר", "גאסלייטינג", "פומו",
    "סליי", "פלופ", "אייקוני", "אקסטרה", "וואט דה פאק", "אומייגאד",
    "מטורף", "אש", "לייט", "רנדומלי", "בייסיק", "באסה רצח",
    "מת על זה", "קורע אותי", "מפוצץ", "רצח", "שובר את האינטרנט",
    "חפיף", "זורם", "פדיחה", "להתפוצץ", "לקרוע ת'צורה"
  ];
  
  const matches = newSlang.filter(s => text.includes(s));
  return {
    recencyHits: matches,
    recencyCount: matches.length,
    hasModernSlang: matches.length >= 1
  };
}

/**
 * בדיקת עקביות רעיונית
 */
function analyzeIdeaConsistency(text) {
  const favorMatches = (text.match(/\bבעד\b/g) || []).length;
  const againstMatches = (text.match(/\bנגד\b/g) || []).length;
  const contradictionScore = (favorMatches > 1 && againstMatches > 1) ? 5 : 0;

  return {
    favorMatches,
    againstMatches,
    contradictionScore,
    hasContradiction: contradictionScore > 0
  };
}

/**
 * ניתוח דקדוק עברי בסיסי
 */
function analyzeHebrewGrammarFeatures(text) {
  const words = text.split(/\s+/).map(w => w.trim());
  
  let definiteArticleCount = 0;
  let smichutCount = 0;

  for (let i = 0; i < words.length; i++) {
    const w = words[i];
    if (/^ה[א-ת]{2,}/.test(w)) {
      definiteArticleCount++;
    }
    if (w === 'של' && i > 0 && i < words.length - 1) {
      smichutCount++;
    }
  }

  return { definiteArticleCount, smichutCount };
}

// ----------------------------------------------------------------------------------------------
// פונקציית הניתוח המרכזית
// ----------------------------------------------------------------------------------------------

/**
 * 🕵️‍♂️ ניתוח תבניות עומק (Forensic Analysis)
 * בודק דפוסים מבניים, אינגלוזים, מבנה פסקאות ועוד
 */
/**
 * 👔 מילון הנמכת משלב (Formal to Casual)
 * AI משתמש במילים "גבוהות" מדי. אנחנו רוצים להוריד אותו לקרקע.
 */
const formalToCasualMap = {
  'כיצד': 'איך',
  'מדוע': 'למה',
  'הינו': 'הוא',
  'הינה': 'היא',
  'הינם': 'הם',
  'הינן': 'הן',
  'אנו': 'אנחנו',
  'לבצע': 'לעשות',
  'ביצוע': 'עשייה',
  'לרכוש': 'לקנות',
  'רכישה': 'קנייה',
  'להעניק': 'לתת',
  'הענקה': 'נתינה',
  'לספק': 'לתת',
  'אספקה': 'נתינה',
  'להוות': 'להיות',
  'מהווה': 'הוא',
  'מהווים': 'הם',
  'בטרם': 'לפני',
  'טרם': 'עוד לא',
  'עקב': 'בגלל',
  'בגין': 'בגלל',
  'אודות': 'על',
  'באמצעות': 'בעזרת',
  'על מנת': 'כדי',
  'במטרה': 'כדי',
  'לשם': 'כדי',
  'ברם': 'אבל',
  'אולם': 'אבל',
  'אף על פי ש': 'למרות ש',
  'כאשר': 'כש',
  'היות ו': 'בגלל ש',
  'מכיוון ש': 'בגלל ש',
  'אי לכך': 'בגלל זה',
  'לפיכך': 'לכן',
  'משום ש': 'בגלל ש',
  'חש': 'מרגיש',
  'סבור': 'חושב',
  'גורס': 'טוען',
  'מצוי': 'נמצא',
  'קיים': 'יש',
  'מתבצע': 'קורה',
  'מתרחש': 'קורה',
  'להשיג': 'להשיג', // לפעמים AI משתמש ב"להשיג" במקום "לקבל"
  'להסיק': 'להבין',
  'להיווכח': 'לראות',
  'שרוי': 'נמצא',
  'מסוגל': 'יכול',
  'מעוניין': 'רוצה',
  'חפץ': 'רוצה'
};

/**
 * 🤖 Claude Fingerprints - טיקים ספציפיים של קלוד בעברית
 * קלוד אוהב להיות "פיוטי", "מאזן" ו"מזמין למסע"
 */
const claudeFingerprints = [
  // הזמנה למסע
  'בואו נצא למסע', 'בואו נצלול', 'נצא למסע מרתק', 'יחד נגלה',
  'במאמר זה נחקור', 'במדריך זה נכסה', 'בשורות הבאות',
  
  // פיוטיות יתר
  'האומנות שב', 'בליבת העשייה', 'מעבר לאופק', 'שוזר בתוכו',
  'מרקם עדין', 'סימפוניה של', 'ריקוד עדין', 'הוליסטי',
  'רב-ממדי', 'פורץ דרך', 'מהפכני', 'עידן חדש',
  
  // איזון מעיק
  'לכל מטבע שני צדדים', 'חשוב לראות את התמונה המלאה',
  'ראוי לגשת לנושא', 'בשקלול כל הגורמים', 'מצד אחד... ומצד שני',
  
  // סיום חינוכי
  'בסיכומו של מסע', 'לסיכום הדברים', 'המסר העיקרי הוא',
  'קחו את הזמן', 'זכרו תמיד', 'אל תשכחו ש'
];

/**
 * 🆕 כפילויות לשוניות (Tautologies) ש-AI אוהב
 * מפתח: הביטוי הכפול, ערך: התיקון
 */
const tautologiesMap = {
  'לעלות למעלה': 'לעלות',
  'לרדת למטה': 'לרדת',
  'לצאת החוצה': 'לצאת',
  'להיכנס פנימה': 'להיכנס',
  'לחזור שוב': 'לחזור',
  'לחזור חזרה': 'לחזור',
  'רוב רובו': 'רובו',
  'כמו למשל': 'למשל',
  'במידה ואם': 'אם',
  'הדדיים אחד לשני': 'הדדיים',
  'יחד ביחד': 'יחד',
  'בסופו של דבר': 'בסוף',
  'ארכיון היסטורי': 'ארכיון',
  'הפתעה לא צפויה': 'הפתעה',
  'מתנה חינם': 'מתנה',
  'תכניות לעתיד': 'תכניות'
};

/**
 * 🆕 מילות קישור כפולות (Double Connectors)
 * AI נוטה לתרגם However/Although בצורה מסורבלת
 */
const doubleConnectorsMap = {
  'אולם יחד עם זאת': 'עם זאת',
  'אך למרות זאת': 'למרות זאת',
  'אבל יחד עם זאת': 'אבל',
  'אולם למרות זאת': 'אולם',
  'בנוסף לכך גם': 'בנוסף',
  'כמו כן גם': 'כמו כן',
  'אף על פי כן ולמרות זאת': 'למרות זאת'
};

/**
 * 🆕 משפטי מעבר רובוטיים (Robotic Transitions)
 * AI מסביר מה הוא הולך לעשות במקום פשוט לעשות את זה
 */
const roboticTransitions = [
  'כעת נעבור ל', 'בואו נצלול ל', 'כפי שראינו קודם',
  'בפסקה הבאה', 'בחלק הבא', 'חשוב להבין קודם',
  'לאחר שהבנו את', 'כעת נבחן את', 'במאמר זה נסקור',
  'נסכם ונאמר', 'מן הראוי לציין', 'כדלקמן'
];

/**
 * 🆕 ביטויים אקדמיים גנריים (Academic Fillers)
 * רשימה מורחבת של "פילרים" ש-AI משתמש בהם כדי להישמע חכם
 */
const aiPhrases = [
  'חשוב לציין', 'ראוי לציין', 'יש לזכור', 'כדאי לדעת', 'ניתן לומר',
  'באופן כללי', 'בדרך כלל', 'ברוב המקרים', 'על פי רוב',
  'בסופו של דבר', 'בסופו של יום', 'בשורה התחתונה',
  'בנוסף לכך', 'יתרה מכך', 'כמו כן', 'במקביל לכך',
  'לאור זאת', 'בהתאם לכך', 'כתוצאה מכך', 'עקב כך',
  'משמעות הדבר', 'כלומר', 'דהיינו', 'רוצה לומר',
  'במידה רבה', 'במידה מסוימת', 'באופן משמעותי',
  'היבט נוסף', 'נקודה נוספת', 'פן נוסף', 'נדבך נוסף',
  'מחד גיסא', 'מאידך גיסא', 'אי לכך ובהתאם לזאת',
  'הלכה למעשה', 'בפועל', 'ברמה הפרקטית',
  'ראייה הוליסטית', 'תמונה רחבה', 'מבט על',
  'שילוב מנצח', 'פתרון אולטימטיבי', 'חווית משתמש',
  'עידן חדש', 'פורץ דרך', 'חסר תקדים', 'אבן דרך'
];

/**
 * 👔 זיהוי שפה רשמית מדי (High Register Analysis)
 */
function analyzeFormalLanguage(text) {
  let formalCount = 0;
  const foundTerms = [];
  
  Object.keys(formalToCasualMap).forEach(term => {
    // מחפש מילה שלמה בלבד
    const regex = new RegExp(`\\s${term}\\s`, 'g');
    const matches = text.match(regex);
    if (matches) {
      formalCount += matches.length;
      if (foundTerms.length < 10) foundTerms.push(term); // שומר דוגמאות
    }
  });
  
  return {
    scorePenalty: formalCount * 2, // כל מילה גבוהה מעלה את ציון ה-AI
    formalCount,
    isFormal: formalCount > 5,
    details: foundTerms
  };
}

/**
 * 🏗️ ניתוח מבנה וטון (Structure & Tone Analysis)
 * מזהה דפוסים דידקטיים, סיומות צפויות והיעדר אישיות
 */
function analyzeStructureAndTone(text) {
  let scorePenalty = 0;
  const signals = [];

  // 1. אובססיית הסיכום (Conclusion Fetish)
  // בודק אם 10% האחרונים של הטקסט מכילים מילות סיכום מובהקות
  const last10Percent = text.substring(text.length - Math.min(text.length * 0.2, 500));
  const conclusionPatterns = ['לסיכום', 'סיכומו של דבר', 'בסיכום', 'לסיום', 'כסיכום', 'השורה התחתונה'];
  let hasConclusion = false;
  conclusionPatterns.forEach(p => {
    if (last10Percent.includes(p)) {
      hasConclusion = true;
    }
  });
  
  if (hasConclusion) {
    scorePenalty += 8;
    signals.push('סיום גנרי ("לסיכום")');
  }

  // 2. תבנית שאלה-תשובה דידקטית (Didactic Q&A)
  // "למה זה קורה? כי...", "מדוע? מכיוון ש..."
  const didacticRegex = /(\?)\s+(כי|מכיוון ש|בגלל ש|הסיבה היא|באמצעות|על ידי)/g;
  const didacticMatches = text.match(didacticRegex);
  if (didacticMatches && didacticMatches.length > 0) {
    scorePenalty += (didacticMatches.length * 5);
    signals.push('שאלות רטוריות דידקטיות (' + didacticMatches.length + ')');
  }

  // 3. היעדר "אני" (Impersonal Vacuum)
  // אם הטקסט ארוך (מעל 1000 תווים) ואין שום אזכור אישי
  const personalPronouns = ['אני', 'שלי', 'לדעתי', 'בעיני', 'מניסיוני', 'אצלנו', 'אנחנו'];
  let hasPersonal = false;
  personalPronouns.forEach(p => {
    if (text.includes(' ' + p + ' ')) hasPersonal = true;
  });

  if (text.length > 1000 && !hasPersonal) {
    scorePenalty += 10;
    signals.push('היעדר מוחלט של גוף ראשון (Impersonal)');
  }

  return {
    scorePenalty,
    signals,
    hasConclusion,
    isDidactic: (didacticMatches?.length || 0) > 0,
    isImpersonal: !hasPersonal && text.length > 1000
  };
}

/**
 * 🏆 זיהוי הגזמות וסופרלטיבים
 */
function analyzeSuperlatives(text) {
  let superlativeCount = 0;
  const foundSuperlatives = [];
  
  Object.keys(superlativesMap).forEach(function(sup) {
    if (text.indexOf(sup) > -1) {
      superlativeCount++;
      foundSuperlatives.push(sup);
    }
  });
  
  // בדיקת "ביותר" (AI אוהב "החשוב ביותר", "המהיר ביותר")
  const biyoterCount = (text.match(/\sביותר\s/g) || []).length;
  
  return {
    scorePenalty: (superlativeCount * 4) + (biyoterCount * 2),
    isExaggerated: superlativeCount > 3 || biyoterCount > 4,
    details: foundSuperlatives
  };
}

/**
 * 💧 "צייד המים" (Watermark Hunter)
 * מזהה תווים נסתרים, סימני כיוון ושאריות העתקה מ-AI
 */
/**
 * 🆕 סופרלטיבים מוגזמים (Superlatives)
 * AI נוטה להגזים בתיאורים ("הכי טוב בעולם")
 */
const superlativesMap = {
  'חסר תקדים': 'מרשים',
  'פורץ דרך': 'חדשני',
  'מהפכני': 'מתקדם',
  'יוצא דופן': 'מיוחד',
  'בלתי רגיל': 'טוב',
  'אולטימטיבי': 'מקיף',
  'מושלם': 'מצוין',
  'אידיאלי': 'מתאים מאוד',
  'הטוב ביותר': 'מעולה',
  'אבסולוטי': 'מוחלט',
  'טוטאלי': 'מלא',
  'קריטי': 'חשוב',
  'חיוני': 'חשוב',
  'הכרחי': 'צריך',
  'בלתי נפרד': 'חלק',
  'אין ספק': 'ברור',
  'ללא עוררין': 'בטוח'
};

/**
 * 🕵️‍♂️ זיהוי ספציפי של Claude
 * מחפש ביטויים פיוטיים, מבני "מסע" ואיזון יתר
 */
function analyzeClaudeSpecifics(text) {
  let claudeScore = 0;
  const foundFingerprints = [];
  
  claudeFingerprints.forEach(function(fp) {
    if (text.indexOf(fp) > -1) {
      claudeScore += 5; // עונש גבוה לכל טיק של קלוד
      foundFingerprints.push(fp);
    }
  });
  
  // בדיקת "איזון יתר" (יתרונות מול חסרונות בצמידות)
  const prosConsPattern = /(יתרונות|חסרונות|בעד|נגד).{1,50}(יתרונות|חסרונות|בעד|נגד)/g;
  if (prosConsPattern.test(text)) {
    claudeScore += 10;
    foundFingerprints.push('מבנה יתרונות-חסרונות צמוד (איזון יתר)');
  }

  return {
    isClaude: claudeScore > 15,
    scorePenalty: claudeScore,
    fingerprints: foundFingerprints
  };
}

/**
 * 🤖 ניתוח תחביר רובוטי (Robotic Syntax)
 * מזהה כפילויות, קישורים כפולים ומעברים מלאכותיים
 */
function analyzeRoboticSyntax(text) {
  let scorePenalty = 0;
  const foundIssues = [];
  
  // 1. בדיקת כפילויות
  let tautologyCount = 0;
  Object.keys(tautologiesMap).forEach(function(t) {
    if (text.indexOf(t) > -1) {
      tautologyCount++;
      foundIssues.push(t);
    }
  });
  
  // 2. בדיקת קישורים כפולים
  let doubleConnectorCount = 0;
  Object.keys(doubleConnectorsMap).forEach(function(dc) {
    if (text.indexOf(dc) > -1) {
      doubleConnectorCount++;
      foundIssues.push(dc);
    }
  });
  
  // 3. בדיקת מעברים רובוטיים
  let roboticTransCount = 0;
  roboticTransitions.forEach(function(rt) {
    if (text.indexOf(rt) > -1) {
      roboticTransCount++;
      foundIssues.push(rt);
    }
  });
  
  if (tautologyCount > 0) scorePenalty += tautologyCount * 3;
  if (doubleConnectorCount > 0) scorePenalty += doubleConnectorCount * 5;
  if (roboticTransCount > 0) scorePenalty += roboticTransCount * 6;
  
  return {
    scorePenalty: scorePenalty,
    hasRoboticSyntax: scorePenalty > 10,
    issues: foundIssues,
    counts: {
      tautologies: tautologyCount,
      doubleConnectors: doubleConnectorCount,
      roboticTransitions: roboticTransCount
    }
  };
}

function analyzeWatermarks(text) {
  // רשימת תווים חשודים:
  // \u200B-\u200D: Zero Width Spaces/Joiners
  // \u200E-\u200F: Directional Marks (LRM/RLM)
  // \uFEFF: Byte Order Mark
  // \u00A0: Non-breaking space (חשוד אם מופיע באמצע משפט רגיל)
  // \u202F: Narrow No-Break Space
  // \uE000-\uF8FF: Private Use Area (לעיתים משמש להסתרת מידע)
  const suspiciousPattern = /[\u200B\u200C\u200D\u200E\u200F\uFEFF\u00A0\u202F\uE000-\uF8FF]/g;
  
  const matches = text.match(suspiciousPattern) || [];
  const uniqueChars = new Set(matches);
  
  // ניתוח המיקום (למשל: רווח קשיח שאינו אחרי מספר)
  // אבל לצורך הפשטות והמהירות - עצם קיומם בטקסט גולמי הוא חשוד
  
  return {
    hasWatermarks: matches.length > 0,
    watermarkCount: matches.length,
    uniqueWatermarks: uniqueChars.size,
    scorePenalty: matches.length * 8, // עונש כבד: 8 נקודות לכל תו נסתר
    details: Array.from(uniqueChars).map(c => 'U+' + c.charCodeAt(0).toString(16).toUpperCase())
  };
}

/**
 * 🕵️‍♂️ מדד האנטרופיה ונדירות מילים (Rare Word Density)
 * בודק אם יש מילים נדירות בטקסט או רק מילים גנריות
 */
function analyzeWordEntropy(text) {
  const words = text.split(/\s+/);
  let rareWordCount = 0;
  const commonWordSet = new Set(Object.keys(hebrewWordFrequency));
  
  words.forEach(word => {
    const cleanWord = word.replace(/[.,!?;:]/g, '');
    // מילה נדירה = לא במילון הנפוצות וגם לא ב-Stop Words וארוכה מ-3 אותיות
    if (!commonWordSet.has(cleanWord) && 
        !hebrewStopWords.has(cleanWord) && 
        cleanWord.length > 3) {
      rareWordCount++;
    }
  });
  
  const rareRatio = rareWordCount / (words.length || 1);
  
  return {
    rareRatio: rareRatio,
    isTooGeneric: rareRatio < 0.15, // פחות מ-15% מילים ייחודיות = חשוד כ-AI גנרי
    rareCount: rareWordCount
  };
}

function analyzeDeepPatterns(text) {
  const result = {
    signals: [],
    scorePenalty: 0,
    details: {}
  };

  // 1. בדיקת "אינגלוזים" (תרגום מכונה)
  let anglicismCount = 0;
  const foundAnglicisms = [];
  Object.keys(anglicismsMap).forEach(function(term) {
    if (text.indexOf(term) > -1) {
      anglicismCount++;
      foundAnglicisms.push(term);
    }
  });
  
  if (anglicismCount > 1) {
    result.signals.push('שימוש בביטויי תרגום ("אינגלוז")');
    result.scorePenalty += anglicismCount * 4;
    result.details.anglicisms = foundAnglicisms;
  }

  // 2. בדיקת "איזון רעיל" (Hedging)
  const hedgingHits = hedgingWords.filter(function(w) { return text.indexOf(w) > -1; });
  const hedgingRatio = hedgingHits.length / (text.split(/\s+/).length || 1);
  
  if (hedgingRatio > 0.015) { // מעל 1.5% מהטקסט
    result.signals.push('שימוש מוגזם במילים מסייגות (פחד להתחייב)');
    result.scorePenalty += 15;
    result.details.hedging = hedgingHits;
  }

  // 3. מבחן ה-"של" מול סמיכות
  const shelCount = (text.match(/\sשל\s/g) || []).length;
  const wordCount = text.split(/\s+/).length;
  const shelRatio = shelCount / (wordCount || 1);
  
  // עברית טבעית משתמשת בסמיכות. AI משתמש ב"של" המון.
  if (shelRatio > 0.045) { // מעל 4.5% מהמילים הן "של"
    result.signals.push('שימוש מוגזם במילת היחס "של" (חוסר בסמיכות)');
    result.scorePenalty += 12;
    result.details.shelRatio = shelRatio;
  }

  // 4. תבנית "בולד + נקודתיים" (The Listicle Pattern)
  // מחפש דפוס כמו: "יתרון: הטקסט..." או "מהירות: המערכת..."
  // זה עובד גם על טקסט נקי כי הניקוי משאיר את הנקודתיים
  const listiclePattern = /^\s*[\wא-ת\s]{1,20}:/gm;
  const listicleMatches = text.match(listiclePattern) || [];
  
  if (listicleMatches.length > 3) {
    result.signals.push('תבנית רשימה רובוטית (מילה + נקודתיים)');
    result.scorePenalty += listicleMatches.length * 5;
    result.details.listicleMatches = listicleMatches;
  }

  // 5. פעלים סבילים (Passive Voice)
  const passiveHits = passiveMarkers.filter(function(w) { return text.indexOf(w) > -1; });
  if (passiveHits.length > 2) {
    result.signals.push('ריבוי פעלים סבילים (כתיבה מרוחקת)');
    result.scorePenalty += passiveHits.length * 3;
    result.details.passiveHits = passiveHits;
  }

  return result;
}

function analyzeText(text) {
  const results = {};
  
  // שמירת הטקסט לחישובים מאוחרים
  results.textLength = text.length;
  results.wordCount = text.split(/\s+/).filter(Boolean).length;

  // ============================================================================================
  // 1. ביטויים גנריים
  // ============================================================================================

  const genericPhrases = [
    "לסיכום", "ניתן לומר כי", "באופן כללי", "בהתאם לכך", "במאמר זה",
    "לאור זאת", "בפתח הדברים", "חשוב להדגיש כי", "כפי שניתן לראות",
    "מכאן עולה כי", "בחינה מעמיקה מראה", "לא ניתן להתעלם מהעובדה ש",
    "בהקשר זה ראוי לציין", "נקודה חשובה נוספת היא", "מוסכם על הכל כי",
    "הדעה הרווחת היא", "מקובל לחשוב ש", "אין ספק כי", "ברור לחלוטין ש",
    "מחקרים מראים כי", "הספרות המקצועית מצביעה על", "ההשערה המרכזית היא",
    "יתרון תחרותי משמעותי", "ערך מוסף", "פתרון אופטימלי", "חדשנות פורצת דרך"
];
  results.phraseHits = genericPhrases.filter(p => text.includes(p));
  results.phraseScore = results.phraseHits.length * 8;

  // ============================================================================================
  // 2. ניתוח משפטים
  // ============================================================================================

  const sentences = text.split(/[.!?]\s+/).filter(s => s.trim().length > 0);
  const sentenceLengths = sentences.map(s => s.split(/\s+/).length);
  results.avgLength = sentenceLengths.reduce((a, b) => a + b, 0) / (sentenceLengths.length || 1);
  const variance = sentenceLengths.reduce((sum, len) => sum + Math.pow(len - results.avgLength, 2), 0) / (sentenceLengths.length || 1);
  results.stdDev = Math.sqrt(variance) || 0;

  results.uniformityPenalty = 0;
  if (results.stdDev < 4 && results.avgLength > 10) results.uniformityPenalty += 18;
  else if (results.stdDev < 6) results.uniformityPenalty += 10;

  // ============================================================================================
  // 3. פתיחות משפט חוזרות
  // ============================================================================================

  const starts = sentences.map(s => s.trim().split(/\s+/)[0]?.toLowerCase()).filter(Boolean);
  const startCounts = {};
  starts.forEach(word => {
    if (word && !hebrewStopWords.has(word)) {
      startCounts[word] = (startCounts[word] || 0) + 1;
    }
  });
  results.repeatedStarts = Object.entries(startCounts)
    .filter(([_, count]) => count > 2)
    .map(([word]) => word);
  results.repetitionPenalty = results.repeatedStarts.length * 6;

  // ============================================================================================
  // 4. מילים שיווקיות
  // ============================================================================================

  const marketingWords = ["הטוב ביותר", "מחיר משתלם", "לא תאמינו", "המדריך השלם", 
                          "שירות יוצא דופן", "הזדמנות שלא תחזור", "פתרון מושלם"];
  results.marketingHits = marketingWords.filter(p => text.includes(p));
  results.marketingScore = results.marketingHits.length * 8;

  // ============================================================================================
  // 5. סמנים אנושיים
  // ============================================================================================

  const humanMarkers = [
    "אני חושב", "נראה לי", "קרה לי פעם", "לדעתי", "מניסיוני",
    "הרגשתי ש", "אני מאמין", "כשהייתי", "אני ממש", "התבאסתי",
    "נמאס לי", "אני לא מבין למה", "פעם חשבתי", "גיליתי ש", "טעיתי",
    "זה פשוט מעצבן", "איזה באסה", "ממש כיף", "מרגיז אותי",
    "אין מצב ש", "וואלה", "סתם", "חבל על הזמן", "אחלה", "סבבה",
    "יאללה", "וואי", "אוף", "חפרתי?", "סורי", "אופסי",
    "רגע, בעצם", "אולי בעצם", "אני לא בטוח", "קשה לדעת",
    "בקיצור", "אז כאילו", "חחח", "לול", "טוב נו",
    "אתם יודעים ש", "נזכרתי עכשיו", "אל תצחקו, אבל"
  ];
  results.humanMarkerHits = humanMarkers.filter(p => text.includes(p));
  results.hasHumanTouch = results.humanMarkerHits.length > 0;
  results.humanBonus = results.humanMarkerHits.length > 0 ? -15 - (results.humanMarkerHits.length * 3) : 12;

  // ============================================================================================
  // 6. ביטויי AI (Claude/GPT)
  // ============================================================================================

  const claudeStyleMarkers = [
    "כמובן", "בהחלט", "אשמח לעזור", "נראה כי", "כדאי לזכור ש",
    "חשוב לציין ש", "מנקודת מבט", "אם אוכל לסייע", "כחלק מהתהליך",
    "מעניין לציין כי", "חשוב להבין ש", "יש לזכור כי", "יש לקחת בחשבון",
    "אפשר לומר ש", "חשוב להדגיש", "ראוי להזכיר ש", "ברצוני להבהיר",
    "בהינתן המידע", "ראשית", "לסיכום", "בתשובה לשאלתך",
    "אני מקווה שזה עונה", "אשמח לעזור בכל שאלה"
  ];
  results.claudeHits = claudeStyleMarkers.filter(p => text.includes(p));
  results.claudeScore = results.claudeHits.length * 10;

  // ============================================================================================
  // 6.5 מקפים עם רווחים באמצע משפט - סימן מובהק ל-GPT! 🆕
  // ============================================================================================
  // GPT אוהב להשתמש במקפים עם רווחים " - " במקום פסיקים או סוגריים
  // דוגמה: "הפתרון - שהוא יעיל מאוד - עובד" במקום "הפתרון (שהוא יעיל מאוד) עובד"
  // 🔥 חשוב: לא לספור מקפים בתחילת שורה (bullet points) - אלה לגיטימיים!
  // Bullet point = שורה שמתחילה ברווחים אופציונליים ואז מקף (– או -)
  // GPT dash = מילה + רווח + מקף + רווח + מילה (באמצע משפט)
  // 🔥 חשוב: לא לספור bullet points!
  
  // מוצאים את כל המקפים עם רווחים
  const allDashMatches = text.match(/\S - \S/g) || [];
  
  // מסננים bullet points - מקפים שמופיעים בתחילת שורה
  // Bullet point: שורה חדשה (או תחילת טקסט) + רווחים אופציונליים + מקף + רווח
  const bulletPointPattern = /(?:^|\n)\s*[-–—]\s/g;
  const bulletPoints = text.match(bulletPointPattern) || [];
  
  // GPT dashes = כל המקפים פחות ה-bullet points
  const dashWithSpacesCount = Math.max(0, allDashMatches.length - bulletPoints.length);
  results.gptDashCount = dashWithSpacesCount;
  results.bulletPointCount = bulletPoints.length; // לדיבאג
  // 🔥 עונש גבוה על מקפים GPT - כל מקף מעלה ב-5 נקודות (ללא הגבלה!)
  results.gptDashScore = dashWithSpacesCount * 5;

  // ============================================================================================
  // 7. יחס שאלות
  // ============================================================================================

  const questionSentences = sentences.filter(s => s.trim().endsWith('?'));
  results.questionRatio = questionSentences.length / (sentences.length || 1);
  results.questionPenalty = results.questionRatio > 0.2 ? 10 : 0;

  // ============================================================================================
  // 8. עושר לשוני
  // ============================================================================================

  const words = text.toLowerCase().match(/[\p{L}]{3,}/gu) || [];
  const uniqueWords = new Set(words);
  results.lexicalRichness = parseFloat((uniqueWords.size / (words.length || 1)).toFixed(2));
  results.lexicalPenalty = results.lexicalRichness < 0.25 ? 10 : 0;

  // ============================================================================================
  // 9. מילות קישור
  // ============================================================================================

  const linkingWords = [
    "כמו כן", "בנוסף לכך", "מעבר לכך", "יחד עם זאת", "לאור זאת", "יתר על כן",
    "אולם", "ברם", "לעומת זאת", "מאידך גיסא", "אף על פי כן",
    "משום ש", "מפני ש", "כיוון ש", "לפיכך", "משום כך", "כתוצאה מכך",
    "תחילה", "לאחר מכן", "בהמשך", "לבסוף", "כדי", "על מנת",
    "לדוגמה", "למשל", "כגון", "להמחשה"
];
  results.linkingHits = linkingWords.filter(p => text.includes(p));
  results.linkingScore = Math.min(results.linkingHits.length * 4, 25);

  // ============================================================================================
  // 10. טון ועקביות
  // ============================================================================================

  const formalToneMarkers = ["אי לכך", "יש לציין כי", "ניתן להסיק", "מן הראוי", "יתרה מזאת"];
  const informalToneMarkers = ["מגניב", "וואלה", "אחלה", "סבבה", "תכלס", "יאללה", "חבל על הזמן"];
  results.formalHits = formalToneMarkers.filter(p => text.includes(p)).length;
  results.informalHits = informalToneMarkers.filter(p => text.includes(p)).length;
  // שילוב של פורמלי ולא פורמלי = יותר אנושי
  results.toneConsistencyScore = (results.formalHits > 0 && results.informalHits > 0) ? -12 : 
                                  (results.informalHits > 0 ? -8 : 6);

  // ============================================================================================
  // 11. סלנג ורגשות
  // ============================================================================================

  const slangExpressions = ["על הפנים", "חבל על הזמן", "לא עושים חשבון", "איזה קטע", "פדיחה", "חפרתי"];
  results.slangHits = slangExpressions.filter(p => text.includes(p));
  results.slangBonus = results.slangHits.length > 0 ? -12 : 5;

  const positiveEmotions = ["שמח", "מרגש", "אוהב", "מצוין", "מדהים", "נפלא"];
  const negativeEmotions = ["מעצבן", "מאכזב", "כועס", "עצוב", "מתסכל", "נוראי"];
  results.positiveHits = positiveEmotions.filter(p => text.includes(p)).length;
  results.negativeHits = negativeEmotions.filter(p => text.includes(p)).length;
  results.emotionMixScore = (results.positiveHits > 0 && results.negativeHits > 0) ? -10 : 5;

  // ============================================================================================
  // 12. מבנה פסקאות
  // ============================================================================================

  const paragraphs = text.split(/\n\s*\n|\r\n\s*\r\n/).filter(p => p.trim().length > 0);
  if (paragraphs.length > 1) {
    const paragraphLengths = paragraphs.map(p => p.split(/\s+/).length);
    const avgParagraphLength = paragraphLengths.reduce((a, b) => a + b, 0) / paragraphLengths.length;
    const paragraphVariance = paragraphLengths.reduce((sum, len) => sum + Math.pow(len - avgParagraphLength, 2), 0) / paragraphLengths.length;
    const paragraphStdDev = Math.sqrt(paragraphVariance);
    results.paragraphUniformityScore = paragraphStdDev < 10 ? 10 : 0;
  } else {
    results.paragraphUniformityScore = 0;
  }

  // ============================================================================================
  // 13. מילות הסתייגות
  // ============================================================================================

  const hedgingWords = [
    "ייתכן", "אולי", "ככל הנראה", "אפשר ש", "סביר להניח", "בדרך כלל",
    "לעתים", "לפעמים", "לא בהכרח", "במקרים מסוימים", "באופן עקרוני",
    "בהנחה ש", "למיטב הערכתי", "במידה מסוימת", "בקירוב", "כמעט",
    "לכאורה", "על פניו", "לא ברור אם", "נתון לפרשנות"
];
  results.hedgingHits = hedgingWords.filter(p => text.includes(p));
  results.hedgingScore = results.hedgingHits.length > 4 ? 12 : (results.hedgingHits.length > 2 ? 6 : 0);

  // ============================================================================================
  // 14. הפניות עצמיות ודוגמאות
  // ============================================================================================

  const selfReferences = ["כפי שציינתי", "כמו שהסברתי", "כמו שאמרתי", "כפי שהזכרתי"];
  results.selfReferenceHits = selfReferences.filter(p => text.includes(p));
  results.selfReferenceScore = results.selfReferenceHits.length > 1 ? 8 : 0;

  const genericExampleMarkers = ["לדוגמה", "למשל", "להמחשה"];
  const specificExampleMarkers = ["קרה לי ש", "כאשר הייתי", "במקרה ש", "בשנת", "חוויתי"];
  results.genericExampleHits = genericExampleMarkers.filter(p => text.includes(p)).length;
  results.specificExampleHits = specificExampleMarkers.filter(p => text.includes(p)).length;
  results.exampleScore = results.specificExampleHits > 0 ? -12 : (results.genericExampleHits > 0 ? 5 : 0);

  // ============================================================================================
  // 15. מונחים טרנדיים ושגיאות
  // ============================================================================================

  const trendyTerms = ["ויראלי", "קרינג'", "פייק ניוז", "קנסלינג", "גאסלייטינג", "פומו", "פלופ"];
  results.trendyHits = trendyTerms.filter(p => text.includes(p));
  results.trendyScore = results.trendyHits.length > 0 ? -12 : 0;

  const commonMistakes = ["אין לי מושג", "יכול להיות ש", "נו באמת", "כאילו", "מה זה"];
  results.mistakeHits = commonMistakes.filter(p => text.includes(p));
  results.mistakeScore = results.mistakeHits.length > 0 ? -10 : 3;

  // ============================================================================================
  // 16. ניתוחים מתקדמים PRO
  // ============================================================================================

  // 🔥 Deep Patterns (Forensic) - חדש V4!
  const deepPatterns = analyzeDeepPatterns(text);
  results.deepSignals = deepPatterns.signals;
  results.deepScorePenalty = deepPatterns.scorePenalty;
  results.deepDetails = deepPatterns.details;

  // 🔥 Entropy & Fluff - חדש V5!
  const entropyAnalysis = analyzeWordEntropy(text);
  results.entropy = entropyAnalysis;
  
  const densityAnalysis = analyzeSemanticDensity(text);
  results.density = densityAnalysis;

  // 💧 Watermark Hunter - חדש V5!
  const watermarkAnalysis = analyzeWatermarks(text);
  results.watermarks = watermarkAnalysis;
  results.watermarkPenalty = watermarkAnalysis.scorePenalty;

  // 🤖 Robotic Syntax - חדש V5.1!
  const roboticAnalysis = analyzeRoboticSyntax(text);
  results.roboticSyntax = roboticAnalysis;
  results.roboticPenalty = roboticAnalysis.scorePenalty;

  // 🎩 Claude Hunter - חדש V5.2!
  const claudeAnalysis = analyzeClaudeSpecifics(text);
  results.claudeSpecifics = claudeAnalysis;
  results.claudePenalty = claudeAnalysis.scorePenalty;

  // 🏆 Superlatives - חדש V5.3!
  const superlativeAnalysis = analyzeSuperlatives(text);
  results.superlatives = superlativeAnalysis;
  results.superlativePenalty = superlativeAnalysis.scorePenalty;

  // 🏗️ Structure & Tone - חדש V5.4!
  const structureAnalysis = analyzeStructureAndTone(text);
  results.structureTone = structureAnalysis;
  results.structurePenalty = structureAnalysis.scorePenalty;

  // 👔 Formal Language - חדש V5.5!
  const formalAnalysis = analyzeFormalLanguage(text);
  results.formalLanguage = formalAnalysis;
  results.formalPenalty = formalAnalysis.scorePenalty;

  // 🔥 Pseudo-Perplexity - חדש!
  const perplexityAnalysis = analyzePseudoPerplexity(text);
  results.perplexity = perplexityAnalysis;
  results.perplexityPenalty = perplexityAnalysis.isLowPerplexity ? 15 : -5;

  // 🔥 N-gram Analysis - חדש!
  const ngramAnalysis = analyzeNgrams(text);
  results.ngrams = ngramAnalysis;
  results.ngramPenalty = ngramAnalysis.normalizedScore;

  // 🔥 Zipf's Law - חדש!
  const zipfAnalysis = analyzeZipfLaw(text);
  results.zipf = zipfAnalysis;
  results.zipfPenalty = zipfAnalysis.isTooUniform ? 12 : (zipfAnalysis.isTooRandom ? 8 : 0);

  // 🔥 Vocabulary Fingerprint - חדש!
  const vocabAnalysis = analyzeVocabularyFingerprint(text);
  results.vocabulary = vocabAnalysis;
  results.vocabPenalty = vocabAnalysis.isLimitedVocab ? 12 : -3;

  // 🔥 Repetition Patterns - חדש!
  const repetitionAnalysis = analyzeRepetitionPatterns(text);
  results.repetitionPatterns = repetitionAnalysis;
  results.patternPenalty = repetitionAnalysis.repetitionScore;

  // 🔥 Sentence Rhythm - חדש!
  const rhythmAnalysis = analyzeSentenceRhythm(text);
  results.rhythm = rhythmAnalysis;
  results.rhythmPenalty = rhythmAnalysis.hasNaturalRhythm ? -8 : 12;

  // 🔥 Connector Density - חדש!
  const connectorAnalysis = analyzeConnectorDensity(text);
  results.connectors = connectorAnalysis;
  results.connectorPenalty = connectorAnalysis.connectorScore;

  // 🔥 Excessive Quotes - חדש!
  const quotesAnalysis = analyzeExcessiveQuotes(text);
  results.quotes = quotesAnalysis;
  results.quotesPenalty = quotesAnalysis.quoteScore;

  // 🔥 Special Characters (dashes, fancy quotes, etc.) - חדש!
  const specialCharsAnalysis = analyzeSpecialCharacters(text);
  results.specialChars = specialCharsAnalysis;
  results.specialCharsPenalty = specialCharsAnalysis.specialCharScore;

  // Burstiness
  const burstinessAnalysis = analyzeBurstiness(text);
  results.burstinessScore = burstinessAnalysis.burstinessScore;
  results.burstinessPenalty = burstinessAnalysis.isHumanLike ? -8 : 12;

  // סטטיסטיקות סגנון - עכשיו בשימוש!
  const styleStats = analyzeStyleStatistics(text);
  results.styleStatistics = styleStats;
  results.styleUniformityPenalty = styleStats.standardDeviations.sentenceLength < 3 ? 10 : 0;

  // משפטים פשוטים/מורכבים
const complexityAnalysis = analyzeSentenceComplexity(text);
results.simpleSentences = complexityAnalysis.simple;
results.compoundSentences = complexityAnalysis.compound;
results.complexSentences = complexityAnalysis.complex;
  results.complexSentenceRatio = complexityAnalysis.complexRatio;

  // פסיביות
const passiveAnalysis = analyzePassiveVoice(text);
results.passiveSentences = passiveAnalysis.passiveCount;
results.passiveRatio = passiveAnalysis.passiveRatio;
  results.passiveInstances = passiveAnalysis.passiveInstances;

  // דקדוק עברי מתקדם - עכשיו בשימוש!
  const advancedGrammar = analyzeAdvancedHebrewGrammar(text);
  results.advancedGrammar = advancedGrammar;
  results.grammarPenalty = advancedGrammar.definiteArticleRatio < 0.03 ? 8 : 0;

  // תכונות דקדוק בסיסיות
const hebrewGrammar = analyzeHebrewGrammarFeatures(text);
results.heDefiniteCount = hebrewGrammar.definiteArticleCount;
results.smichutCount = hebrewGrammar.smichutCount;

  // קוהרנטיות - מתוקן!
const semanticCoherence = analyzeSemanticCoherence(text);
results.forcedConnections = semanticCoherence.forcedConnections;
results.abruptTopicChanges = semanticCoherence.abruptTopicChanges;

  // עקביות תוכן
  const contentConsistency = analyzeContentConsistency(text);
  results.logicalJumps = contentConsistency.logicalJumps;
  results.topicConsistency = contentConsistency.topicConsistency;

  // רגשות מתקדמים
const advancedEmotion = analyzeAdvancedEmotionFlow(text);
results.emotionalShifts = advancedEmotion.emotionalShifts;
results.ironyIndicators = advancedEmotion.ironyIndicators;
  results.hasEmotionalVariety = advancedEmotion.hasEmotionalVariety;

  // תרבות ועדכניות
const culturalAnalysis = analyzeCulturalReferences(text);
results.culturalHits = culturalAnalysis.culturalHits;
results.culturalCount = culturalAnalysis.culturalCount;

const recencyAnalysis = analyzeRecency(text);
results.recencyHits = recencyAnalysis.recencyHits;
results.recencyCount = recencyAnalysis.recencyCount;

// עקביות רעיונית
const ideaConsistency = analyzeIdeaConsistency(text);
results.contradictionScore = ideaConsistency.contradictionScore;

// ============================================================================================
  // 17. חישוב ניקוד כולל
// ============================================================================================

  // ניקוד בסיס
results.oldMetricsScore =
  results.phraseScore +
  results.uniformityPenalty +
  results.repetitionPenalty +
  results.marketingScore +
  results.humanBonus +
  results.claudeScore +
    results.gptDashScore +  // 🆕 מקפים עם רווחים - סימן GPT
  results.questionPenalty +
  results.lexicalPenalty +
    results.linkingScore;

  // ניקוד מורחב
results.newMetricsScore =
  results.toneConsistencyScore +
  results.slangBonus +
  results.emotionMixScore +
  results.paragraphUniformityScore +
  results.hedgingScore +
  results.selfReferenceScore +
  results.exampleScore +
  results.trendyScore +
    results.mistakeScore;

  // ניקוד מתקדם PRO
let advancedScore = 0;

  // 🔥 PRO Analysis Scores
  advancedScore += results.deepScorePenalty;       // Forensic Patterns V4
  
  if (results.entropy?.isTooGeneric) advancedScore += 15;   // עונש על גנריות
  if (results.density?.isFluffy) advancedScore += 12;       // עונש על מריחת זמן
  
  advancedScore += results.watermarkPenalty;       // עונש על סימני מים
  advancedScore += results.roboticPenalty;         // עונש על תחביר רובוטי (V5.1)
  advancedScore += results.claudePenalty;          // עונש על טיקים של קלוד (V5.2)
  advancedScore += results.superlativePenalty;     // עונש על הגזמות (V5.3)
  advancedScore += results.structurePenalty;       // עונש על מבנה וטון (V5.4)
  advancedScore += results.formalPenalty;          // עונש על שפה רשמית (V5.5)
  
  advancedScore += results.perplexityPenalty;      // Pseudo-Perplexity
  advancedScore += results.ngramPenalty;           // N-grams
  advancedScore += results.zipfPenalty;            // Zipf's Law
  advancedScore += results.vocabPenalty;           // Vocabulary
  advancedScore += results.patternPenalty;         // Repetition Patterns
  advancedScore += results.rhythmPenalty;          // Sentence Rhythm
  advancedScore += results.connectorPenalty;       // Connectors
  advancedScore += results.quotesPenalty;          // 🆕 Excessive Quotes
  advancedScore += results.specialCharsPenalty;   // 🆕 Special Characters (dashes etc.)
  
  // Burstiness
  advancedScore += results.burstinessPenalty;
  
  // סטטיסטיקות סגנון
  advancedScore += results.styleUniformityPenalty;
  
  // דקדוק
  advancedScore += results.grammarPenalty;

  // משפטים מורכבים
  if (results.complexSentenceRatio > 0.45) advancedScore += 12;
  else if (results.complexSentenceRatio > 0.35) advancedScore += 6;

  // פסיביות
  if (results.passiveRatio > 0.35) advancedScore += 10;
  else if (results.passiveRatio > 0.25) advancedScore += 5;

  // קוהרנטיות
  if (results.forcedConnections > 3) advancedScore += 8;
  if (results.abruptTopicChanges > 2) advancedScore += 6;

  // רגשות
  if (!results.hasEmotionalVariety && sentences.length > 5) advancedScore += 6;
  if (results.ironyIndicators > 0) advancedScore -= 8;

  // תרבות ועדכניות
  if (results.culturalCount >= 2) advancedScore -= 10;
  if (results.recencyCount >= 1) advancedScore -= 8;

  // סתירות
  if (results.contradictionScore > 0) advancedScore -= 5;

results.advancedMetricsScore = advancedScore;

  // משקלול סופי PRO - יותר משקל לניתוחים המתקדמים
const finalScore =
    results.oldMetricsScore * 0.35 +      // פחות משקל לבדיקות בסיסיות
    results.newMetricsScore * 0.20 +      
    results.advancedMetricsScore * 0.45;  // יותר משקל לניתוחים PRO

  // 🔥 נורמליזציה משופרת - מתחשבת בטווח אמיתי
  // הציון הגולמי יכול להגיע ל-500+, אז צריך לנרמל נכון
  // 0-30 = אנושי, 30-60 = מעורב, 60-100 = AI
  const MAX_RAW_SCORE = 300; // ציון גולמי מקסימלי "סביר"
  const normalizedScore = (finalScore / MAX_RAW_SCORE) * 100;
  results.rawScore = Math.max(0, Math.min(100, normalizedScore));
  
  // 🔥 PRO Confidence Score - שילוב של כל הניתוחים
  let proSignals = [
    results.perplexity?.isLowPerplexity,
    results.ngrams?.isAIPattern,
    results.zipf?.isTooUniform,
    results.vocabulary?.isLimitedVocab,
    results.repetitionPatterns?.hasRepetitiveStructure,
    !results.rhythm?.hasNaturalRhythm,
    results.connectors?.isOverlyFormal,
    results.quotes?.isExcessiveQuotes,       // 🆕 מרכאות מוגזמות
    results.specialChars?.hasAICharacters,   // 🆕 תווים מיוחדים (דאשים וכו')
    results.watermarks?.hasWatermarks,       // 🆕 סימני מים (תווים נסתרים)
    results.roboticSyntax?.hasRoboticSyntax, // 🆕 תחביר רובוטי (V5.1)
    results.claudeSpecifics?.isClaude,       // 🆕 זיהוי קלוד (V5.2)
    results.entropy?.isTooGeneric,           // 🆕 טקסט גנרי מדי (V5)
    results.density?.isFluffy,               // 🆕 יותר מדי מילים ריקות (V5)
    !burstinessAnalysis.isHumanLike
  ].filter(Boolean).length;
  
  // הוספת סימנים פורנזיים V4
  if (results.deepSignals && results.deepSignals.length > 0) {
    proSignals += results.deepSignals.length; // כל סימן פורנזי נחשב כאות אזהרה נוסף
  }

  results.proSignalCount = proSignals;
  results.proConfidence = proSignals >= 6 ? 'גבוהה מאוד' :
                          proSignals >= 4 ? 'גבוהה' :
                          proSignals >= 2 ? 'בינונית' : 'נמוכה';

// ============================================================================================
  // 18. קביעת ביטחון והסבר
// ============================================================================================

  if (results.rawScore >= 80) {
  results.confidence = 'גבוהה מאוד';
    results.explanation = 'התוכן ככל הנראה נכתב על ידי AI - מבנה אחיד, ביטויים גנריים, וחוסר אישיות.';
  } else if (results.rawScore >= 65) {
  results.confidence = 'גבוהה';
    results.explanation = 'קיימים מאפיינים מובהקים של טקסט AI - ייתכן שנוצר אוטומטית.';
  } else if (results.rawScore >= 45) {
  results.confidence = 'בינונית';
    results.explanation = 'חלק מהסימנים מצביעים על AI, אך לא באופן חד משמעי. ייתכן עריכה אנושית.';
  } else if (results.rawScore >= 30) {
    results.confidence = 'נמוכה-בינונית';
    results.explanation = 'מעט סימני AI, אך רוב הטקסט נראה אנושי.';
} else {
  results.confidence = 'נמוכה';
    results.explanation = 'לא זוהו סימנים מובהקים ל-AI. סביר שזה טקסט אנושי.';
}

// ============================================================================================
  // 19. זיהוי בעיות והמלצות
// ============================================================================================

  const problems = [];
  const suggestions = [];

  if (results.phraseScore > 0) {
    problems.push({
      type: "ביטויים גנריים",
      elements: results.phraseHits,
      score: results.phraseScore,
      suggestion: "להחליף בניסוחים אישיים"
    });
    suggestions.push("החלף ביטויים גנריים (לסיכום, ניתן לומר) בביטויים אישיים יותר.");
  }

  if (results.repetitionPenalty > 0) {
    problems.push({
      type: "פתיחות חוזרות",
      elements: results.repeatedStarts,
      score: results.repetitionPenalty,
      suggestion: "גיוון פתיחות המשפטים"
    });
    suggestions.push("גוון את פתיחות המשפטים.");
  }

  if (results.claudeScore > 0) {
    problems.push({
      type: "ביטויי AI",
      elements: results.claudeHits,
      score: results.claudeScore,
      suggestion: "הסרה או החלפה"
    });
    suggestions.push("הסר ביטויים אופייניים ל-AI כמו 'בהחלט', 'אשמח לעזור'.");
  }

  if (!results.hasHumanTouch) {
    problems.push({
      type: "חוסר אנושיות",
      elements: ["אין ביטויים אישיים"],
      score: 12,
      suggestion: "הוסף ביטויים בגוף ראשון"
    });
    suggestions.push("הוסף ביטויים אישיים: לדעתי, אני חושב, מניסיוני.");
  }

  if (results.burstinessPenalty > 0) {
    problems.push({
      type: "אחידות מוגזמת",
      elements: ["משפטים באורך דומה מדי"],
      score: results.burstinessPenalty,
      suggestion: "גוון אורכי משפטים"
    });
    suggestions.push("ערבב משפטים קצרים מאוד עם ארוכים.");
  }

  const totalProblemScore = problems.reduce((acc, p) => acc + p.score, 0);
  const potentialScore = Math.max(0, Math.round(results.rawScore - totalProblemScore));

  results.problematicElements = problems;
  results.improvementSuggestions = [...new Set(suggestions)];
  results.potentialMinScore = potentialScore;

  // ============================================================================================
  // 20. יצירת סיכום
  // ============================================================================================

  let summaryText = `**ציון AI נוכחי:** ${Math.round(results.rawScore)} (${results.confidence})\n`;
  summaryText += `**רמת ודאות PRO:** ${results.proConfidence} (${results.proSignalCount}/8 סימנים)\n\n`;
  summaryText += `**הסבר:** ${results.explanation}\n\n`;
  
  summaryText += `**🔥 ניתוח PRO:**\n`;
  summaryText += `• Pseudo-Perplexity: ${(results.perplexity?.perplexityScore * 100).toFixed(0)}% - ${results.perplexity?.analysis}\n`;
  summaryText += `• N-grams זוהו: ${results.ngrams?.bigramCount + results.ngrams?.trigramCount} דפוסי AI\n`;
  summaryText += `• Zipf's Law: ${results.zipf?.analysis}\n`;
  summaryText += `• Vocabulary: TTR=${results.vocabulary?.typeTokenRatio?.toFixed(2)} - ${results.vocabulary?.analysis}\n`;
  summaryText += `• קצב משפטים: ${results.rhythm?.analysis}\n`;
  summaryText += `• מחברים: ${results.connectors?.analysis}\n`;
  summaryText += `• מרכאות: ${results.quotes?.analysis} (${results.quotes?.unnecessaryQuotes} מיותרות)\n\n`;
  
  summaryText += `**ניתוח מבני:**\n`;
  summaryText += `• משפטים: ${sentences.length} (ממוצע ${results.avgLength.toFixed(1)} מילים)\n`;
  summaryText += `• סטיית תקן אורך: ${results.stdDev.toFixed(1)}\n`;
  summaryText += `• Burstiness: ${(results.burstinessScore * 100).toFixed(0)}% (${results.burstinessScore > 0.25 ? 'אנושי' : 'AI-like'})\n`;
  summaryText += `• יחס פסיביות: ${(results.passiveRatio * 100).toFixed(0)}%\n`;
  summaryText += `• יחס מורכבות: ${(results.complexSentenceRatio * 100).toFixed(0)}%\n\n`;

  if (problems.length > 0) {
    summaryText += `**בעיות שזוהו (${problems.length}):**\n`;
    problems.sort((a, b) => b.score - a.score).forEach((p, i) => {
      summaryText += `${i + 1}. ${p.type} (${p.score} נק')\n`;
    });
    summaryText += '\n';
  }

  if (suggestions.length > 0) {
    summaryText += `**המלצות לשיפור:**\n`;
    suggestions.forEach((s, i) => {
      summaryText += `${i + 1}. ${s}\n`;
    });
  }

  summaryText += `\n**ציון פוטנציאלי אחרי תיקון:** ${potentialScore}`;

  results.summary = summaryText;

  return results;
}

// ========================================
// 🔧 פונקציית ניקוי ותיקון אוטומטי
// ========================================

/**
 * מילון החלפות מורחב - 150+ ביטויים עם 8-15 אלטרנטיבות לכל אחד
 * מבטיח גיוון מקסימלי גם על המון תכנים
 */
const aiToHumanReplacements = {
  
  // ========================================
  // 🔷 ביטויי פתיחה וסיכום
  // ========================================
  "ניתן לומר כי": ["בקיצור,", "תכלס,", "בעצם,", "אז ככה -", "הנה העניין:", "פשוט -", "זהו:", "ובמילים פשוטות,", "אם לקצר,", "אז מה?", "בפשטות,", "הנקודה היא ש"],
  "ניתן לומר ש": ["בקיצור,", "תכלס,", "בעצם,", "פשוט -", "הנה העניין:", "ובמילים פשוטות,", "אם לקצר,", "בפשטות,", "הנקודה היא ש"],
  "באופן כללי": ["בגדול,", "ככה בערך,", "פחות או יותר,", "בכללי,", "בד\"כ,", "רוב הזמן,", "בדרך כלל,", "בממוצע,", "לרוב,", "בעיקרון,", "בבסיס,"],
  "לסיכום": ["בקיצור,", "אז מה למדנו?", "השורה התחתונה:", "סיכום קצר:", "בסוף,", "אז לסכם -", "לקראת סוף,", "בנקודה,", "מה שחשוב:", "בשורה אחת:", "התמצית:"],
  "במאמר זה": ["פה", "בדף הזה", "כאן", "בפוסט", "בכתבה", "בעמוד", "במדריך הזה", "בתוכן הזה", "למעלה", "למטה"],
  "בפתח הדברים": ["אז ככה,", "בואו נתחיל -", "להתחלה,", "קודם כל,", "ראשית,", "נתחיל מזה:", "אז הנה -", "לפני הכל,", "בהתחלה,", "אז קודם -"],
  "לאור זאת": ["אז", "לכן", "ובגלל זה", "ומזה יוצא ש", "כתוצאה,", "אז בעקבות זה,", "ולכן,", "בעקבות,", "מזה משתמע ש"],
  "בהתאם לכך": ["אז", "לכן", "ככה ש", "ולפי זה,", "בהתאם,", "לפי זה,", "מתאים לזה,", "בקנה אחד עם זה,"],
  "להלן": ["הנה", "זה", "אלה", "פה", "למטה", "בהמשך", "עכשיו", "מה שבא:", "אז הנה:"],
  
  // ========================================
  // 🔷 ביטויי AI אופייניים - "חשוב"
  // ========================================
  "חשוב לציין כי": ["שימו לב -", "רגע, חשוב:", "אגב,", "הנה נקודה:", "תזכרו:", "אל תפספסו:", "טיפ:", "עוד משהו -", "דבר נוסף:", "לא לשכוח:", "שווה לשים לב:"],
  "חשוב לציין ש": ["שימו לב -", "רגע, חשוב:", "אגב,", "הנה נקודה:", "תזכרו:", "עוד משהו -", "דבר נוסף:", "נקודה:", "שווה לדעת:"],
  "חשוב לציין": ["שימו לב -", "אגב,", "הנה עוד:", "נקודה:", "טיפ:", "עוד משהו:", "רגע -", "וגם:", "לא פחות חשוב:"],
  "חשוב להדגיש כי": ["תזכרו ש", "אל תשכחו -", "חייבים להבין:", "הנקודה המרכזית:", "הדגש:", "שימו לב טוב:", "מאוד חשוב:", "קריטי:"],
  "חשוב להדגיש ש": ["תזכרו ש", "אל תשכחו -", "חייבים להבין:", "שימו לב:", "קריטי -", "מאוד משמעותי:", "אסור לפספס:"],
  "חשוב להדגיש": ["תזכרו ש", "הנה הקטע:", "מאוד משמעותי:", "הנקודה:", "קריטי:", "המפתח:", "הכי חשוב:"],
  "חשוב לזכור כי": ["תזכרו ש", "אל תשכחו:", "זכרו -", "לא לשכוח:", "תמיד תזכרו:", "חשוב -", "נקודה למחשבה:"],
  "חשוב לזכור ש": ["שווה לדעת ש", "כדאי לדעת -", "טוב לדעת ש", "משהו שכדאי לדעת:"],
  "חשוב לזכור": ["שווה לדעת", "כדאי לדעת", "טוב לדעת", "משהו חשוב"],
  "חשוב להבין כי": ["העניין הוא ש", "הקטע הוא ש", "המציאות היא ש", "בפועל"],
  "חשוב להבין ש": ["תבינו ש", "צריך להבין:", "הקטע הוא ש", "בפשטות:", "הנקודה:"],
  "חשוב להבין": ["צריך להבין", "תבינו", "העניין הוא", "הקטע הוא", "הרעיון:"],
  "חשוב לדעת כי": ["שווה לדעת:", "תדעו ש", "הנה פקט:", "מידע חשוב:", "לידיעתכם:"],
  "חשוב לדעת ש": ["שווה לדעת:", "תדעו ש", "עובדה:", "מעניין:"],
  "חשוב לדעת": ["שווה לדעת", "תדעו", "עובדה -", "לידיעתכם"],
  
  // ========================================
  // 🔷 ביטויי AI אופייניים - "ראוי/יש"
  // ========================================
  "ראוי לציין כי": ["אגב,", "שווה לדעת:", "עוד משהו:", "נקודה:", "בהקשר הזה:", "וגם:", "אה, ו"],
  "ראוי לציין ש": ["אגב,", "שווה לדעת:", "עוד:", "וגם:", "נקודה:"],
  "ראוי לציין": ["אגב,", "שווה לדעת:", "עוד משהו -", "וגם -", "בנוסף -"],
  "ראוי להזכיר כי": ["אגב,", "שווה לדעת:", "עוד נקודה:", "וגם:", "כדאי לדעת:"],
  "ראוי להזכיר ש": ["אגב,", "שווה לדעת ש", "עוד:", "וגם:"],
  "ראוי להזכיר": ["אגב,", "שווה לדעת:", "עוד משהו -", "כמו כן -", "וגם -"],
  "מן הראוי": ["כדאי", "שווה", "רצוי", "מומלץ", "טוב", "עדיף", "הגיוני", "נכון"],
  "יש לציין כי": ["אגב,", "שימו לב -", "עוד משהו:", "וגם:", "נקודה:", "עוד:"],
  "יש לציין ש": ["אגב,", "עוד משהו:", "וגם:", "נקודה:"],
  "יש לציין": ["אגב,", "עוד -", "וגם:", "שימו לב:"],
  "יש לזכור כי": ["תזכרו ש", "אל תשכחו -", "לא לשכוח:", "זכרו -"],
  "יש לזכור ש": ["שווה לדעת ש", "כדאי לדעת -", "טוב לדעת ש"],
  "יש לזכור": ["שווה לדעת", "כדאי לדעת", "טוב לדעת"],
  "יש להניח כי": ["כנראה ש", "סביר ש", "נראה ש", "אפשר להניח ש"],
  "יש להניח ש": ["כנראה ש", "סביר ש", "נראה ש"],
  "יש לקחת בחשבון": ["צריך לחשוב על", "שווה לשקול", "קחו בחשבון", "כדאי לשקול"],
  
  // ========================================
  // 🔷 מחברים פורמליים - קבוצה 1
  // ========================================
  "בנוסף לכך": ["וגם", "ועוד דבר -", "גם", "ומלבד זה,", "חוץ מזה,", "ועוד -", "בנוסף,", "גם כן,", "עוד משהו -", "ומה עוד?", "לא רק זה -"],
  "כמו כן": ["וגם", "גם", "ועוד -", "בנוסף", "עוד", "ומלבד זה", "חוץ מזה", "גם כן", "ועוד דבר", "ומה עוד"],
  "יתר על כן": ["ומה עוד?", "ועוד:", "גם", "יותר מזה -", "ובכלל,", "ואפילו יותר -", "וזה לא הכל:", "ומעבר לזה:"],
  "יתרה מזאת": ["ועוד משהו -", "וגם", "ומלבד זה -", "יותר מזה:", "ואפילו:", "ובנוסף לזה:", "וזה עוד לא הכל:"],
  "יתרה מזו": ["ועוד משהו -", "וגם", "ומלבד זה -", "יותר מזה:", "ואפילו:", "ולא רק זה:"],
  "מעבר לכך": ["חוץ מזה,", "ומעבר לזה -", "גם", "ובנוסף,", "ולא רק זה,", "יותר מזה,", "ואפילו,"],
  "נוסף על כך": ["וגם", "חוץ מזה,", "ועוד -", "בנוסף,", "גם כן,", "ומלבד זה,"],
  "זאת ועוד": ["וגם", "ובנוסף", "ועוד דבר -", "יותר מזה -", "ומה עוד?"],
  
  // ========================================
  // 🔷 מחברים פורמליים - קבוצה 2 (ניגודים)
  // ========================================
  "לעומת זאת": ["מצד שני,", "אבל", "לעומת זה,", "מנגד,", "אבל מצד שני,", "ומנגד,", "אבל הנה -", "אלא ש", "רק ש"],
  "מאידך גיסא": ["מצד שני,", "אבל מנגד,", "ומהצד השני,", "אבל", "אבל מנגד -", "לעומת זה,"],
  "מאידך": ["מצד שני,", "אבל", "לעומת זה,", "מנגד,", "ומהצד השני,"],
  "אף על פי כן": ["אבל בכל זאת,", "ועדיין,", "למרות הכל,", "ובכל זאת,", "אבל עדיין,", "למרות זה,", "ועם כל זה,"],
  "עם זאת": ["אבל", "ועדיין", "בכל זאת", "אבל הנה -", "רק ש", "אלא ש", "ועם כל זה"],
  "למרות זאת": ["אבל", "ועדיין", "בכל זאת", "למרות הכל", "אבל בכל זאת"],
  "אולם": ["אבל", "רק ש", "אלא ש", "ועדיין", "ובכל זאת"],
  "ברם": ["אבל", "רק ש", "אלא ש", "ועדיין"],
  "אלא ש": ["אבל", "רק ש", "הבעיה היא ש", "הקאץ' הוא ש"],
  
  // ========================================
  // 🔷 מחברים פורמליים - קבוצה 3 (סיבה ותוצאה)
  // ========================================
  "אי לכך": ["אז", "לכן", "ולכן", "בעקבות זה,", "ומזה,", "כתוצאה,"],
  "לפיכך": ["אז", "לכן", "ובגלל זה", "בעקבות,", "כתוצאה,", "ומזה יוצא ש"],
  "משום כך": ["לכן", "אז", "בגלל זה", "ולכן", "ובעקבות זה", "כתוצאה"],
  "כתוצאה מכך": ["אז", "ולכן", "בגלל זה", "ומזה -", "וכתוצאה -", "בעקבות זה -"],
  "כתוצאה מזה": ["אז", "ולכן", "בגלל זה", "ומזה -", "בעקבות -"],
  "מכאן ש": ["אז", "לכן", "ומזה יוצא ש", "כלומר", "זאת אומרת"],
  "מכאן נובע כי": ["אז", "ולכן", "זה אומר ש", "כלומר", "המסקנה:"],
  "מכאן נובע ש": ["אז", "ולכן", "זה אומר ש", "כלומר"],
  "בשל כך": ["בגלל זה", "לכן", "אז", "ומזה", "בעקבות"],
  "עקב כך": ["בגלל זה", "לכן", "אז", "ומזה", "בעקבות זה"],
  "כפועל יוצא": ["אז", "ולכן", "וכתוצאה", "בעקבות זה"],
  
  // ========================================
  // 🔷 ביטויי Claude/GPT אופייניים - 30+ חלופות!
  // ========================================
  "בהחלט": [
    "כן", "ברור", "בטח", "נכון", "מאה אחוז", "ממש", "לגמרי", "בדיוק", "אכן",
    "בטוח", "וודאי", "בלי ספק", "בלי שאלה", "חד משמעית", "לחלוטין", "באופן מוחלט",
    "אין ספק", "אין שאלה", "זה ברור", "זה בטוח", "זה נכון", "זה מדויק",
    "בהחלט כן", "בוודאות", "בביטחון", "מובן מאליו", "פשוט כן", "בפירוש",
    "אבסולוטי", "טוטאלי", "מוחלט"
  ],
  "כמובן": [
    "ברור", "כן", "בטח", "ודאי", "נכון", "מובן", "פשוט",
    "ברור לגמרי", "בטח שכן", "ודאי שכן", "נכון מאוד", "מובן מאליו", "פשוט כן",
    "זה ברור", "זה מובן", "זה ידוע", "זה פשוט", "אין ספק", "בלי שאלה",
    "מאה אחוז", "לגמרי", "לחלוטין", "בהחלט", "בדיוק", "אכן",
    "כן כן", "בטח בטח", "ברור ברור", "נכון נכון"
  ],
  "ללא ספק": [
    "בטוח", "ברור", "בלי שאלה", "מאה אחוז", "פשוט", "לגמרי",
    "בלי ספק", "אין ספק", "אין שאלה", "חד משמעית", "לחלוטין", "באופן מוחלט",
    "זה ברור", "זה בטוח", "זה ודאי", "זה מוחלט", "זה חד משמעי",
    "בהחלט", "בוודאות", "בביטחון", "מובן מאליו", "פשוט כן", "בפירוש",
    "כן", "ברור שכן", "בטח שכן", "ודאי שכן", "נכון מאוד", "אכן"
  ],
  "אכן": [
    "כן", "נכון", "באמת", "בדיוק", "ממש",
    "בהחלט", "בטח", "ברור", "ודאי", "מאה אחוז",
    "זה נכון", "זה באמת", "זה בדיוק", "זה ממש", "זה כן",
    "אכן כן", "נכון מאוד", "באמת באמת", "בדיוק כך", "ממש ככה",
    "כן כן", "נכון נכון", "באמת שכן", "בדיוק בדיוק", "ממש ממש",
    "בפירוש", "בוודאות", "בהחלט כן", "לגמרי", "לחלוטין"
  ],
  "אשמח לעזור": [
    "בכיף", "אין בעיה", "בשמחה", "כמובן",
    "בטח", "ברור", "ודאי", "נכון", "כן",
    "אני פה", "אני כאן", "אני זמין", "אני מוכן", "אני מחכה",
    "תשאלו", "תפנו", "תכתבו", "תצרו קשר", "תדברו איתי",
    "אפשר לפנות", "אפשר לשאול", "אפשר לכתוב", "אפשר ליצור קשר",
    "מחכה לשמוע", "מחכה לעזור", "מוכן לעזור", "שמח לעזור", "אשמח לסייע"
  ],
  "אשמח לסייע": [
    "בכיף", "אין בעיה", "בשמחה",
    "בטח", "ברור", "ודאי", "נכון", "כן",
    "אני פה", "אני כאן", "אני זמין", "אני מוכן", "אני מחכה",
    "תשאלו", "תפנו", "תכתבו", "תצרו קשר", "תדברו איתי",
    "אפשר לפנות", "אפשר לשאול", "אפשר לכתוב", "אפשר ליצור קשר",
    "מחכה לשמוע", "מחכה לעזור", "מוכן לעזור", "שמח לעזור", "אשמח לעזור"
  ],
  "אשמח להסביר": [
    "אסביר", "הנה", "אז ככה",
    "בוא נסביר", "בואו נסביר", "אסביר בקצרה", "אסביר בפשטות", "אסביר במילים פשוטות",
    "הנה הסבר", "הנה הפירוש", "הנה התשובה", "הנה המידע", "הנה הפרטים",
    "אז ככה זה עובד", "אז ככה זה נראה", "אז ככה זה בנוי", "אז ככה זה פועל",
    "בקיצור", "בתכלס", "בפשטות", "במילים פשוטות", "בשפה פשוטה",
    "תשמעו", "תראו", "תבינו", "תדעו", "קחו"
  ],
  "זו שאלה מצוינת": [
    "שאלה טובה", "וואלה שאלה", "הממ, בוא נראה",
    "שאלה מעניינת", "שאלה חשובה", "שאלה נכונה", "שאלה רלוונטית", "שאלה בנקודה",
    "שאלה בול", "שאלה בדיוק", "שאלה בזמן", "שאלה במקום", "שאלה בעניין",
    "אוקיי", "טוב", "יופי", "סבבה", "מעולה",
    "בוא נראה", "בואו נראה", "בוא נבדוק", "בואו נבדוק", "בוא נחשוב",
    "אז ככה", "אז הנה", "אז זהו", "אז זה", "אז מה"
  ],
  "שאלה מעולה": [
    "שאלה טובה", "שאלה מעניינת", "הממ",
    "שאלה חשובה", "שאלה נכונה", "שאלה רלוונטית", "שאלה בנקודה", "שאלה בול",
    "אוקיי", "טוב", "יופי", "סבבה", "מעולה",
    "בוא נראה", "בואו נראה", "בוא נבדוק", "בואו נבדוק", "בוא נחשוב",
    "אז ככה", "אז הנה", "אז זהו", "אז זה", "אז מה",
    "וואלה שאלה", "שאלה בדיוק", "שאלה בזמן", "שאלה במקום", "שאלה בעניין"
  ],
  "נראה כי": [
    "נראה ש", "זה נראה כאילו", "לכאורה", "נדמה ש", "מסתמן ש",
    "זה נראה", "זה נראה כמו", "זה נראה ש", "זה מראה ש", "זה מצביע ש",
    "מסתבר ש", "מתברר ש", "יוצא ש", "עולה ש", "מתגלה ש",
    "אפשר לראות ש", "ניתן לראות ש", "רואים ש", "ברור ש", "ניכר ש",
    "על פניו", "ממבט ראשון", "בהשקפה ראשונה", "לפי מה שנראה", "לפי מה שמסתמן",
    "כנראה", "ככל הנראה", "כפי הנראה", "סביר ש", "יתכן ש"
  ],
  "נראה ש": [
    "זה נראה", "לכאורה", "כאילו", "נדמה ש",
    "זה נראה כמו", "זה נראה כאילו", "זה מראה ש", "זה מצביע ש", "זה מעיד ש",
    "מסתבר ש", "מתברר ש", "יוצא ש", "עולה ש", "מתגלה ש",
    "אפשר לראות ש", "ניתן לראות ש", "רואים ש", "ברור ש", "ניכר ש",
    "על פניו", "ממבט ראשון", "בהשקפה ראשונה", "לפי מה שנראה", "לפי מה שמסתמן",
    "כנראה", "ככל הנראה", "כפי הנראה", "סביר ש", "יתכן ש"
  ],
  "ייתכן ש": [
    "אולי", "יכול להיות ש", "יש סיכוי ש", "לא בטוח אבל",
    "יכול להיות", "יש אפשרות ש", "יש סיכוי", "לא בטוח", "לא ברור",
    "אפשר ש", "אפשרי ש", "יתכן", "יכול להיות שכן", "יכול להיות שלא",
    "מי יודע", "מי יודע אם", "מי יודע ש", "מי יודע אולי", "מי יודע יכול להיות",
    "נראה לי ש", "נדמה לי ש", "מרגיש לי ש", "חושב שאולי", "מניח שאולי",
    "לא הייתי מופתע אם", "לא הייתי שולל ש", "לא הייתי פוסל ש"
  ],
  "ייתכן כי": [
    "אולי", "יכול להיות ש", "יש סיכוי ש",
    "יכול להיות", "יש אפשרות ש", "יש סיכוי", "לא בטוח", "לא ברור",
    "אפשר ש", "אפשרי ש", "יתכן", "יכול להיות שכן", "יכול להיות שלא",
    "מי יודע", "מי יודע אם", "מי יודע ש", "מי יודע אולי", "מי יודע יכול להיות",
    "נראה לי ש", "נדמה לי ש", "מרגיש לי ש", "חושב שאולי", "מניח שאולי",
    "לא הייתי מופתע אם", "לא הייתי שולל ש", "לא הייתי פוסל ש"
  ],
  "ייתכן": [
    "אולי", "יכול להיות", "אפשרי",
    "יש סיכוי", "יש אפשרות", "לא בטוח", "לא ברור", "מי יודע",
    "נראה לי", "נדמה לי", "מרגיש לי", "חושב שאולי", "מניח שאולי",
    "לא הייתי מופתע", "לא הייתי שולל", "לא הייתי פוסל",
    "אפשר", "יכול", "סביר", "אולי כן", "אולי לא",
    "מי יודע אם", "מי יודע ש", "מי יודע אולי", "מי יודע יכול להיות"
  ],
  "סביר להניח ש": [
    "כנראה", "סיכוי טוב ש", "נראה לי ש", "הייתי מהמר ש",
    "כנראה ש", "ככל הנראה", "כפי הנראה", "סביר ש", "יתכן ש",
    "נראה לי", "נדמה לי", "מרגיש לי", "חושב ש", "מניח ש",
    "הייתי אומר ש", "הייתי מניח ש", "הייתי חושב ש", "הייתי מאמין ש",
    "אפשר להניח ש", "ניתן להניח ש", "מסתבר ש", "מתברר ש", "יוצא ש",
    "לפי מה שנראה", "לפי מה שמסתמן", "לפי מה שידוע", "לפי מה שברור"
  ],
  "סביר להניח כי": [
    "כנראה", "סיכוי טוב ש", "נראה לי ש",
    "כנראה ש", "ככל הנראה", "כפי הנראה", "סביר ש", "יתכן ש",
    "נראה לי", "נדמה לי", "מרגיש לי", "חושב ש", "מניח ש",
    "הייתי אומר ש", "הייתי מניח ש", "הייתי חושב ש", "הייתי מאמין ש",
    "אפשר להניח ש", "ניתן להניח ש", "מסתבר ש", "מתברר ש", "יוצא ש",
    "לפי מה שנראה", "לפי מה שמסתמן", "לפי מה שידוע", "לפי מה שברור"
  ],
  "סביר להניח": [
    "כנראה", "סיכוי טוב", "נראה לי",
    "ככל הנראה", "כפי הנראה", "סביר", "יתכן", "אולי",
    "נדמה לי", "מרגיש לי", "חושב", "מניח", "מאמין",
    "הייתי אומר", "הייתי מניח", "הייתי חושב", "הייתי מאמין",
    "אפשר להניח", "ניתן להניח", "מסתבר", "מתברר", "יוצא",
    "לפי מה שנראה", "לפי מה שמסתמן", "לפי מה שידוע", "לפי מה שברור"
  ],
  "ככל הנראה": [
    "כנראה", "נראה לי ש", "מסתבר ש", "כפי הנראה",
    "נדמה לי ש", "מרגיש לי ש", "חושב ש", "מניח ש", "מאמין ש",
    "הייתי אומר ש", "הייתי מניח ש", "הייתי חושב ש", "הייתי מאמין ש",
    "אפשר להניח ש", "ניתן להניח ש", "סביר ש", "יתכן ש", "אולי",
    "לפי מה שנראה", "לפי מה שמסתמן", "לפי מה שידוע", "לפי מה שברור",
    "מה שנראה", "מה שמסתמן", "מה שידוע", "מה שברור", "מה שמתברר"
  ],
  "הנה הסבר": [
    "אז ככה:", "בקיצור:", "הסבר:", "ככה זה עובד:",
    "בתכלס:", "בפשטות:", "במילים פשוטות:", "בשפה פשוטה:", "בעברית:",
    "אז הנה:", "הנה:", "זהו:", "ככה:", "פשוט:",
    "בוא נסביר:", "בואו נסביר:", "אסביר:", "אסביר בקצרה:", "אסביר בפשטות:",
    "תשמעו:", "תראו:", "תבינו:", "תדעו:", "קחו:",
    "אז זהו:", "אז ככה זה:", "אז ככה זה עובד:", "אז ככה זה נראה:"
  ],
  "הנה התשובה": [
    "אז:", "בקיצור:", "התשובה:", "זהו:",
    "בתכלס:", "בפשטות:", "במילים פשוטות:", "בשפה פשוטה:", "בעברית:",
    "אז הנה:", "הנה:", "ככה:", "פשוט:", "בגדול:",
    "אז התשובה:", "התשובה היא:", "התשובה הקצרה:", "התשובה הפשוטה:", "התשובה בקצרה:",
    "תשמעו:", "תראו:", "תבינו:", "תדעו:", "קחו:",
    "אז זהו:", "אז ככה זה:", "אז זה:", "אז מה:"
  ],
  
  // ========================================
  // 🔷 ביטויים אקדמיים ופורמליים
  // ========================================
  "מחקרים מראים כי": ["מחקרים מראים ש", "לפי מחקרים,", "מחקרים גילו ש", "נמצא ש", "הוכח ש"],
  "מחקרים מראים ש": ["לפי מחקרים,", "נמצא ש", "הוכח ש", "גילו ש"],
  "מחקרים רבים מראים": ["הרבה מחקרים מראים", "מחקרים גילו", "נמצא"],
  "הספרות מצביעה על": ["המחקר מראה ש", "נמצא ש", "ידוע ש"],
  "על פי מחקרים": ["לפי מחקרים", "מחקרים מראים", "נמצא"],
  "בהתבסס על": ["לפי", "על בסיס", "בהסתמך על", "בהתאם ל", "על פי"],
  "בהסתמך על": ["לפי", "על בסיס", "בהתאם ל", "על פי"],
  "בספרות המקצועית": ["במחקרים", "בתחום", "אצל מומחים"],
  "כפי שהוזכר לעיל": ["כמו שאמרתי", "כמו קודם", "חזרה -", "שוב -"],
  "כפי שצוין קודם": ["כמו שאמרתי", "כמו קודם", "שוב -"],
  "כפי שניתן לראות": ["אפשר לראות", "רואים ש", "ברור ש", "נראה ש"],
  "כאמור": ["כמו שאמרתי", "שוב", "חזרה", "כפי שציינתי"],
  "כאמור לעיל": ["כמו שאמרתי", "כפי שציינתי קודם", "שוב"],
  
  // ========================================
  // 🔷 ביטויי סיום
  // ========================================
  "בסופו של דבר": ["בסוף", "בשורה התחתונה", "בסוף היום", "מה שחשוב זה", "העיקר", "הסוף סוף"],
  "בשורה התחתונה": ["בקיצור", "בסוף", "המסקנה:", "התוצאה:", "מה שנשאר:", "הסיכום:"],
  "לסיכום הדברים": ["בקיצור,", "אז לסכם:", "סיכום:", "מה למדנו?", "העיקר:"],
  "אני מקווה שזה עוזר": ["מקווה שעזרתי", "מקווה שעזר", "בהצלחה!", "אם יש שאלות - שלחו"],
  "אני מקווה שהסברתי": ["מקווה שזה ברור", "מקווה שהבנתם"],
  "אם יש לך שאלות נוספות": ["שאלות? שלחו", "עוד שאלות? אין בעיה", "אם צריך עוד -"],
  "אם יש לכם שאלות": ["שאלות? שלחו", "צריכים עזרה?"],
  "אני כאן לעזור": ["אפשר לשאול", "אני פה"],
  "נשמח לעזור": ["אפשר לפנות", "אנחנו פה"],
  
  // ========================================
  // 🔷 הסתייגויות מוגזמות
  // ========================================
  "במידה מסוימת": ["קצת", "פחות או יותר", "באיזשהו אופן", "בערך", "יחסית"],
  "במידה רבה": ["הרבה", "מאוד", "ממש", "לגמרי", "בצורה משמעותית"],
  "באופן יחסי": ["יחסית", "בערך", "פחות או יותר"],
  "באופן משמעותי": ["משמעותית", "הרבה", "ממש", "מאוד", "בצורה רצינית", "ברצינות"],
  "באופן ניכר": ["ממש", "מאוד", "משמעותית", "בצורה ברורה", "ברור ש"],
  "באופן בולט": ["מאוד", "ממש", "בבירור", "משמעותית"],
  "באופן מובהק": ["מאוד", "ברור", "בבירור", "חד משמעית"],
  "באופן גורף": ["לגמרי", "בכללי", "בצורה רחבה", "לחלוטין"],
  "באופן חלקי": ["קצת", "חלקית", "בחלק", "לא לגמרי"],
  
  // ========================================
  // 🔷 ביטויי "על מנת" ו"בכדי"
  // ========================================
  "על מנת ל": ["כדי ל", "בשביל ל", "לצורך", "ל"],
  "על מנת ש": ["כדי ש", "בשביל ש", "ש", "כך ש"],
  "בכדי ל": ["כדי ל", "בשביל ל", "לצורך", "ל"],
  "בכדי ש": ["כדי ש", "בשביל ש", "ש"],
  "לצורך כך": ["לזה", "בשביל זה", "למטרה זו"],
  "למטרה זו": ["לזה", "בשביל זה", "לצורך זה"],
  
  // ========================================
  // 🔷 ביטויי זמן פורמליים
  // ========================================
  "נכון להיום": ["היום", "עכשיו", "כיום", "כרגע"],
  "בעת הנוכחית": ["עכשיו", "היום", "כרגע", "בזמן הזה"],
  "בשלב זה": ["עכשיו", "כרגע", "בנקודה הזו", "פה"],
  "בנקודת זמן זו": ["עכשיו", "כרגע", "בשלב הזה", "היום"],
  "לאורך זמן": ["עם הזמן", "במשך הזמן", "לאט לאט", "בהדרגה"],
  "לאורך השנים": ["עם השנים", "במשך השנים", "בהמשך", "עם הזמן"],
  
  // ========================================
  // 🔷 ביטויים כלליים נוספים
  // ========================================
  "הינו": ["הוא", "זה"],
  "הינה": ["היא", "זו", "זאת"],
  "הינם": ["הם", "אלה"],
  "הינן": ["הן", "אלה"],
  "מהווה": ["הוא", "זה", "נחשב", "מהווה את"],
  "מהווים": ["הם", "אלה", "נחשבים"],
  "מצוי": ["נמצא", "יש", "קיים"],
  "קיימת": ["יש", "נמצאת", "קיים"],
  "קיימים": ["יש", "נמצאים", "ישנם"],
  "מתקיים": ["יש", "קורה", "קיים"],
  "מתקיימת": ["יש", "קורה", "קיימת"],
  "ניכר כי": ["ברור ש", "רואים ש", "נראה ש"],
  "ניכר ש": ["ברור ש", "רואים ש", "נראה ש"],
  "ברי כי": ["ברור ש", "ידוע ש", "פשוט"],
  "ברי ש": ["ברור ש", "ידוע ש"],
  "יודגש כי": ["שימו לב:", "חשוב -", "אגב -"],
  "יודגש ש": ["שימו לב:", "חשוב -"],
  "יצוין כי": ["אגב,", "שווה לדעת:", "עוד -"],
  "יצוין ש": ["אגב,", "שווה לדעת:"],
  "ייאמר כי": ["אפשר להגיד ש", "בקיצור,", "אז -"],
  "ייאמר ש": ["אפשר להגיד ש", "בקיצור,"],
  "ניתן לראות כי": ["רואים ש", "ברור ש", "אפשר לראות ש"],
  "ניתן לראות ש": ["רואים ש", "ברור ש", "אפשר לראות ש"],
  "ניתן להבחין כי": ["רואים ש", "ברור ש", "שמים לב ש"],
  "ניתן להבחין ש": ["רואים ש", "ברור ש"],
  "ניתן להבין כי": ["מובן ש", "ברור ש", "אפשר להבין ש"],
  "ניתן להבין ש": ["מובן ש", "ברור ש"],
  "בהקשר זה": ["בקשר לזה,", "בנושא הזה,", "על זה,", "לגבי זה,"],
  "בהקשר הזה": ["בקשר לזה,", "בנושא הזה,", "על זה,"],
  "בנושא זה": ["בזה,", "על זה,", "בקשר לזה,", "לגבי זה,"],
  "ביחס לכך": ["לגבי זה,", "על זה,", "בקשר לזה,"],
  "ביחס לזה": ["לגבי זה,", "על זה,", "בקשר לזה,"]
};

/**
 * אימוג'ים שAI אוהב להשתמש בהם יותר מדי
 */
const aiEmojis = ['✨', '🌟', '💡', '🎯', '🚀', '💪', '👉', '📌', '⭐', '🔑', '💎', '🏆', '✅', '❌', '📊', '📈', '🎉', '👍', '🙌', '💯'];

/**
 * 🆕 מילון "אינגלוזים" (תרגום מכונה מאנגלית)
 * AI נוטה לתרגם ניבים אנגליים מילולית
 */
const anglicismsMap = {
  'בסופו של יום': 'בסיכומו של דבר',
  'לקחת בחשבון': 'להתחשב ב',
  'עושה שכל': 'הגיוני',
  'משחק תפקיד': 'משפיע',
  'תמונה גדולה': 'ראייה רחבה',
  'השורה התחתונה': 'תכלס',
  'לא מחזיק מים': 'לא משכנע',
  'להביא לשולחן': 'להציע',
  'לשים דגש': 'להדגיש',
  'רץ חלק': 'עובד מצוין',
  'בגדול': 'בעיקרון',
  'צד שני של המטבע': 'מצד שני'
};

/**
 * 🆕 מילים מסייגות (Hedging)
 * AI מפחד להתחייב ומשתמש במילים אלו בהגזמה
 */
const hedgingWords = [
  'חשוב לציין', 'ראוי להזכיר', 'כדאי לזכור', 'בדרך כלל',
  'עלול להיות', 'עשוי להוביל', 'במרבית המקרים', 'באופן יחסי',
  'במידה מסוימת', 'לכאורה', 'פוטנציאלית', 'תיאורטית'
];

/**
 * 🆕 פעלים סבילים (Passive Voice)
 * AI כותב "אקדמי" ומרוחק
 */
const passiveMarkers = [
  'ניתן לראות', 'ניתן לומר', 'בוצע', 'נבדק', 'הוחלט',
  'מומלץ לבצע', 'יש לבחון', 'נמצא כי', 'הוסכם ש',
  'נראה כי', 'מסתמן ש', 'ידוע כי'
];

/**
 * 🔧 תווים מיוחדים שAI משתמש בהם במקום תווים פשוטים
 * מערך של [תו_מקורי, תו_חלופי]
 */
// 🔥 תיקון: לא מחליפים ל-" - " כי זה סימן GPT!
const aiSpecialCharsReplacements = [
  // Dashes - AI אוהב דאשים מפוארים - מחליפים לפסיק או נקודתיים
  ['\u2013', ','],      // En-dash → פסיק (לא מקף!)
  ['\u2014', ', '],     // Em-dash → פסיק ורווח (לא " - "!)
  ['\u2212', '-'],      // Minus sign → hyphen
  ['\u2010', '-'],      // Unicode hyphen → regular hyphen
  ['\u2011', '-'],      // Non-breaking hyphen → regular hyphen
  ['\u2012', '-'],      // Figure dash → hyphen
  ['\u2015', ', '],     // Horizontal bar → פסיק ורווח (לא " - "!)
  
  // Quotes - נורמליזציה
  ['\u201C', '"'],      // Left double quote → regular
  ['\u201D', '"'],      // Right double quote → regular
  ['\u2018', "'"],      // Left single quote → apostrophe
  ['\u2019', "'"],      // Right single quote → apostrophe
  ['\u05F4', '"'],      // Hebrew quote → regular
  ['\u05F3', "'"],      // Hebrew single quote → apostrophe
  ['\u00AB', '"'],      // French left quote
  ['\u00BB', '"'],      // French right quote
  ['\u201E', '"'],      // German low quote
  
  // Spaces - AI משתמש ברווחים מיוחדים
  ['\u00A0', ' '],      // Non-breaking space → regular space
  ['\u2002', ' '],      // En space → regular
  ['\u2003', ' '],      // Em space → regular
  ['\u2009', ' '],      // Thin space → regular
  ['\u200B', ''],       // Zero-width space → remove
  ['\u200C', ''],       // Zero-width non-joiner → remove
  ['\u200D', ''],       // Zero-width joiner → remove
  
  // Ellipsis
  ['\u2026', '...'],    // Ellipsis character → three dots
  
  // Other
  // ['\u2022', '-'],   // Bullet → hyphen - הוסר! אנחנו משתמשים ב-• כ-bullet points
  ['\u00B7', '.'],      // Middle dot → period
  ['\u2032', "'"],      // Prime → apostrophe
  ['\u2033', '"'],      // Double prime → quote
  ['\u00A9', '(c)'],    // Copyright
  ['\u00AE', '(R)'],    // Registered
  ['\u2122', '(TM)'],   // Trademark
];

/**
 * 🔧 מילים שAI אוהב לשים במרכאות מיותרות
 * אנושיים לא שמים את המילים האלה במרכאות
 */
const wordsAIQuotesUnnecessarily = [
  'חשוב', 'מעניין', 'מיוחד', 'ייחודי', 'מושלם', 'אידיאלי', 'מצוין', 'נהדר',
  'משמעותי', 'קריטי', 'חיוני', 'הכרחי', 'חובה', 'מומלץ', 'רצוי',
  'פשוט', 'קל', 'מהיר', 'יעיל', 'אפקטיבי', 'מוצלח',
  'בעיה', 'פתרון', 'אתגר', 'הזדמנות', 'יתרון', 'חיסרון',
  'מקצועי', 'איכותי', 'מתקדם', 'חדשני', 'מודרני',
  'נכון', 'טוב', 'רע', 'גרוע', 'עדיף', 'גרוע',
  'אמיתי', 'מדויק', 'ברור', 'פשוט', 'מורכב',
  'הכי', 'יותר', 'פחות', 'מאוד', 'ממש', 'לגמרי',
  'תוצאה', 'תוצאות', 'השפעה', 'השלכות', 'משמעות',
  'דרך', 'שיטה', 'גישה', 'אסטרטגיה', 'טכניקה',
  'מומחה', 'מומחים', 'מקצוען', 'מקצוענים', 'אנשי מקצוע'
];

/**
 * פונקציה לבחירה רנדומלית מרשימה
 */
function randomPick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

/**
 * 🧹 ניקוי בסיסי בלבד - תמיד רץ!
 * (הגרסה הישנה הוסרה - ראה למטה את הגרסה החדשה עם ההגנות)
 */
// Removed old basicCleanText implementation

/**
 * 🧹 ניקוי בסיסי של הטקסט (רץ תמיד)
 * מסיר אימוג'ים, תווים מיוחדים, ושפות זרות
 * 🛡️ כולל הגנה הרמטית על SCRIPT, STYLE ו-TAGS
 */
function basicCleanText(text) {
  let cleaned = text;
  const changes = [];
  
  // =================================================================
  // 🛡️ שלב 1: הגנה על בלוקים שלמים (קוד שלא רוצים לגעת בו)
  // =================================================================
  const protectedBlocks = [];
  
  function protectBlock(tagName) {
      let safety = 0;
      while (safety < 1000) { 
          safety++;
          const regex = new RegExp(`<${tagName}[^>]*>[^]*?<\/${tagName}>`, 'i');
          const match = cleaned.match(regex);
          
          if (!match) break;
          
          const fullBlock = match[0];
          const placeholder = `___PROTECTED_BLOCK_${tagName.toUpperCase()}_${protectedBlocks.length}___`;
          
          protectedBlocks.push({ placeholder: placeholder, content: fullBlock });
          cleaned = cleaned.replace(fullBlock, placeholder);
      }
  }
  
  protectBlock('script');
  protectBlock('style');
  protectBlock('pre'); 
  protectBlock('code'); 
  protectBlock('textarea'); // גם טקסט ב-textarea לא נרצה לשנות

  // =================================================================
  // 🛡️ שלב 1.5: הגנה על רכיבי UI קצרים (כפתורים, כותרות, תוויות)
  // מונע מחיקת אימוג'ים שהם חלק מהעיצוב!
  // =================================================================
  
  // Regex לזיהוי שפות זרות (כדי לנקות גם בתוך אלמנטים מוגנים!)
  const foreignRegex = /[\u0400-\u04FF\u4E00-\u9FFF\u0600-\u06FF]/g;
  const foreignWordRegex = /\S*[\u0400-\u04FF\u4E00-\u9FFF\u0600-\u06FF]\S*/g;
  
  let protectedForeignChars = 0;
  
  // 🔥 מבנה חדש: שומרים מילה + הקשר מלא תמיד!
  const foreignWordsWithContext = [];

  function protectShortUI(tagName) {
      const regex = new RegExp(`<${tagName}\\b[^>]*>(?:(?!<${tagName}).){0,200}<\\/${tagName}>`, 'gi');
      
      // שומרים את הטקסט המלא לפני ההחלפות כדי לשלוף הקשר רחב
      const fullTextBeforeReplace = cleaned;
      
      cleaned = cleaned.replace(regex, function(match, offset) {
          const tagMatch = match.match(/^(<[^>]+>)(.*)(<\/[^>]+>)$/s);
          
          let contentToProtect = match;
          
          if (tagMatch) {
             const openTag = tagMatch[1];
             let innerContent = tagMatch[2];
             const closeTag = tagMatch[3];
             
             // זיהוי מילים שנפגעו לפני הניקוי - עם הקשר רחב!
             const words = innerContent.match(foreignWordRegex);
             if (words) {
                 words.forEach(w => {
                     // שולפים הקשר רחב מהטקסט המלא (100 תווים לכל צד של התגית)
                     const start = Math.max(0, offset - 100);
                     const end = Math.min(fullTextBeforeReplace.length, offset + match.length + 100);
                     const wideContext = fullTextBeforeReplace.substring(start, end);
                     
                     foreignWordsWithContext.push({
                         word: w,
                         context: wideContext
                     });
                 });
             }
             
             // ניקוי רק בתוכן הפנימי
             const cleanInner = innerContent.replace(foreignRegex, function(m) {
                 protectedForeignChars++;
                 return '';
             });
             
             contentToProtect = openTag + cleanInner + closeTag;
          }
          
          const placeholder = `___PROTECTED_UI_${tagName.toUpperCase()}_${protectedBlocks.length}___`;
          protectedBlocks.push({ placeholder: placeholder, content: contentToProtect });
          return placeholder;
      });
  }
  
  function protectClassedUI(tagName) {
      const regex = new RegExp(`<${tagName}\\b[^>]*class=['"][^'"]*['"][^>]*>(?:(?!<${tagName}).){0,200}<\\/${tagName}>`, 'gi');
      
      // שומרים את הטקסט המלא לפני ההחלפות כדי לשלוף הקשר רחב
      const fullTextBeforeReplace = cleaned;
      
      cleaned = cleaned.replace(regex, function(match, offset) {
          const tagMatch = match.match(/^(<[^>]+>)(.*)(<\/[^>]+>)$/s);
          let contentToProtect = match;
          
          if (tagMatch) {
             const openTag = tagMatch[1];
             let innerContent = tagMatch[2];
             const closeTag = tagMatch[3];

             // זיהוי מילים שנפגעו לפני הניקוי - עם הקשר רחב!
             const words = innerContent.match(foreignWordRegex);
             if (words) {
                 words.forEach(w => {
                     // שולפים הקשר רחב מהטקסט המלא (100 תווים לכל צד של התגית)
                     const start = Math.max(0, offset - 100);
                     const end = Math.min(fullTextBeforeReplace.length, offset + match.length + 100);
                     const wideContext = fullTextBeforeReplace.substring(start, end);
                     
                     foreignWordsWithContext.push({
                         word: w,
                         context: wideContext
                     });
                 });
             }
             
             const cleanInner = innerContent.replace(foreignRegex, function(m) {
                 protectedForeignChars++;
                 return '';
             });
             
             contentToProtect = openTag + cleanInner + closeTag;
          }

          const placeholder = `___PROTECTED_CLASSED_${tagName.toUpperCase()}_${protectedBlocks.length}___`;
          protectedBlocks.push({ placeholder: placeholder, content: contentToProtect });
          return placeholder;
      });
  }
  
  // רשימת התגיות שבהן אימוג'י הוא בדרך כלל עיצובי ולא "זבל"
  const uiTags = ['button', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'th', 'label', 'legend', 'strong', 'b', 'small'];
  uiTags.forEach(tag => protectShortUI(tag));

  // תגיות גנריות - מוגנות רק אם יש להן CLASS
  const classedTags = ['div', 'span', 'p', 'i', 'em', 'mark'];
  classedTags.forEach(tag => protectClassedUI(tag));

  // =================================================================
  // 🛡️ שלב 2: הגנה על תגיות HTML (Attributes, Classes, IDs)
  // =================================================================
  const protectedTags = [];
  let tagIndex = 0;
  
  cleaned = cleaned.replace(/<[^>]+>/g, function(match) {
      const placeholder = `___PROTECTED_TAG_${tagIndex}___`;
      protectedTags.push({ placeholder: placeholder, content: match });
      tagIndex++;
      return placeholder;
  });

  // =================================================================
  // 🧹 לוגיקה של הניקוי (עכשיו בטוחה - רצה רק על טקסט נקי!)
  // =================================================================

  // 1. הסרת שפות זרות - חיפוש בטקסט הראשי (אחרי הגנת תגיות)
  const foreignMatches = cleaned.match(foreignRegex);
  const foreignWordMatches = [...cleaned.matchAll(foreignWordRegex)];
  
  // DEBUG
  if (foreignMatches) console.log("Foreign chars found:", foreignMatches.length);
  if (foreignWordMatches.length > 0) console.log("Foreign words found:", foreignWordMatches.length);
  
  // הוספת מילים מהטקסט הראשי עם הקשר
  if (foreignWordMatches.length > 0) {
      foreignWordMatches.forEach(m => {
          const word = m[0];
          const index = m.index;
          const fullText = m.input;
          
          // חותכים 100 תווים לכל צד להקשר רחב
          const start = Math.max(0, index - 100);
          const end = Math.min(fullText.length, index + word.length + 100);
          const context = fullText.substring(start, end);
          
          foreignWordsWithContext.push({
              word: word,
              context: context
          });
      });
  }
  
  let foreignCount = protectedForeignChars;
  if (foreignMatches) {
      foreignCount += foreignMatches.length;
  }

  let foreignWordsList = [];
  
  if (foreignWordsWithContext.length > 0) {
    // סינון כפילויות לפי המילה עצמה
    const seenWords = new Set();
    
    foreignWordsList = foreignWordsWithContext
        .filter(item => {
            if (seenWords.has(item.word)) return false;
            seenWords.add(item.word);
            return true;
        })
        .map(item => {
            // מנקים את המילה מתווים זרים
            const cleanedWord = item.word.replace(foreignRegex, '');
            // מנקים את ההקשר מתווים זרים (כדי שה-AI יראה מה נשאר)
            const cleanedContext = item.context.replace(foreignRegex, '');
            
            return {
                word: item.word,
                cleaned: cleanedWord,
                context: cleanedContext.trim()
            };
        });
    
    changes.push({
      type: 'ניקוי שפות זרות',
      count: foreignCount,
      description: 'הוסרו תווים בערבית/רוסית/סינית',
      details: foreignWordsList.map(w => ({ from: w.word, to: w.cleaned }))
    });
  }
  
  // ניקוי התווים הזרים מהטקסט
  if (foreignCount > 0) {
    cleaned = cleaned.replace(foreignRegex, '');
  }

  // 2. טיפול באימוג'ים
  const emojiRegex = /[\u{1F300}-\u{1F9FF}]/gu;
  const emojiMatches = cleaned.match(emojiRegex);
  
  if (emojiMatches && emojiMatches.length > 0) {
     let removedEmojis = 0;
     
     cleaned = cleaned.replace(/([\u{1F300}-\u{1F9FF}].*?)([\u{1F300}-\u{1F9FF}]+)/gu, function(match, p1, p2) {
         if (p2.length >= 1) { 
             removedEmojis += p2.length;
             return p1; 
         }
         return match;
     });
     
     const remainingEmojis = cleaned.match(emojiRegex);
     if (remainingEmojis && remainingEmojis.length > 3) {
        cleaned = cleaned.replace(emojiRegex, ''); 
        removedEmojis += remainingEmojis.length;
     }

     if (removedEmojis > 0) {
        changes.push({
          type: 'ניקוי אימוג\'ים',
          count: removedEmojis,
          description: 'הוסרו אימוג\'ים מוגזמים'
        });
     }
  }

  // 3. ניקוי סימני GPT מובהקים - תמיד רץ!
  let gptSignsRemoved = 0;
  
  // 3.1 מקפים עם רווחים " - " באמצע משפט - סימן מובהק ל-GPT!
  // 🔥 חשוב: לא להסיר מקפים בתחילת שורה (bullet points)!
  
  // 🔥 מריצים בלולאה עד שאין יותר מקפים GPT!
  let dashLoopCount = 0;
  const maxDashLoops = 10; // מונע לולאה אינסופית
  
  while (cleaned.match(/\S - \S/) && dashLoopCount < maxDashLoops) {
      dashLoopCount++;
      
      // אם יש 3 חלקים (סנדוויץ') - מסירים לגמרי
      // דוגמה: "הפתרון - שהוא יעיל - עובד" -> "הפתרון שהוא יעיל עובד"
      const sandwichPattern = /(\S)\s+-\s+([^-\n]+)\s+-\s+(\S)/g;
      const sandwichMatches = cleaned.match(sandwichPattern);
      if (sandwichMatches) {
          cleaned = cleaned.replace(sandwichPattern, '$1 $2 $3');
          gptSignsRemoved += sandwichMatches.length;
      }
      
      // מקפים בודדים באמצע משפט - מחליפים לרווח בודד
      // 🔥 Pattern: מילה + רווח + מקף + רווח + מילה (לא bullet points!)
      const gptDashPattern = /(\S) - (\S)/g;
      const gptDashCount = (cleaned.match(gptDashPattern) || []).length;
      if (gptDashCount > 0) {
          cleaned = cleaned.replace(gptDashPattern, '$1 $2');
          gptSignsRemoved += gptDashCount;
      }
  }
  
  // 3.2 נקודות (•) - כבר לא מחליפים! אנחנו משתמשים בהם כ-bullet points
  // if (cleaned.includes('•')) {
  //     cleaned = cleaned.replace(/•/g, '-');
  //     gptSignsRemoved++; 
  // }
  
  // 3.3 קווי הפרדה "---" או "—" בשורה נפרדת - סימן GPT מובהק!
  // מסיר שורות שמכילות רק מקפים (2 או יותר)
  const separatorPattern = /\n\s*[-—–]{2,}\s*\n/g;
  const separatorMatches = cleaned.match(separatorPattern);
  if (separatorMatches) {
      cleaned = cleaned.replace(separatorPattern, '\n\n');
      gptSignsRemoved += separatorMatches.length;
  }

  if (gptSignsRemoved > 0) {
      changes.push({
          type: 'ניקוי מקפי GPT',
          count: gptSignsRemoved,
          description: 'הוסרו " - " וקווי הפרדה "---"',
          details: [{ from: ' - ', to: '(הוסר)' }, { from: '---', to: '(הוסר)' }]
      });
  }

  // =================================================================
  // 🛡️ שחזור (בסדר הפוך: קודם תגיות, אחר כך בלוקים - ומהסוף להתחלה!)
  // חובה להשתמש ב-reverse() כדי לפתוח קינונים (Outer משחרר את Inner)
  // =================================================================
  
  // 1. שחזור תגיות
  // [...protectedTags] יוצר עותק כדי ש-reverse לא יהרוס את המקור (למרות שלא קריטי פה)
  [...protectedTags].reverse().forEach(tag => {
      cleaned = cleaned.replace(tag.placeholder, tag.content);
  });

  // 2. שחזור בלוקים
  [...protectedBlocks].reverse().forEach(block => {
      cleaned = cleaned.replace(block.placeholder, block.content);
  });

  // =================================================================
  // 🔥 שלב אחרון: ניקוי מקפים GPT אחרי שחזור התגיות!
  // הניקוי הקודם לא עובד טוב עם placeholders, אז מריצים שוב
  // 🔥 חשוב: מנקים רק בתוכן טקסט, לא בתוך תגיות HTML!
  // =================================================================
  let finalGptDashesRemoved = 0;
  
  // פונקציה שמנקה מקפים GPT - כולל ליד תגיות HTML!
  // 🔥 חשוב: לא למחוק bullet points (מקפים בתחילת שורה)!
  function cleanGptDashesInText(html) {
      let dashesRemoved = 0;
      
      // פונקציה שבודקת אם מקף הוא bullet point
      function isBulletPoint(text, matchIndex) {
          // בודקים אם לפני המקף יש תחילת שורה (או תחילת טקסט)
          const beforeMatch = text.substring(Math.max(0, matchIndex - 10), matchIndex);
          // אם יש newline ואז רק רווחים לפני המקף - זה bullet point
          return /(?:^|\n)\s*$/.test(beforeMatch);
      }
      
      let result = html;
      
      // 1. מקפים רגילים בטקסט: "מילה - מילה" (לא bullet points)
      result = result.replace(/(\S) - (\S)/g, (match, before, after, offset) => {
          // בודקים אם זה bullet point
          if (isBulletPoint(html, offset - 1)) {
              return match; // לא משנים bullet points
          }
          dashesRemoved++;
          return before + ' ' + after;
      });
      
      // 2. מקפים לפני תגית HTML: "מילה - <tag>" (לא bullet points)
      result = result.replace(/(\S) - </g, (match, before, offset) => {
          if (isBulletPoint(html, offset - 1)) {
              return match;
          }
          dashesRemoved++;
          return before + ' <';
      });
      
      // 3. מקפים אחרי תגית HTML: "</tag> - מילה" (לא bullet points)
      result = result.replace(/> - (\S)/g, (match, after, offset) => {
          if (isBulletPoint(html, offset)) {
              return match;
          }
          dashesRemoved++;
          return '> ' + after;
      });
      
      // 4. סנדוויץ' מקפים (לא bullet points)
      result = result.replace(/(\S) - ([^-<>\n]+) - (\S)/g, (match, before, middle, after, offset) => {
          if (isBulletPoint(html, offset - 1)) {
              return match;
          }
          dashesRemoved += 2;
          return before + ' ' + middle + ' ' + after;
      });
      
      return { text: result, removed: dashesRemoved };
  }
  
  // מריצים עד שאין עוד מקפים GPT
  let loopCount = 0;
  const maxLoops = 20;
  while (loopCount < maxLoops) {
      loopCount++;
      const cleanResult = cleanGptDashesInText(cleaned);
      if (cleanResult.removed === 0) break;
      cleaned = cleanResult.text;
      finalGptDashesRemoved += cleanResult.removed;
  }
  
  // =================================================================
  // 🔥 המרת מקפים בתחילת שורה ל-bullet points אמיתיים (•)
  // מקפים בתחילת שורה הם bullet points לגיטימיים, אבל נחליף אותם ל-•
  // =================================================================
  let bulletPointsConverted = 0;
  
  // כל סוגי המקפים האפשריים (Unicode)
  const dashChars = '\\-\\u2010\\u2011\\u2012\\u2013\\u2014\\u2015\\u2212\\u002D';
  
  // Pattern 1: שורה חדשה אמיתית (\n) + מקף + רווח
  const pattern1 = new RegExp(`(\\n)([\\t ]*)[${dashChars}]([\\t ]+)`, 'g');
  cleaned = cleaned.replace(pattern1, (match, newline, leadingSpaces) => {
      bulletPointsConverted++;
      return newline + (leadingSpaces || '') + '• ';
  });
  
  // Pattern 2: תחילת הטקסט + מקף + רווח
  const pattern2 = new RegExp(`^([\\t ]*)[${dashChars}]([\\t ]+)`, 'g');
  cleaned = cleaned.replace(pattern2, (match, leadingSpaces) => {
      bulletPointsConverted++;
      return (leadingSpaces || '') + '• ';
  });
  
  // Pattern 3: אחרי תגית HTML סוגרת (>) + מקף + רווח
  const pattern3 = new RegExp(`(>)([\\t ]*)[${dashChars}]([\\t ]+)`, 'g');
  cleaned = cleaned.replace(pattern3, (match, tag, leadingSpaces) => {
      bulletPointsConverted++;
      return tag + (leadingSpaces || '') + '• ';
  });
  
  if (bulletPointsConverted > 0) {
      changes.push({
          type: 'מקפים ➜ בולטים',
          count: bulletPointsConverted,
          description: 'מקף בתחילת שורה הפך ל-•',
          details: [{ from: '- טקסט', to: '• טקסט' }]
      });
  }
  
  if (finalGptDashesRemoved > 0) {
      // מוסיף לשינויים הקיימים או יוצר חדש
      const existingGptChange = changes.find(c => c.type === 'ניקוי מקפי GPT');
      if (existingGptChange) {
          existingGptChange.count += finalGptDashesRemoved;
      } else {
          changes.push({
              type: 'ניקוי מקפי GPT',
              count: finalGptDashesRemoved,
              description: 'הוסרו " - " (מקף עם רווחים)',
              details: [{ from: ' - ', to: '(הוסר)' }]
          });
      }
  }

  return {
      cleanedText: cleaned,
      changes: changes,
      totalChanges: changes.reduce((sum, c) => sum + c.count, 0),
      isModified: cleaned !== text,
      foreignWordsList: foreignWordsList
  };
}

/**
 * 🔧 פונקציית ניקוי ותיקון הטקסט
 * שומרת על מבנה ה-HTML המקורי!
 * 🛡️ כולל הגנה מלאה על SCRIPT, STYLE, PRE, CODE וכל התגיות (Attributes)
 */
function humanizeText(text, analysisResults) {
  let humanized = text;
  
  // =================================================================
  // 🛡️ שלב 1: הגנה על בלוקים שלמים
  // =================================================================
  const protectedBlocks = [];
  
  function protectBlock(tagName) {
      let safety = 0;
      while (safety < 1000) { 
          safety++;
          const regex = new RegExp(`<${tagName}[^>]*>[^]*?<\/${tagName}>`, 'i');
          const match = humanized.match(regex);
          
          if (!match) break;
          
          const fullBlock = match[0];
          const placeholder = `___PROTECTED_BLOCK_${tagName.toUpperCase()}_${protectedBlocks.length}___`;
          
          protectedBlocks.push({ placeholder: placeholder, content: fullBlock });
          humanized = humanized.replace(fullBlock, placeholder);
      }
  }
  
  protectBlock('script');
  protectBlock('style');
  protectBlock('pre');
  protectBlock('code');
  protectBlock('textarea');
  
  // 🔒 שמירת JSON-LD Schema (אם לא נתפס כבר ע"י script - ליתר ביטחון)
  // (קוד קצר שבודק אם נשאר משהו)
  const jsonLdBlocks = []; 

  // =================================================================
  // 🛡️ שלב 1.5: הגנה על רכיבי UI קצרים (כפתורים, כותרות, תוויות)
  // מונע מחיקת אימוג'ים שהם חלק מהעיצוב!
  // =================================================================
  
  function protectShortUI(tagName) {
      // מחפש תגיות שנסגרות מהר (עד 200 תווים) ולא מכילות תגית מאותו סוג בתוכן
      const regex = new RegExp(`<${tagName}\\b[^>]*>(?:(?!<${tagName}).){0,200}<\\/${tagName}>`, 'gi');
      
      humanized = humanized.replace(regex, function(match) {
          const placeholder = `___PROTECTED_UI_${tagName.toUpperCase()}_${protectedBlocks.length}___`;
          protectedBlocks.push({ placeholder: placeholder, content: match });
          return placeholder;
      });
  }

  // הגנה חדשה: אלמנטים עם CLASS (כמו div class="icon")
  function protectClassedUI(tagName) {
      // מחפש תגית שיש לה CLASS בתוך התגית הפותחת
      const regex = new RegExp(`<${tagName}\\b[^>]*class=['"][^'"]*['"][^>]*>(?:(?!<${tagName}).){0,200}<\\/${tagName}>`, 'gi');
      
      humanized = humanized.replace(regex, function(match) {
          const placeholder = `___PROTECTED_CLASSED_${tagName.toUpperCase()}_${protectedBlocks.length}___`;
          protectedBlocks.push({ placeholder: placeholder, content: match });
          return placeholder;
      });
  }
  
  // רשימת התגיות שבהן אימוג'י הוא בדרך כלל עיצובי
  const uiTags = ['button', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'th', 'label', 'legend', 'strong', 'b', 'small'];
  uiTags.forEach(tag => protectShortUI(tag));

  // תגיות גנריות - מוגנות רק אם יש להן CLASS
  const classedTags = ['div', 'span', 'p', 'i', 'em', 'mark'];
  classedTags.forEach(tag => protectClassedUI(tag));

  // =================================================================
  // 🛡️ שלב 2: הגנה על תגיות HTML (Attributes, Classes, IDs)
  // =================================================================
  const protectedTags = [];
  let tagIndex = 0;
  
  humanized = humanized.replace(/<[^>]+>/g, function(match) {
      const placeholder = `___PROTECTED_TAG_${tagIndex}___`;
      protectedTags.push({ placeholder: placeholder, content: match });
      tagIndex++;
      return placeholder;
  });

  // 🔒 שמירת WordPress shortcodes (חייב להיות אחרי הגנת תגיות כדי לא להחליף בתוכן)
  const shortcodes = [];
  const shortcodeMatches = humanized.match(/\[[^\]]+\]/g) || [];
  shortcodeMatches.forEach(function(sc, idx) {
    const placeholder = '___SHORTCODE_' + idx + '___';
    shortcodes.push({ placeholder: placeholder, content: sc });
    humanized = humanized.replace(sc, placeholder);
  });

  // =================================================================
  // 🔧 לוגיקה של השכתוב (עכשיו בטוחה - רצה רק על טקסט נקי!)
  // =================================================================

  const changes = [];
  
  // 0.5. 🔧 החלפת תווים מיוחדים של AI (גיבוי ל-basicClean)
  let specialCharsReplaced = 0;
  const specialCharDetails = [];
  
  aiSpecialCharsReplacements.forEach(function(pair) {
    const aiChar = pair[0];
    const humanChar = pair[1];
    if (humanized.indexOf(aiChar) > -1) {
      let count = 0;
      // מחליפים בזהירות רק אם לא בתוך מילה מוגנת (אבל הכל מוגן כבר!)
      // שימוש ב-split/join פשוט
      const parts = humanized.split(aiChar);
      if (parts.length > 1) {
          count = parts.length - 1;
          humanized = parts.join(humanChar);
          specialCharsReplaced += count;
          if (specialCharDetails.length < 10) {
            specialCharDetails.push({ from: aiChar, to: humanChar || '(הוסר)', count: count });
          }
      }
    }
  });
  
  if (specialCharsReplaced > 0) {
    changes.push({
      type: 'החלפת תווים מיוחדים',
      count: specialCharsReplaced,
      details: specialCharDetails,
      description: `הוחלפו ${specialCharsReplaced} תווים מיוחדים (דאשים, מרכאות, רווחים)`
    });
  }
  
  // 1. ניקוי תווים בשפות אחרות
  const foreignCharsRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u0400-\u04FF\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]/g;
  const foreignMatches = humanized.match(foreignCharsRegex);
  if (foreignMatches && foreignMatches.length > 0) {
    humanized = humanized.replace(foreignCharsRegex, '');
    changes.push({
      type: 'ניקוי שפות זרות',
      count: foreignMatches.length,
      description: 'הוסרו תווים בערבית/רוסית/סינית/יפנית'
    });
  }
  
  // 1.5. 🔧 ניקוי מרכאות מיותרות
  let quotesRemoved = 0;
  const quoteDetails = [];
  
  wordsAIQuotesUnnecessarily.forEach(word => {
    // תבניות שונות של מרכאות סביב המילה
    const patterns = [
      new RegExp(`"${word}"`, 'gi'),
      new RegExp(`"${word}"`, 'gi'),
      new RegExp(`״${word}״`, 'gi'),
      new RegExp(`'${word}'`, 'gi'),
      new RegExp(`׳${word}׳`, 'gi'),
      new RegExp(`«${word}»`, 'gi'),
      new RegExp(`„${word}"`, 'gi'),
      new RegExp(`"ה${word}"`, 'gi'),
      new RegExp(`"ה${word}"`, 'gi'),
      new RegExp(`״ה${word}״`, 'gi'),
    ];
    
    patterns.forEach(pattern => {
      const matches = humanized.match(pattern);
      if (matches) {
        matches.forEach(match => {
          const cleanWord = match.replace(/["״׳'"«»„""]/g, '');
          humanized = humanized.replace(match, cleanWord);
          quotesRemoved++;
          if (quoteDetails.length < 10) {
            quoteDetails.push({ from: match, to: cleanWord });
          }
        });
      }
    });
  });
  
  // הסרת מרכאות כפולות
  const doubleQuotePatterns = [
    { pattern: /""([^"]+)""/g, replacement: '"$1"' },
    { pattern: /״״([^״]+)״״/g, replacement: '״$1״' },
    { pattern: /""/g, replacement: '' },
    { pattern: /״״/g, replacement: '' },
    { pattern: /"\s+"/g, replacement: '' },
    { pattern: /"\s*$/gm, replacement: '' },
    { pattern: /^\s*"/gm, replacement: '' },
  ];
  
  doubleQuotePatterns.forEach(({ pattern, replacement }) => {
    const matches = humanized.match(pattern);
    if (matches) {
      quotesRemoved += matches.length;
      humanized = humanized.replace(pattern, replacement);
    }
  });
  
  // ספירת מרכאות כללית - אם יש יותר מדי, מסיר חלק
  const allQuotes = humanized.match(/["״׳'"«»„""]/g) || [];
  const wordCount = humanized.split(/\s+/).length;
  const quoteRatio = allQuotes.length / wordCount;
  
  // אם יותר מ-5% מהמילים במרכאות - יש בעיה
  if (quoteRatio > 0.05 && allQuotes.length > 10) {
    // מסיר מרכאות ממילים קצרות (פחות מ-4 אותיות)
    humanized = humanized.replace(/["״]([א-ת]{1,3})["״]/g, '$1');
    quotesRemoved += 5;
  }
  
  if (quotesRemoved > 0) {
    changes.push({
      type: 'ניקוי מרכאות מיותרות',
      count: quotesRemoved,
      details: quoteDetails,
      description: `הוסרו ${quotesRemoved} מרכאות מיותרות (סימן AI)`
    });
  }
  
  // 2. ניקוי או הפחתת אימוג'ים של AI
  let emojiCount = 0;
  aiEmojis.forEach(emoji => {
    const regex = new RegExp(emoji, 'g');
    const matches = humanized.match(regex);
    if (matches) {
      emojiCount += matches.length;
      // משאיר רק אחד מכל סוג (אם יש יותר מאחד)
      if (matches.length > 1) {
        // מסיר את כל ההופעות מלבד הראשונה
        let firstFound = false;
        humanized = humanized.replace(regex, (match) => {
          if (!firstFound) {
            firstFound = true;
            return match;
          }
          return '';
        });
      }
    }
  });
  
  // אם יש יותר מ-5 אימוג'ים - מסיר את כולם
  const totalEmojis = (humanized.match(/[\u{1F300}-\u{1F9FF}]/gu) || []).length;
  if (totalEmojis > 5) {
    humanized = humanized.replace(/[\u{1F300}-\u{1F9FF}]/gu, '');
    changes.push({
      type: 'ניקוי אימוג\'ים',
      count: totalEmojis,
      description: 'הוסרו אימוג\'ים מוגזמים'
    });
  } else if (emojiCount > 0) {
    changes.push({
      type: 'צמצום אימוג\'ים',
      count: emojiCount,
      description: 'צומצמו אימוג\'ים חוזרים'
    });
  }
  
  // 3. החלפת ביטויי AI בביטויים אנושיים - 🔧 רק המלצות, לא מחליף בפועל!
  let replacementCount = 0;
  const replacementDetails = [];
  
  // מיון לפי אורך (ארוך לקצר) כדי לזהות ביטויים ארוכים קודם
  const sortedPhrases = Object.keys(aiToHumanReplacements).sort((a, b) => b.length - a.length);
  
  sortedPhrases.forEach(aiPhrase => {
    const regex = new RegExp(aiPhrase, 'gi');
    const matches = humanized.match(regex);
    if (matches) {
      matches.forEach(() => {
        const replacement = randomPick(aiToHumanReplacements[aiPhrase]);
        // 🔧 לא מחליפים! רק מדווחים
        // humanized = humanized.replace(regex, replacement);
        replacementCount++;
        replacementDetails.push({
          from: aiPhrase,
          to: replacement || '(מומלץ להסיר)'
        });
      });
    }
  });
  
  if (replacementCount > 0) {
    changes.push({
      type: '💡 המלצה: החלפת ביטויי AI',
      count: replacementCount,
      details: replacementDetails.slice(0, 10), // רק 10 ראשונים
      description: `נמצאו ${replacementCount} ביטויים להחלפה (לא הוחלפו אוטומטית)`
    });
  }
  
  // 🆕 החלפת "אינגלוזים" (Anglicisms) - 🔧 רק המלצות!
  let anglicismsFixed = 0;
  const anglicismDetails = [];
  
  Object.keys(anglicismsMap).forEach(function(badTerm) {
    if (humanized.indexOf(badTerm) > -1) {
      const betterTerm = anglicismsMap[badTerm];
      const regex = new RegExp(badTerm, 'g');
      const matches = humanized.match(regex);
      if (matches) {
        anglicismsFixed += matches.length;
        // 🔧 לא מחליפים! רק מדווחים
        // humanized = humanized.replace(regex, betterTerm);
        anglicismDetails.push({ from: badTerm, to: betterTerm, count: matches.length });
      }
    }
  });

  if (anglicismsFixed > 0) {
    changes.push({
      type: '💡 המלצה: תיקון תרגמת (אינגלוז)',
      count: anglicismsFixed,
      details: anglicismDetails,
      description: 'נמצאו ביטויים מתורגמים מאנגלית (לא הוחלפו אוטומטית)'
    });
  }

  // 🆕 שבירת תבנית "בולד+נקודתיים" - 🔧 רק המלצות!
  // דוגמה: "מהירות: המערכת עובדת..." -> "לגבי המהירות, המערכת עובדת..."
  const listiclePattern = /(?:<b>|\*\*)([\wא-ת\s]{1,20})(?:<\/b>|\*\*):\s*/g;
  let listiclesBroken = 0;
  const listicleDetails = [];
  
  // 🔧 רק סופרים ומדווחים, לא מחליפים!
  let listicleMatch;
  const listicleRegex = /(?:<b>|\*\*)([\wא-ת\s]{1,20})(?:<\/b>|\*\*):\s*/g;
  while ((listicleMatch = listicleRegex.exec(humanized)) !== null) {
    listiclesBroken++;
    const term = listicleMatch[1];
    listicleDetails.push({ 
      from: listicleMatch[0].trim(), 
      to: `לגבי ה${term}, ...` 
    });
  }
  
  if (listiclesBroken > 0) {
    changes.push({
      type: '💡 המלצה: שבירת תבניות רשימה',
      count: listiclesBroken,
      details: listicleDetails.slice(0, 5),
      description: 'נמצא פורמט "מילה: הסבר" (לא שונה אוטומטית)'
    });
  }

  // 🆕 טיפול בפעלים סבילים נפוצים - 🔧 רק המלצות!
  const passiveReplacements = {
    'ניתן לראות': 'אפשר לראות',
    'מומלץ לבצע': 'כדאי לעשות',
    'יש לבחון': 'שווה לבדוק',
    'בוצע שימוש': 'השתמשנו',
    'נמצא כי': 'גילינו ש',
    'ידוע כי': 'כולם יודעים ש'
  };
  
  let passiveFixed = 0;
  const passiveDetails = [];
  Object.keys(passiveReplacements).forEach(function(passive) {
    if (humanized.indexOf(passive) > -1) {
      const active = passiveReplacements[passive];
      const regex = new RegExp(passive, 'g');
      const matches = humanized.match(regex);
      if (matches) {
        passiveFixed += matches.length;
        // 🔧 לא מחליפים! רק מדווחים
        // humanized = humanized.replace(regex, active);
        passiveDetails.push({ from: passive, to: active });
      }
    }
  });

  if (passiveFixed > 0) {
    changes.push({
      type: '💡 המלצה: הפיכת סביל לפעיל',
      count: passiveFixed,
      details: passiveDetails,
      description: 'נמצאו ניסוחים אקדמיים (לא שונו אוטומטית)'
    });
  }

  // 7. תיקון כפילויות לשוניות וקישורים כפולים 🆕 - 🔧 רק המלצות!
  let tautologiesFixed = 0;
  const tautologyDetails = [];
  
  // מיזוג מילונים לתיקון אחד
  const allTautologies = Object.assign({}, tautologiesMap, doubleConnectorsMap);
  
  Object.keys(allTautologies).forEach(function(bad) {
    if (humanized.indexOf(bad) > -1) {
      const good = allTautologies[bad];
      const regex = new RegExp(bad, 'g');
      const matches = humanized.match(regex);
      if (matches) {
        tautologiesFixed += matches.length;
        // 🔧 לא מחליפים! רק מדווחים
        // humanized = humanized.replace(regex, good);
        tautologyDetails.push({ from: bad, to: good, count: matches.length });
      }
    }
  });
  
  // זיהוי מעברים רובוטיים - 🔧 רק המלצות!
  let roboticTransFixed = 0;
  const roboticDetails = [];
  roboticTransitions.forEach(function(rt) {
    if (humanized.indexOf(rt) > -1) {
      const regex = new RegExp(rt, 'g');
      const matches = humanized.match(regex);
      if (matches) {
        roboticTransFixed += matches.length;
        // 🔧 לא מסירים! רק מדווחים
        // humanized = humanized.replace(regex, ''); 
        roboticDetails.push({ from: rt, to: '(מומלץ להסיר)' });
      }
    }
  });
  
  if (tautologiesFixed > 0 || roboticTransFixed > 0) {
    changes.push({
      type: '💡 המלצה: ניקוי תחביר רובוטי',
      count: tautologiesFixed + roboticTransFixed,
      details: [...tautologyDetails, ...roboticDetails].slice(0, 10),
      description: 'נמצאו כפילויות ומשפטי מעבר מלאכותיים (לא שונו אוטומטית)'
    });
  }

  // 8. הסרת "טיקים" של קלוד (Claude Detox) 🆕 - 🔧 רק המלצות!
  let claudeFixed = 0;
  const claudeDetails = [];
  claudeFingerprints.forEach(function(fp) {
    if (humanized.indexOf(fp) > -1) {
      const regex = new RegExp(fp, 'g');
      const matches = humanized.match(regex);
      if (matches) {
        claudeFixed += matches.length;
        // 🔧 לא מחליפים! רק מדווחים
        let suggestedReplacement = '(מומלץ להסיר)';
        if (fp.includes('מסע')) {
          suggestedReplacement = 'תהליך';
        } else if (fp.includes('לצלול')) {
          suggestedReplacement = 'להעמיק';
        } else if (fp.includes('האומנות שב')) {
          suggestedReplacement = 'הסוד של';
        } else if (fp.includes('לכל מטבע')) {
          suggestedReplacement = 'אבל יש גם צד שני';
        }
        claudeDetails.push({ from: fp, to: suggestedReplacement });
      }
    }
  });

  if (claudeFixed > 0) {
    changes.push({
      type: '💡 המלצה: ניקוי סגנון קלוד',
      count: claudeFixed,
      details: claudeDetails,
      description: 'נמצאו ביטויים פיוטיים וקלישאות של Claude (לא הוסרו אוטומטית)'
    });
  }

  // 9. גמילה מסופרלטיבים (Superlative Detox) 🆕 - 🔧 רק המלצות!
  let superlativesFixed = 0;
  const superlativeDetails = [];
  
  Object.keys(superlativesMap).forEach(function(sup) {
    if (humanized.indexOf(sup) > -1) {
      const regex = new RegExp(sup, 'g');
      const matches = humanized.match(regex);
      if (matches) {
        superlativesFixed += matches.length;
        // 🔧 לא מחליפים! רק מדווחים
        // humanized = humanized.replace(regex, superlativesMap[sup]);
        superlativeDetails.push({ from: sup, to: superlativesMap[sup] });
      }
    }
  });
  
  if (superlativesFixed > 0) {
    changes.push({
      type: '💡 המלצה: הפחתת הגזמות',
      count: superlativesFixed,
      description: 'נמצאו סופרלטיבים (לא הוחלפו אוטומטית)',
      details: superlativeDetails
    });
  }

  // 10. גיוון פיסוק (Punctuation Variety) ➖ 🆕
  // משנה את הלוגיקה: במקום להוסיף מקפים (שנראים כמו GPT), נוסיף סוגריים או נפצל משפטים
  // 🔥 תיקון: עובדים על כל פסקה בנפרד כדי לשמור על ירידות שורה!
  let punctuationVaried = 0;
  
  // מפצלים לפסקאות קודם (לפי ירידות שורה)
  const paragraphsForPunct = humanized.split(/(\n+)/); // שומר את ירידות השורה כאלמנטים נפרדים
  
  for (let pIdx = 0; pIdx < paragraphsForPunct.length; pIdx++) {
    // אם זה ירידת שורה - לא נוגעים
    if (/^\n+$/.test(paragraphsForPunct[pIdx])) continue;
    
    const sentences = paragraphsForPunct[pIdx].split('.');
    for (let i = 0; i < sentences.length; i++) {
      // זיהוי מקפי "סנדוויץ'" של GPT (מקף - הסבר - מקף) והסרתם
      // לדוגמה: "הפתרון - שהוא יעיל - עובד" -> "הפתרון שהוא יעיל עובד"
      // 🔥 כל מקף GPT מוסר לגמרי (לא מחליפים לפסיק!)
      if (sentences[i].includes(' - ')) {
         const dashCount = (sentences[i].match(/ - /g) || []).length;
         sentences[i] = sentences[i].replace(/ - /g, ' ');
         punctuationVaried += dashCount;
      }
    }
    paragraphsForPunct[pIdx] = sentences.join('.');
  }
  humanized = paragraphsForPunct.join(''); // מחבר הכל בחזרה כולל ירידות השורה

  if (punctuationVaried > 0) {
     changes.push({
      type: 'טיפול במקפים ופיסוק',
      count: punctuationVaried,
      description: 'הוסרו מקפי GPT ( - ) והוחלפו בפסיקים או הוסרו לגמרי'
    });
  }

  // 11. שבירת תבניות דידקטיות (Structure Fix) 🆕 - 🔧 רק המלצות!
  let structureFixed = 0;
  const structureDetails = [];
  
  // זיהוי "לסיכום" בסוף - רק מדווחים!
  const conclusionPatterns = ['לסיכום,', 'לסיכום:', 'לסיכום -', 'סיכומו של דבר,'];
  conclusionPatterns.forEach(p => {
    const lastIndex = humanized.lastIndexOf(p);
    if (lastIndex > humanized.length * 0.8) { // רק אם זה בסוף
      // 🔧 לא מחליפים! רק מדווחים
      structureFixed++;
      structureDetails.push({ from: p, to: 'בשורה התחתונה, / (להסיר)' });
    }
  });

  // זיהוי שאלות רטוריות דידקטיות - רק מדווחים!
  const rhetoricalPatterns = [
    { regex: /למה זה (חשוב|קורה)\? (כי|מכיוון ש)/g, replacement: 'הסיבה שזה $1 היא ש' },
    { regex: /איך (עושים|בודקים) את זה\? (באמצעות|על ידי)/g, replacement: 'הדרך ל$1 את זה היא $2' },
    { regex: /מה הפתרון\? (הפתרון הוא)/g, replacement: 'והפתרון הוא פשוט:' }
  ];

  rhetoricalPatterns.forEach(pat => {
    const matches = humanized.match(pat.regex);
    if (matches) {
       structureFixed += matches.length;
       // 🔧 לא מחליפים! רק מדווחים
       // humanized = humanized.replace(pat.regex, pat.replacement);
       matches.forEach(m => {
         structureDetails.push({ from: m, to: pat.replacement.replace(/\$\d/g, '...') });
       });
    }
  });

  if (structureFixed > 0) {
     changes.push({
      type: '💡 המלצה: שבירת תבניות דידקטיות',
      count: structureFixed,
      details: structureDetails.slice(0, 5),
      description: 'נמצאו כותרות סיכום ושאלות רטוריות (לא שונו אוטומטית)'
    });
  }

  // 12. הנמכת משלב (High Register Washing) 🆕 - 🔧 רק המלצות!
  // מזהה מילים "גבוהות" וממליץ על חלופות בשפה יומיומית
  let formalFixed = 0;
  const formalDetails = [];
  
  Object.keys(formalToCasualMap).forEach(term => {
    // בודק מילים שלמות בלבד
    const regex = new RegExp(`(?<![א-ת])${term}(?![א-ת])`, 'g');
    
    if (humanized.match(regex)) {
       const matches = humanized.match(regex);
       formalFixed += matches.length;
       // 🔧 לא מחליפים! רק מדווחים
       // humanized = humanized.replace(regex, formalToCasualMap[term]);
       formalDetails.push({ from: term, to: formalToCasualMap[term] });
    }
  });

  if (formalFixed > 0) {
     changes.push({
      type: '💡 המלצה: הנמכת משלב',
      count: formalFixed,
      description: 'נמצאו מילים גבוהות (לא הוחלפו אוטומטית)',
      details: formalDetails
    });
  }

  // 4. ניקוי רווחים כפולים שנוצרו - 🔥 תיקון: לא נוגעים בירידות שורה!
  // משתמשים ב-[^\S\n] במקום \s כדי לתפוס רווחים וטאבים אבל לא \n
  humanized = humanized.replace(/[^\S\n]{2,}/g, ' '); // רווחים כפולים (לא \n)
  humanized = humanized.replace(/[^\S\n]+([.,!?;:])/g, '$1'); // רווח לפני פיסוק
  humanized = humanized.replace(/([.,!?;:])[^\S\n]*([.,!?;:])/g, '$1'); // פיסוק כפול
  
  // 5. ניקוי שורות ריקות מיותרות
  humanized = humanized.replace(/\n{3,}/g, '\n\n');
  
  // 6. תיקון פיסוק בעייתי
  humanized = humanized.replace(/,\s*,/g, ',');
  humanized = humanized.replace(/\.\s*\./g, '.');
  humanized = humanized.replace(/^\s*[,.:;]\s*/gm, '');
  
  // 🔒 שחזור JSON-LD Schema
  jsonLdBlocks.forEach(function(block) {
    humanized = humanized.replace(block.placeholder, block.content);
  });
  
  // =================================================================
  // 🎨 הוספת מגע אנושי - 🔧 מבוטל! רק דיווח המלצות
  // =================================================================
  if (analysisResults) {
      // 🆕 שלב 1: בדיקה מה היה נוסף (בלי לשנות בפועל)
      const humanMarkersResult = injectHumanMarkers(humanized, analysisResults);
      // 🔧 לא משנים את הטקסט!
      // humanized = humanMarkersResult.text;
      
      if (humanMarkersResult.changesCount > 0) {
        changes.push({
          type: '💡 המלצה: הזרקת סמנים אנושיים',
          count: humanMarkersResult.changesCount,
          description: 'ניתן להוסיף ביטויים אנושיים (לא הוספו אוטומטית)',
          details: humanMarkersResult.changes
        });
      }
      
      // שלב 2: בדיקה מה היה נוסף (בלי לשנות בפועל)
      const humanTouchResult = addHumanTouches(humanized, analysisResults);
      // 🔧 לא משנים את הטקסט!
      // humanized = humanTouchResult.text;
      
      if (humanTouchResult.changesCount > 0) {
          changes.push({
              type: '💡 המלצה: מגע אנושי',
              count: humanTouchResult.changesCount,
              description: 'ניתן להוסיף ביטויים אנושיים (לא הוספו אוטומטית)',
              details: humanTouchResult.appliedChanges
          });
      }
  }

  // 🔒 שחזור WordPress shortcodes
  shortcodes.forEach(function(sc) {
    humanized = humanized.replace(sc.placeholder, sc.content);
  });
  
  // =================================================================
  // 🛡️ שחזור בלוקים מוגנים + תגיות (בסדר הפוך: קודם תגיות, אז בלוקים - ומהסוף להתחלה!)
  // חובה להשתמש ב-reverse() כדי לפתוח קינונים (Outer משחרר את Inner)
  // =================================================================
  
  // 1. שחזור תגיות HTML (attributes וכד')
  [...protectedTags].reverse().forEach(tag => {
      humanized = humanized.replace(tag.placeholder, tag.content);
  });

  // 2. שחזור בלוקים שלמים (סקריפטים, סטיילים)
  [...protectedBlocks].reverse().forEach(block => {
      humanized = humanized.replace(block.placeholder, block.content);
  });

  return {
    originalText: text,
    humanizedText: humanized.trim(),
    changes: changes,
    totalChanges: changes.reduce(function(sum, c) { return sum + c.count; }, 0),
    isModified: humanized.trim() !== text.trim()
  };
}

/**
 * 🔧 ביטויים אישיים להוספה
 */
const personalExpressions = [
  "לדעתי, ", "אני חושב ש", "מניסיוני, ", "מה שכיף הוא ש",
  "הנה הקטע: ", "אצלי זה עבד ככה: ", "לפי מה שאני יודע, ",
  "מה שלמדתי הוא ש", "אישית, ", "בעיניי, ", "לטעמי, "
];

/**
 * 🔧 משפטים קצרים להזרקה
 */
const shortSentences = [
  "פשוט.", "ברור.", "זהו.", "בדיוק.", "נכון?", "הגיוני, לא?",
  "עובד מצוין.", "ממש.", "בול.", "קל.", "פשוט ככה.", "זה הכל.",
  "לא מסובך.", "עובד.", "מומלץ.", "שווה.", "בקיצור.", "סוף."
];

/**
 * 🔧 סלנג ישראלי להוספה
 */
const israeliSlang = [
  "תכלס", "וואלה", "סבבה", "אחלה", "יאללה", "בכיף",
  "חבל על הזמן", "פצצה", "מטורף", "אש", "סוף הדרך",
  "לא יאומן", "מעולה", "בומבה", "חזק"
];

/**
 * 🔧 פתיחות משפט חלופיות לגיוון
 */
// 🔥 תיקון: הסרנו " - " מכל ההחלפות כי זה סימן GPT!
const sentenceStarterReplacements = {
  // אם מתחיל באותו אופן יותר מפעמיים
  "חשוב": ["שווה לדעת ש", "אגב, ", "עוד דבר:", "טיפ: ", "הנה קטע:"],
  "ניתן": ["אפשר ", "דרך אחת היא ", "יש אפשרות ", "אופציה טובה: "],
  "יש": ["קיימת אפשרות ", "אפשר למצוא ", "יש לנו ", "קיים "],
  "זה": ["הדבר הזה ", "העניין ", "הנושא ", "הקטע "],
  "אם": ["במקרה ש", "כש", "ברגע ש", "אם וכאשר "],
  "כאשר": ["כש", "ברגע ש", "בזמן ש", "בעת ש"],
  "בנוסף": ["וגם ", "ועוד:", "מעבר לזה, ", "גם ככה "],
  "לכן": ["אז ", "ולכן ", "בגלל זה ", "משום כך "],
  "עם זאת": ["אבל ", "ובכל זאת ", "ועדיין ", "למרות זאת "],
  "המחקר": ["מחקרים ", "לפי מחקרים ", "נמצא ש", "גילו ש"],
  "ישנם": ["יש ", "קיימים ", "אפשר למצוא ", "נמצאים "],
  "ישנה": ["יש ", "קיימת ", "נמצאת ", "אפשר למצוא "]
};

/**
 * 🆕 הזרקת סמנים אנושיים חזקים - להורדת ציון מתחת ל-30
 * מוסיף ביטויים שהאלגוריתם מזהה כ"אנושיים" ונותן עליהם בונוס
 */
function injectHumanMarkers(text, analysisResults) {
  let enhanced = text;
  const changes = [];
  
  // רק אם הציון גבוה מ-40 - שווה להוסיף סמנים אנושיים
  if (analysisResults.rawScore < 40) {
    return { text: enhanced, changes: [], changesCount: 0 };
  }
  
  // 🎯 סמנים אנושיים חזקים שנותנים בונוס גדול - 30+ אפשרויות!
  const strongHumanMarkers = [
    // ביטויי דעה אישית
    "לדעתי, ", "לטעמי, ", "בעיני, ", "מבחינתי, ", "לפי דעתי, ",
    "אני חושב ש", "אני מאמין ש", "אני סבור ש", "אני משוכנע ש", "אני בטוח ש",
    "נראה לי ש", "נדמה לי ש", "מרגיש לי ש", "יוצא לי ש", "מסתבר לי ש",
    
    // ביטויי ניסיון אישי
    "מניסיוני, ", "מהניסיון שלי, ", "לפי הניסיון שלי, ", "מה שלמדתי זה ש", "מה שגיליתי זה ש",
    "קרה לי פעם ש", "היה לי מקרה ש", "נתקלתי פעם ב", "ראיתי פעם ש", "שמעתי פעם ש",
    "גיליתי ש", "למדתי ש", "הבנתי ש", "שמתי לב ש", "הרגשתי ש",
    
    // ביטויי קיצור/תכלס
    "בקיצור, ", "תכלס, ", "בתכלס, ", "בגדול, ", "בעצם, ",
    "בשורה התחתונה, ", "בסופו של דבר, ", "בסיכום, ", "בתמצית, ", "במילים פשוטות, ",
    
    // ביטויי אמפתיה/קשר
    "אני מבין ש", "אני יודע ש", "אני מכיר את זה, ", "אני מזדהה עם זה, ", "גם לי זה קרה, ",
    "הרבה אנשים שואלים, ", "שאלה נפוצה היא, ", "משהו שכדאי לדעת, ", "טיפ קטן: ", "סוד קטן: ",
    
    // ביטויי הפתעה/גילוי
    "וואלה, ", "מעניין ש", "מפתיע ש", "מדהים ש", "לא האמנתי ש",
    "הייתי מופתע לגלות ש", "התפלאתי לראות ש", "לא ציפיתי ש", "לא חשבתי ש", "לא ידעתי ש",
    
    // ביטויי המלצה אישית
    "אני ממליץ ", "אני מציע ", "הייתי מציע ", "הייתי ממליץ ", "שווה לנסות ",
    "כדאי לבדוק ", "שווה לבדוק ", "תנסו את ", "תבדקו את ", "קחו בחשבון ש"
  ];
  
  // 🎯 החלפות של ביטויים רשמיים לאנושיים - עם 30+ חלופות לכל ביטוי!
  // פונקציית עזר לבחירה אקראית ממערך
  function pickRandom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }
  
  const formalToHumanMulti = {
    // ============================================================
    // ביטויי Claude/GPT מובהקים - חייבים להחליף! (30+ חלופות)
    // ============================================================
    "כמובן": [
      "ברור", "ברור ש", "ברור לגמרי", "בטח", "בטח ש", "נכון", "נכון מאוד", 
      "זה ברור", "מובן מאליו", "לא צריך להסביר", "כן", "בוודאי", "מאה אחוז",
      "זה ידוע", "אין ספק", "בלי שאלה", "אכן", "באמת", "לגמרי", "מוסכם",
      "זה פשוט", "זה ברור לכולם", "זה ידוע לכל", "אין מה להתווכח", "זה מקובל",
      "כולם יודעים", "ברור כשמש", "פשוט", "זה עובדה", "אין על מה לדבר"
    ],
    "נראה כי": [
      "נראה ש", "זה נראה כאילו", "אפשר לראות ש", "רואים ש", "ברור ש",
      "נדמה ש", "מסתבר ש", "יוצא ש", "מתברר ש", "אפשר להבין ש",
      "זה נראה כמו", "לפי מה שרואים", "ממה שרואים", "על פניו", "לכאורה",
      "זה מראה ש", "זה מעיד ש", "מזה עולה ש", "אפשר להסיק ש", "זה מלמד ש",
      "זה מצביע על", "מתקבל הרושם ש", "זה משדר ש", "מזה משתמע ש", "ניכר ש",
      "בולט ש", "ניתן לראות ש", "ניתן להבחין ש", "אפשר לשים לב ש", "שמים לב ש"
    ],
    "כדאי לזכור ש": [
      "טוב לזכור ש", "שווה לזכור ש", "חשוב לזכור ש", "אל תשכחו ש", "תזכרו ש",
      "כדאי לשים לב ש", "שימו לב ש", "זכרו ש", "אל תשכח ש", "תשים לב ש",
      "נקודה חשובה:", "דבר שצריך לזכור:", "משהו שכדאי לדעת:", "טיפ:", "הערה:",
      "רגע לפני שממשיכים:", "עוד משהו:", "בנוסף:", "גם חשוב:", "ועוד דבר:",
      "לא לשכוח ש", "תמיד תזכרו ש", "קחו בחשבון ש", "שימו על הראדר ש", "תנו דעתכם ש",
      "אגב,", "דרך אגב,", "למי שלא יודע:", "למי ששכח:", "תזכורת:"
    ],
    "חשוב לציין ש": [
      "שווה לדעת ש", "כדאי לדעת ש", "טוב לדעת ש", "חשוב לדעת ש", "צריך לדעת ש",
      "משהו שכדאי לדעת:", "נקודה חשובה:", "שימו לב:", "הערה:", "טיפ:",
      "עוד משהו:", "גם חשוב לציין:", "ועוד:", "בנוסף:", "מעבר לזה:",
      "אגב,", "דרך אגב,", "למי שלא יודע:", "למי שמתעניין:", "למי שרוצה לדעת:",
      "עוד דבר:", "משהו נוסף:", "וגם:", "ובנוסף:", "וחוץ מזה:",
      "תדעו ש", "דעו ש", "קחו לידיעה ש", "שימו לב לזה:", "זה חשוב:"
    ],
    "מנקודת מבט": [
      "מהזווית של", "מהכיוון של", "מצד", "מהפרספקטיבה של", "אם מסתכלים מ",
      "כשרואים את זה מ", "מבחינת", "לפי", "על פי", "בעיני",
      "לדעת", "לפי הראייה של", "מהמקום של", "מנקודת הראות של", "בראייה של",
      "אם שואלים את", "לפי דעת", "לטעם", "בתפיסת", "בעולם של",
      "מהעמדה של", "מהעמדת", "בגישת", "לפי גישת", "בתורת",
      "אם מסתכלים דרך", "דרך העיניים של", "בפריזמה של", "מזווית הראייה של", "מהצד של"
    ],
    "כחלק מהתהליך": [
      "בתהליך", "במהלך", "כשעושים את זה", "תוך כדי", "בזמן",
      "בשלב הזה", "בנקודה הזו", "פה", "כאן", "עכשיו",
      "בחלק הזה", "בשלב", "באמצע", "תוך כדי התהליך", "במסגרת",
      "כשמבצעים", "כשעוברים", "כשמתקדמים", "בדרך", "לאורך הדרך",
      "בהמשך", "בהמשך הדרך", "תוך כדי עבודה", "בעבודה", "בפועל",
      "בביצוע", "בעשייה", "כשעושים", "כשמיישמים", "ביישום"
    ],
    "מעניין לציין כי": [
      "מעניין ש", "מעניין לדעת ש", "מעניין לראות ש", "מפתיע ש", "מפליא ש",
      "הפתעה:", "משהו מעניין:", "דבר מעניין:", "עובדה מעניינת:", "נקודה מעניינת:",
      "אגב,", "דרך אגב,", "בצד:", "הערה:", "שימו לב:",
      "וואו,", "מדהים ש", "מרתק ש", "מרשים ש", "נחמד לראות ש",
      "קטע מעניין:", "עניין מעניין:", "משהו ששווה לדעת:", "פרט מעניין:", "נתון מעניין:",
      "מה שמעניין זה ש", "הדבר המעניין הוא ש", "מה שכדאי לדעת:", "מה שמפתיע:", "מה שמדהים:"
    ],
    "חשוב להבין ש": [
      "צריך להבין ש", "חייבים להבין ש", "כדאי להבין ש", "שווה להבין ש", "טוב להבין ש",
      "תבינו ש", "תנסו להבין ש", "הבינו ש", "קחו בחשבון ש", "שימו לב ש",
      "העניין הוא ש", "הנקודה היא ש", "הדבר הוא ש", "המצב הוא ש", "העובדה היא ש",
      "פשוט תבינו:", "בקיצור:", "בתכלס:", "בפשטות:", "במילים פשוטות:",
      "מה שצריך להבין:", "מה שחשוב להבין:", "הדבר החשוב להבין:", "נקודת המפתח:", "הקטע הוא ש",
      "בסופו של דבר:", "בשורה התחתונה:", "המסקנה:", "התובנה:", "הלקח:"
    ],
    "יש לזכור כי": [
      "טוב לזכור ש", "כדאי לזכור ש", "שווה לזכור ש", "חשוב לזכור ש", "צריך לזכור ש",
      "אל תשכחו ש", "תזכרו ש", "זכרו ש", "אל תשכח ש", "תשים לב ש",
      "נקודה לזכור:", "דבר לזכור:", "משהו לזכור:", "תזכורת:", "הערה:",
      "לא לשכוח:", "תמיד לזכור:", "קחו בחשבון:", "שימו על הראדר:", "תנו דעתכם:",
      "עוד משהו:", "גם חשוב:", "ועוד דבר:", "בנוסף:", "מעבר לזה:",
      "אגב,", "דרך אגב,", "למי שלא יודע:", "למי ששכח:", "רגע,"
    ],
    "יש לקחת בחשבון": [
      "צריך לזכור", "צריך לקחת בחשבון", "כדאי לזכור", "שווה לזכור", "חשוב לזכור",
      "תזכרו", "קחו בחשבון", "שימו לב", "אל תשכחו", "תשימו לב",
      "נקודה חשובה:", "דבר חשוב:", "משהו לזכור:", "הערה:", "טיפ:",
      "עוד משהו:", "גם חשוב:", "ועוד דבר:", "בנוסף:", "מעבר לזה:",
      "לא לשכוח:", "תמיד לזכור:", "שימו על הראדר:", "תנו דעתכם:", "קחו לתשומת לב:",
      "אגב,", "דרך אגב,", "למי שלא יודע:", "למי ששכח:", "רגע,"
    ],
    
    // ============================================================
    // פירושו/כלומר - 30+ חלופות!
    // ============================================================
    "פירושו": [
      "זה אומר", "כלומר", "בעצם", "במילים אחרות", "זאת אומרת",
      "הכוונה היא", "פשוט", "בפשטות", "בקיצור", "בתכלס",
      "מה זה אומר?", "מה הכוונה?", "מה המשמעות?", "בעברית:", "בפשטות:",
      "אז מה זה?", "אז בעצם", "ובעצם", "שזה אומר", "וזה אומר",
      "דהיינו", "היינו", "כלומר:", "זה בעצם", "וזה בעצם",
      "המשמעות:", "הפירוש:", "התרגום:", "בתרגום חופשי:", "במילים פשוטות:"
    ],
    "פירושו ש": [
      "זה אומר ש", "כלומר ש", "בעצם ש", "במילים אחרות,", "זאת אומרת ש",
      "הכוונה היא ש", "פשוט ש", "בפשטות,", "בקיצור,", "בתכלס,",
      "מה זה אומר? ש", "מה הכוונה? ש", "בעברית:", "בפשטות:", "בתרגום:",
      "אז מה זה אומר? ש", "אז בעצם,", "ובעצם,", "שזה אומר ש", "וזה אומר ש",
      "דהיינו,", "היינו,", "כלומר:", "זה בעצם אומר ש", "וזה בעצם אומר ש",
      "המשמעות היא ש", "הפירוש הוא ש", "התרגום הוא:", "במילים פשוטות:", "בעברית פשוטה:"
    ],
    "במילים אחרות": [
      "בעצם", "כלומר", "זאת אומרת", "פשוט", "בפשטות",
      "בקיצור", "בתכלס", "בעברית", "במילים פשוטות", "בשפה פשוטה",
      "אחרת:", "בניסוח אחר:", "בגרסה פשוטה:", "בתרגום:", "בתרגום חופשי:",
      "מה זה אומר?", "מה הכוונה?", "מה המשמעות?", "הסבר:", "פירוש:",
      "אז בעצם", "ובעצם", "זה בעצם", "וזה בעצם", "פשוט לומר:",
      "בגדול:", "בשורה התחתונה:", "בסופו של דבר:", "בסיכום:", "בתמצית:"
    ],
    "כלומר": [
      "זאת אומרת", "בעצם", "פשוט", "בפשטות", "במילים אחרות",
      "בקיצור", "בתכלס", "בעברית", "במילים פשוטות", "בשפה פשוטה",
      "אחרת:", "בניסוח אחר:", "בגרסה פשוטה:", "בתרגום:", "בתרגום חופשי:",
      "מה זה אומר?", "מה הכוונה?", "מה המשמעות?", "הסבר:", "פירוש:",
      "אז בעצם", "ובעצם", "זה בעצם", "וזה בעצם", "פשוט לומר:",
      "בגדול:", "בשורה התחתונה:", "בסופו של דבר:", "בסיכום:", "בתמצית:"
    ],
    
    // ============================================================
    // מילות קישור רשמיות - 30+ חלופות!
    // ============================================================
    "באופן כללי": [
      "בגדול", "בכללי", "בדרך כלל", "לרוב", "ברוב המקרים",
      "בסך הכל", "בממוצע", "באופן טיפוסי", "בדרך כלל", "בנורמה",
      "רוב הזמן", "ברוב הפעמים", "הרבה פעמים", "בדרך כלל", "בשגרה",
      "בעיקרון", "בבסיס", "ביסוד", "בתשתית", "בשורש",
      "אם לסכם:", "אם להכליל:", "בהכללה:", "באופן גורף:", "בכלליות:",
      "בראייה רחבה:", "בתמונה הגדולה:", "במבט על:", "מלמעלה:", "בפרספקטיבה:"
    ],
    "לסיכום": [
      "בקיצור", "בתמצית", "בסיכום", "בשורה התחתונה", "בסופו של דבר",
      "אז בגדול", "אז בעצם", "אז ככה", "אז זהו", "אז מה יוצא?",
      "המסקנה:", "התוצאה:", "השורה התחתונה:", "הסיכום:", "התמצית:",
      "לסיום:", "בסיום:", "לפני שמסיימים:", "ולסיום:", "ובסיום:",
      "מה למדנו?", "מה יוצא מזה?", "מה המסקנה?", "מה התוצאה?", "מה השורה התחתונה?",
      "אז מה?", "אז מה עכשיו?", "אז מה הלאה?", "ומה עכשיו?", "ומה הלאה?"
    ],
    "בהחלט": [
      "בטח", "בוודאי", "ודאי", "בהחלט", "לגמרי",
      "מאה אחוז", "בלי ספק", "בלי שאלה", "ללא ספק", "אין ספק",
      "כן", "נכון", "בדיוק", "ממש", "לחלוטין",
      "זה בטוח", "זה ודאי", "זה ברור", "אין מה לדבר", "אין על מה לדבר",
      "בלי שום ספק", "בלי שום שאלה", "בהחלט כן", "בוודאות", "בביטחון",
      "בפירוש", "באופן מוחלט", "באופן ברור", "באופן ודאי", "באופן חד משמעי"
    ],
    "ללא ספק": [
      "בלי שאלה", "בלי ספק", "אין ספק", "ברור", "ברור לגמרי",
      "בטח", "בוודאי", "ודאי", "מאה אחוז", "בהחלט",
      "זה ברור", "זה ודאי", "זה בטוח", "אין מה לדבר", "אין על מה לדבר",
      "בלי שום ספק", "בלי שום שאלה", "בהחלט כן", "בוודאות", "בביטחון",
      "בפירוש", "באופן מוחלט", "באופן ברור", "באופן ודאי", "באופן חד משמעי",
      "לגמרי", "לחלוטין", "ממש", "בדיוק", "נכון"
    ],
    "יתרה מזאת": [
      "ועוד משהו", "ומעבר לזה", "וחוץ מזה", "ובנוסף", "וגם",
      "ויותר מזה", "ומה שיותר חשוב", "ומה שיותר מעניין", "ומה שיותר משמעותי", "ומה שיותר רלוונטי",
      "ועוד:", "ובנוסף:", "וגם:", "ומעבר:", "וחוץ:",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "וזה לא הכל:", "וזה עוד לא הכל:", "ויש עוד:", "ויש יותר:", "ויש משהו נוסף:",
      "אבל רגע,", "אבל זה לא הכל,", "אבל יש עוד,", "ורגע,", "ועוד רגע,"
    ],
    "מעבר לכך": [
      "חוץ מזה", "ובנוסף", "וגם", "ועוד", "ומעבר לזה",
      "ויותר מזה", "ומה שיותר חשוב", "ומה שיותר מעניין", "ומה שיותר משמעותי", "ומה שיותר רלוונטי",
      "ועוד:", "ובנוסף:", "וגם:", "ומעבר:", "וחוץ:",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "וזה לא הכל:", "וזה עוד לא הכל:", "ויש עוד:", "ויש יותר:", "ויש משהו נוסף:",
      "אבל רגע,", "אבל זה לא הכל,", "אבל יש עוד,", "ורגע,", "ועוד רגע,"
    ],
    "בנוסף לכך": [
      "ועוד", "וגם", "ובנוסף", "ומעבר לזה", "וחוץ מזה",
      "ויותר מזה", "ומה שיותר חשוב", "ומה שיותר מעניין", "ומה שיותר משמעותי", "ומה שיותר רלוונטי",
      "ועוד:", "ובנוסף:", "וגם:", "ומעבר:", "וחוץ:",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "וזה לא הכל:", "וזה עוד לא הכל:", "ויש עוד:", "ויש יותר:", "ויש משהו נוסף:",
      "אבל רגע,", "אבל זה לא הכל,", "אבל יש עוד,", "ורגע,", "ועוד רגע,"
    ],
    "כמו כן": [
      "וגם", "ובנוסף", "ועוד", "ומעבר לזה", "וחוץ מזה",
      "גם", "בנוסף", "עוד", "מעבר לזה", "חוץ מזה",
      "ועוד:", "ובנוסף:", "וגם:", "ומעבר:", "וחוץ:",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "וזה לא הכל:", "וזה עוד לא הכל:", "ויש עוד:", "ויש יותר:", "ויש משהו נוסף:",
      "אבל רגע,", "אבל זה לא הכל,", "אבל יש עוד,", "ורגע,", "ועוד רגע,"
    ],
    "לפיכך": [
      "אז", "ולכן", "לכן", "בגלל זה", "משום כך",
      "ואז", "וככה", "ומכאן", "ומזה", "ולכן גם",
      "אז מה?", "אז מה יוצא?", "אז מה המסקנה?", "אז מה עושים?", "אז מה הלאה?",
      "ולכן:", "ומכאן:", "ומזה:", "ובגלל זה:", "ומשום כך:",
      "התוצאה:", "המסקנה:", "השורה התחתונה:", "הסיכום:", "התמצית:",
      "בשורה התחתונה:", "בסופו של דבר:", "בסיכום:", "בתמצית:", "בקיצור:"
    ],
    "משום כך": [
      "בגלל זה", "לכן", "ולכן", "אז", "ואז",
      "ולכן גם", "ובגלל זה", "ומשום כך", "ומכאן", "ומזה",
      "אז מה?", "אז מה יוצא?", "אז מה המסקנה?", "אז מה עושים?", "אז מה הלאה?",
      "ולכן:", "ומכאן:", "ומזה:", "ובגלל זה:", "ומשום כך:",
      "התוצאה:", "המסקנה:", "השורה התחתונה:", "הסיכום:", "התמצית:",
      "בשורה התחתונה:", "בסופו של דבר:", "בסיכום:", "בתמצית:", "בקיצור:"
    ],
    "יש לציין": [
      "שווה לציין", "כדאי לציין", "חשוב לציין", "טוב לציין", "ראוי לציין",
      "שווה לדעת", "כדאי לדעת", "חשוב לדעת", "טוב לדעת", "ראוי לדעת",
      "שימו לב:", "הערה:", "טיפ:", "נקודה:", "פרט:",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "אגב,", "דרך אגב,", "למי שלא יודע:", "למי שמתעניין:", "למי שרוצה לדעת:",
      "תדעו ש", "דעו ש", "קחו לידיעה ש", "שימו לב לזה:", "זה חשוב:"
    ],
    "יחד עם זאת": [
      "אבל", "אך", "עם זאת", "למרות זאת", "בכל זאת",
      "ובכל זאת", "ועדיין", "ולמרות זאת", "ועם זאת", "ואף על פי כן",
      "אבל רגע,", "אבל שנייה,", "אבל מצד שני,", "אבל יש גם,", "אבל צריך לזכור,",
      "מצד שני,", "מהצד השני,", "בצד השני,", "מנגד,", "לעומת זאת,",
      "אבל:", "אך:", "עם זאת:", "למרות זאת:", "בכל זאת:",
      "ועדיין:", "ולמרות:", "ובכל אופן:", "ובכל מקרה:", "ובכל זאת:"
    ],
    "אף על פי כן": [
      "בכל זאת", "ובכל זאת", "ועדיין", "ולמרות זאת", "ועם זאת",
      "אבל", "אך", "עם זאת", "למרות זאת", "בכל אופן",
      "אבל רגע,", "אבל שנייה,", "אבל מצד שני,", "אבל יש גם,", "אבל צריך לזכור,",
      "מצד שני,", "מהצד השני,", "בצד השני,", "מנגד,", "לעומת זאת,",
      "ועדיין:", "ולמרות:", "ובכל אופן:", "ובכל מקרה:", "ובכל זאת:",
      "למרות הכל,", "למרות הכל:", "בסופו של דבר,", "בסוף,", "בסוף:"
    ],
    "לאור זאת": [
      "בגלל זה", "לכן", "ולכן", "אז", "ואז",
      "ולכן גם", "ובגלל זה", "ומשום כך", "ומכאן", "ומזה",
      "אז מה?", "אז מה יוצא?", "אז מה המסקנה?", "אז מה עושים?", "אז מה הלאה?",
      "ולכן:", "ומכאן:", "ומזה:", "ובגלל זה:", "ומשום כך:",
      "התוצאה:", "המסקנה:", "השורה התחתונה:", "הסיכום:", "התמצית:",
      "בשורה התחתונה:", "בסופו של דבר:", "בסיכום:", "בתמצית:", "בקיצור:"
    ],
    "מאידך גיסא": [
      "מצד שני", "מהצד השני", "בצד השני", "מנגד", "לעומת זאת",
      "אבל", "אך", "עם זאת", "למרות זאת", "בכל זאת",
      "אבל רגע,", "אבל שנייה,", "אבל מצד שני,", "אבל יש גם,", "אבל צריך לזכור,",
      "מצד שני,", "מהצד השני,", "בצד השני,", "מנגד,", "לעומת זאת,",
      "ומצד שני:", "ומהצד השני:", "ובצד השני:", "ומנגד:", "ולעומת זאת:",
      "בניגוד לזה,", "בניגוד לכך,", "להיפך,", "ההיפך,", "בהיפוך,"
    ],
    "יתר על כן": [
      "ויותר מזה", "ומעבר לזה", "וחוץ מזה", "ובנוסף", "וגם",
      "ועוד משהו", "ומה שיותר חשוב", "ומה שיותר מעניין", "ומה שיותר משמעותי", "ומה שיותר רלוונטי",
      "ועוד:", "ובנוסף:", "וגם:", "ומעבר:", "וחוץ:",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "וזה לא הכל:", "וזה עוד לא הכל:", "ויש עוד:", "ויש יותר:", "ויש משהו נוסף:",
      "אבל רגע,", "אבל זה לא הכל,", "אבל יש עוד,", "ורגע,", "ועוד רגע,"
    ],
    
    // ============================================================
    // ביטויים גנריים - 30+ חלופות!
    // ============================================================
    "קיימים מספר": [
      "יש כמה", "יש מספר", "יש הרבה", "יש כל מיני", "יש שונים",
      "אפשר למצוא כמה", "אפשר למצוא מספר", "אפשר למצוא הרבה", "אפשר למצוא שונים", "אפשר למצוא כל מיני",
      "נמצאים כמה", "נמצאים מספר", "נמצאים הרבה", "נמצאים שונים", "נמצאים כל מיני",
      "ישנם כמה", "ישנם מספר", "ישנם הרבה", "ישנם שונים", "ישנם כל מיני",
      "קיימים כמה", "קיימים הרבה", "קיימים שונים", "קיימים כל מיני", "קיימים מגוון",
      "יש לנו כמה", "יש לנו מספר", "יש לנו הרבה", "יש לנו שונים", "יש לנו כל מיני"
    ],
    "קיימות מספר": [
      "יש כמה", "יש מספר", "יש הרבה", "יש כל מיני", "יש שונות",
      "אפשר למצוא כמה", "אפשר למצוא מספר", "אפשר למצוא הרבה", "אפשר למצוא שונות", "אפשר למצוא כל מיני",
      "נמצאות כמה", "נמצאות מספר", "נמצאות הרבה", "נמצאות שונות", "נמצאות כל מיני",
      "ישנן כמה", "ישנן מספר", "ישנן הרבה", "ישנן שונות", "ישנן כל מיני",
      "קיימות כמה", "קיימות הרבה", "קיימות שונות", "קיימות כל מיני", "קיימות מגוון",
      "יש לנו כמה", "יש לנו מספר", "יש לנו הרבה", "יש לנו שונות", "יש לנו כל מיני"
    ],
    "ישנם מספר": [
      "יש כמה", "יש מספר", "יש הרבה", "יש כל מיני", "יש שונים",
      "אפשר למצוא כמה", "אפשר למצוא מספר", "אפשר למצוא הרבה", "אפשר למצוא שונים", "אפשר למצוא כל מיני",
      "נמצאים כמה", "נמצאים מספר", "נמצאים הרבה", "נמצאים שונים", "נמצאים כל מיני",
      "קיימים כמה", "קיימים מספר", "קיימים הרבה", "קיימים שונים", "קיימים כל מיני",
      "יש לנו כמה", "יש לנו מספר", "יש לנו הרבה", "יש לנו שונים", "יש לנו כל מיני",
      "ניתן למצוא כמה", "ניתן למצוא מספר", "ניתן למצוא הרבה", "ניתן למצוא שונים", "ניתן למצוא כל מיני"
    ],
    "ישנן מספר": [
      "יש כמה", "יש מספר", "יש הרבה", "יש כל מיני", "יש שונות",
      "אפשר למצוא כמה", "אפשר למצוא מספר", "אפשר למצוא הרבה", "אפשר למצוא שונות", "אפשר למצוא כל מיני",
      "נמצאות כמה", "נמצאות מספר", "נמצאות הרבה", "נמצאות שונות", "נמצאות כל מיני",
      "קיימות כמה", "קיימות מספר", "קיימות הרבה", "קיימות שונות", "קיימות כל מיני",
      "יש לנו כמה", "יש לנו מספר", "יש לנו הרבה", "יש לנו שונות", "יש לנו כל מיני",
      "ניתן למצוא כמה", "ניתן למצוא מספר", "ניתן למצוא הרבה", "ניתן למצוא שונות", "ניתן למצוא כל מיני"
    ],
    "מגוון רחב של": [
      "הרבה סוגים של", "המון סוגים של", "כל מיני", "מלא", "שפע של",
      "אוסף של", "מבחר של", "בחירה של", "סלקציה של", "קולקציה של",
      "הרבה", "המון", "מלא", "שפע", "עושר של",
      "מגוון של", "מגוון גדול של", "מגוון עצום של", "מגוון מרשים של", "מגוון מדהים של",
      "אפשרויות רבות של", "אופציות רבות של", "בחירות רבות של", "חלופות רבות של", "דרכים רבות של",
      "סוגים שונים של", "סוגים רבים של", "סוגים מגוונים של", "סוגים מרובים של", "סוגים מרשימים של"
    ],
    "מספר רב של": [
      "הרבה", "המון", "מלא", "שפע של", "עושר של",
      "כמות גדולה של", "כמות עצומה של", "כמות מרשימה של", "כמות מדהימה של", "כמות נכבדה של",
      "מספר גדול של", "מספר עצום של", "מספר מרשים של", "מספר מדהים של", "מספר נכבד של",
      "הרבה מאוד", "המון המון", "מלא מלא", "שפע שפע", "עושר עושר",
      "רבים", "רבות", "הרבה מאוד", "המון מאוד", "מלא מאוד",
      "כמה וכמה", "לא מעט", "די הרבה", "יותר מדי", "בלי סוף"
    ],
    "מומלץ מאוד": [
      "ממש כדאי", "מאוד כדאי", "שווה מאוד", "מאוד שווה", "ממש שווה",
      "כדאי מאוד", "שווה מאוד", "מומלץ בחום", "מומלץ מאוד", "ממליץ בחום",
      "תעשו את זה", "עשו את זה", "לכו על זה", "קחו את זה", "נסו את זה",
      "אל תפספסו", "אל תוותרו", "אל תחמיצו", "אל תדלגו", "אל תעברו על זה",
      "חובה", "חובה לנסות", "חובה לעשות", "חובה לקחת", "חובה ללכת על זה",
      "טיפ שלי:", "המלצה שלי:", "עצה שלי:", "הצעה שלי:", "רעיון שלי:"
    ],
    "חשוב ביותר": [
      "ממש חשוב", "מאוד חשוב", "סופר חשוב", "קריטי", "חיוני",
      "הכי חשוב", "הכי קריטי", "הכי חיוני", "הכי משמעותי", "הכי רלוונטי",
      "חשוב מאוד", "חשוב להפליא", "חשוב במיוחד", "חשוב בטירוף", "חשוב לגמרי",
      "זה חשוב", "זה קריטי", "זה חיוני", "זה משמעותי", "זה רלוונטי",
      "אי אפשר בלי", "חייבים", "מוכרחים", "צריכים", "נדרשים",
      "נקודת מפתח:", "עיקר העניין:", "הלב של העניין:", "הבסיס:", "היסוד:"
    ],
    "משמעותי ביותר": [
      "ממש משמעותי", "מאוד משמעותי", "סופר משמעותי", "קריטי", "חיוני",
      "הכי משמעותי", "הכי קריטי", "הכי חיוני", "הכי חשוב", "הכי רלוונטי",
      "משמעותי מאוד", "משמעותי להפליא", "משמעותי במיוחד", "משמעותי בטירוף", "משמעותי לגמרי",
      "זה משמעותי", "זה קריטי", "זה חיוני", "זה חשוב", "זה רלוונטי",
      "אי אפשר להתעלם", "חייבים לשים לב", "מוכרחים להתייחס", "צריכים לזכור", "נדרשים להבין",
      "נקודת מפתח:", "עיקר העניין:", "הלב של העניין:", "הבסיס:", "היסוד:"
    ],
    
    // ============================================================
    // פתיחות משפט חוזרות - 30+ חלופות!
    // ============================================================
    "ראשית": [
      "קודם כל", "בהתחלה", "ראשון", "דבר ראשון", "נקודה ראשונה",
      "לפני הכל", "קודם לכל", "בראש ובראשונה", "ראשית כל", "ראשית דבר",
      "נתחיל עם", "נתחיל מ", "נפתח עם", "נפתח ב", "נתחיל בזה:",
      "הדבר הראשון:", "הנקודה הראשונה:", "הפרט הראשון:", "העניין הראשון:", "הסעיף הראשון:",
      "אז קודם כל,", "אז בהתחלה,", "אז ראשון,", "אז דבר ראשון,", "אז נקודה ראשונה,",
      "בואו נתחיל עם", "בואו נתחיל מ", "בואו נפתח עם", "בואו נפתח ב", "בואו נתחיל:"
    ],
    "שנית": [
      "דבר שני", "נקודה שנייה", "שני", "בנוסף", "ועוד",
      "הדבר השני:", "הנקודה השנייה:", "הפרט השני:", "העניין השני:", "הסעיף השני:",
      "ועכשיו לדבר השני,", "ועכשיו לנקודה השנייה,", "ועכשיו לשני,", "ועכשיו לבנוסף,", "ועכשיו לעוד,",
      "אחרי זה,", "בהמשך,", "ואז,", "ואחר כך,", "ולאחר מכן,",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "וגם:", "ובנוסף:", "ומעבר:", "וחוץ:", "ועוד:"
    ],
    "שלישית": [
      "ועוד דבר", "נקודה שלישית", "שלישי", "בנוסף", "ועוד",
      "הדבר השלישי:", "הנקודה השלישית:", "הפרט השלישי:", "העניין השלישי:", "הסעיף השלישי:",
      "ועכשיו לדבר השלישי,", "ועכשיו לנקודה השלישית,", "ועכשיו לשלישי,", "ועכשיו לבנוסף,", "ועכשיו לעוד,",
      "אחרי זה,", "בהמשך,", "ואז,", "ואחר כך,", "ולאחר מכן,",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "וגם:", "ובנוסף:", "ומעבר:", "וחוץ:", "ועוד:"
    ],
    "לבסוף": [
      "ובסוף", "לסיום", "בסיום", "ולסיום", "ובסיום",
      "הדבר האחרון:", "הנקודה האחרונה:", "הפרט האחרון:", "העניין האחרון:", "הסעיף האחרון:",
      "ועכשיו לדבר האחרון,", "ועכשיו לנקודה האחרונה,", "ועכשיו לאחרון,", "ועכשיו לסיום,", "ועכשיו לבסוף,",
      "בשורה התחתונה:", "בסופו של דבר:", "בסיכום:", "בתמצית:", "בקיצור:",
      "ולפני שמסיימים:", "ולפני הסיום:", "ולפני שנסיים:", "ולפני שנגמור:", "ולפני שנחתום:",
      "עוד משהו אחרון:", "עוד דבר אחרון:", "עוד נקודה אחרונה:", "עוד פרט אחרון:", "עוד עניין אחרון:"
    ],
    
    // ============================================================
    // ביטויים נוספים - 30+ חלופות!
    // ============================================================
    "אפשר לומר ש": [
      "אפשר להגיד ש", "ניתן לומר ש", "ניתן להגיד ש", "אפשר לטעון ש", "ניתן לטעון ש",
      "זה נכון ש", "זה ברור ש", "זה ידוע ש", "זה מקובל ש", "זה מוסכם ש",
      "לדעתי,", "לטעמי,", "בעיני,", "מבחינתי,", "לפי דעתי,",
      "אני חושב ש", "אני מאמין ש", "אני סבור ש", "אני טוען ש", "אני אומר ש",
      "נראה לי ש", "נדמה לי ש", "מסתבר ש", "מתברר ש", "יוצא ש",
      "בעצם,", "בקיצור,", "בתכלס,", "בגדול,", "בשורה התחתונה,"
    ],
    "חשוב להדגיש": [
      "צריך לשים לב", "כדאי לשים לב", "שווה לשים לב", "חשוב לשים לב", "טוב לשים לב",
      "שימו לב:", "הערה:", "טיפ:", "נקודה:", "פרט:",
      "אל תפספסו:", "אל תחמיצו:", "אל תדלגו:", "אל תעברו על זה:", "אל תתעלמו:",
      "זה חשוב:", "זה קריטי:", "זה חיוני:", "זה משמעותי:", "זה רלוונטי:",
      "נקודת מפתח:", "עיקר העניין:", "הלב של העניין:", "הבסיס:", "היסוד:",
      "רגע,", "רגע רגע,", "חכו,", "חכו רגע,", "עצרו רגע,"
    ],
    "ראוי להזכיר ש": [
      "שווה להזכיר ש", "כדאי להזכיר ש", "חשוב להזכיר ש", "טוב להזכיר ש", "ראוי לציין ש",
      "אגב,", "דרך אגב,", "למי שלא יודע:", "למי ששכח:", "תזכורת:",
      "שימו לב:", "הערה:", "טיפ:", "נקודה:", "פרט:",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "תדעו ש", "דעו ש", "קחו לידיעה ש", "שימו לב לזה:", "זה חשוב:",
      "לא לשכוח:", "תמיד לזכור:", "קחו בחשבון:", "שימו על הראדר:", "תנו דעתכם:"
    ],
    "ברצוני להבהיר": [
      "אני רוצה להסביר", "אני רוצה להבהיר", "אני רוצה לומר", "אני רוצה להגיד", "אני רוצה לציין",
      "בואו נבהיר:", "בואו נסביר:", "בואו נאמר:", "בואו נגיד:", "בואו נציין:",
      "הבהרה:", "הסבר:", "הערה:", "הארה:", "תוספת:",
      "רגע, אני רוצה להסביר:", "רגע, אני רוצה להבהיר:", "רגע, אני רוצה לומר:", "רגע, אני רוצה להגיד:", "רגע, אני רוצה לציין:",
      "חשוב לי להסביר:", "חשוב לי להבהיר:", "חשוב לי לומר:", "חשוב לי להגיד:", "חשוב לי לציין:",
      "אני חייב להסביר:", "אני חייב להבהיר:", "אני חייב לומר:", "אני חייב להגיד:", "אני חייב לציין:"
    ],
    "בהינתן המידע": [
      "לפי מה שיש", "לפי המידע", "לפי הנתונים", "לפי העובדות", "לפי הפרטים",
      "בהתחשב בזה", "בהתחשב במידע", "בהתחשב בנתונים", "בהתחשב בעובדות", "בהתחשב בפרטים",
      "על סמך זה", "על סמך המידע", "על סמך הנתונים", "על סמך העובדות", "על סמך הפרטים",
      "בהתבסס על זה", "בהתבסס על המידע", "בהתבסס על הנתונים", "בהתבסס על העובדות", "בהתבסס על הפרטים",
      "ממה שיש", "ממה שידוע", "ממה שנראה", "ממה שמסתבר", "ממה שמתברר",
      "לפי זה,", "על פי זה,", "בהתאם לזה,", "בעקבות זה,", "בגלל זה,"
    ],
    "ניתן לראות כי": [
      "רואים ש", "אפשר לראות ש", "ניתן להבחין ש", "אפשר להבחין ש", "ניתן לזהות ש",
      "ברור ש", "ברור לראות ש", "ברור להבחין ש", "ברור לזהות ש", "ברור להבין ש",
      "נראה ש", "נראה לעין ש", "נראה בבירור ש", "נראה בבירור לעין ש", "נראה בבירור להבחין ש",
      "מסתבר ש", "מתברר ש", "יוצא ש", "עולה ש", "מתגלה ש",
      "זה מראה ש", "זה מעיד ש", "זה מלמד ש", "זה מצביע ש", "זה מדגים ש",
      "אפשר להבין ש", "ניתן להבין ש", "אפשר להסיק ש", "ניתן להסיק ש", "אפשר להגיע למסקנה ש"
    ],
    "מומלץ לבדוק": [
      "כדאי לבדוק", "שווה לבדוק", "חשוב לבדוק", "טוב לבדוק", "ראוי לבדוק",
      "תבדקו", "בדקו", "נסו לבדוק", "כדאי לנסות לבדוק", "שווה לנסות לבדוק",
      "אל תשכחו לבדוק", "אל תפספסו לבדוק", "אל תחמיצו לבדוק", "אל תדלגו על לבדוק", "אל תעברו בלי לבדוק",
      "טיפ: תבדקו", "המלצה: תבדקו", "עצה: תבדקו", "הצעה: תבדקו", "רעיון: תבדקו",
      "לפני שממשיכים, תבדקו", "לפני שמתקדמים, תבדקו", "לפני שעוברים הלאה, תבדקו", "לפני שנמשיך, תבדקו", "לפני שנתקדם, תבדקו",
      "חובה לבדוק", "מוכרחים לבדוק", "צריכים לבדוק", "נדרשים לבדוק", "חייבים לבדוק"
    ],
    "חשוב להדגיש כי": [
      "צריך לשים לב ש", "כדאי לשים לב ש", "שווה לשים לב ש", "חשוב לשים לב ש", "טוב לשים לב ש",
      "שימו לב:", "הערה:", "טיפ:", "נקודה:", "פרט:",
      "אל תפספסו:", "אל תחמיצו:", "אל תדלגו:", "אל תעברו על זה:", "אל תתעלמו:",
      "זה חשוב:", "זה קריטי:", "זה חיוני:", "זה משמעותי:", "זה רלוונטי:",
      "נקודת מפתח:", "עיקר העניין:", "הלב של העניין:", "הבסיס:", "היסוד:",
      "רגע,", "רגע רגע,", "חכו,", "חכו רגע,", "עצרו רגע,"
    ],
    "ראוי לציין ש": [
      "שווה לציין ש", "כדאי לציין ש", "חשוב לציין ש", "טוב לציין ש", "ראוי להזכיר ש",
      "אגב,", "דרך אגב,", "למי שלא יודע:", "למי שמתעניין:", "למי שרוצה לדעת:",
      "שימו לב:", "הערה:", "טיפ:", "נקודה:", "פרט:",
      "עוד משהו:", "עוד דבר:", "עוד נקודה:", "עוד פרט:", "עוד עניין:",
      "תדעו ש", "דעו ש", "קחו לידיעה ש", "שימו לב לזה:", "זה חשוב:",
      "לא לשכוח:", "תמיד לזכור:", "קחו בחשבון:", "שימו על הראדר:", "תנו דעתכם:"
    ],
    "כפי שניתן לראות": [
      "כמו שרואים", "כמו שאפשר לראות", "כמו שניתן לראות", "כמו שברור", "כמו שנראה",
      "רואים ש", "אפשר לראות ש", "ניתן לראות ש", "ברור ש", "נראה ש",
      "זה מראה ש", "זה מעיד ש", "זה מלמד ש", "זה מצביע ש", "זה מדגים ש",
      "מסתבר ש", "מתברר ש", "יוצא ש", "עולה ש", "מתגלה ש",
      "אפשר להבין ש", "ניתן להבין ש", "אפשר להסיק ש", "ניתן להסיק ש", "אפשר להגיע למסקנה ש",
      "ברור לעין ש", "ברור להבחין ש", "ברור לזהות ש", "ברור להבין ש", "ברור להסיק ש"
    ],
    "מכאן עולה כי": [
      "מזה יוצא ש", "מזה עולה ש", "מזה מסתבר ש", "מזה מתברר ש", "מזה ברור ש",
      "אז יוצא ש", "אז עולה ש", "אז מסתבר ש", "אז מתברר ש", "אז ברור ש",
      "המסקנה היא ש", "התוצאה היא ש", "השורה התחתונה היא ש", "הסיכום הוא ש", "התמצית היא ש",
      "לכן,", "ולכן,", "משום כך,", "בגלל זה,", "מכאן,",
      "אז מה?", "אז מה יוצא?", "אז מה המסקנה?", "אז מה עושים?", "אז מה הלאה?",
      "בשורה התחתונה:", "בסופו של דבר:", "בסיכום:", "בתמצית:", "בקיצור:"
    ]
  };
  
  // מחליפים ביטויים רשמיים - כל ההופעות! עם בחירה אקראית ללא חזרות!
  Object.keys(formalToHumanMulti).forEach(formal => {
    const alternatives = formalToHumanMulti[formal];
    const usedReplacements = new Set(); // 🔧 מעקב אחרי מה כבר נבחר
    
    while (enhanced.includes(formal)) {
      // בחירת חלופה שעוד לא נבחרה
      let replacement;
      const availableAlternatives = alternatives.filter(a => !usedReplacements.has(a));
      
      if (availableAlternatives.length > 0) {
        replacement = pickRandom(availableAlternatives);
      } else {
        // אם כל החלופות נוצלו, מתחילים מחדש
        usedReplacements.clear();
        replacement = pickRandom(alternatives);
      }
      
      usedReplacements.add(replacement);
      enhanced = enhanced.replace(formal, replacement);
      changes.push({ type: 'החלפה לאנושי', from: formal, to: replacement });
    }
  });
  
  // 🎯 הוספת סמנים אנושיים למספר פסקאות - עם הגבלות חכמות!
  const paragraphs = enhanced.split(/\n\n+/);
  let markersAdded = 0;
  const maxMarkers = Math.min(3, Math.floor(paragraphs.length / 3)); // עד 3 סמנים
  
  // 🚫 דפוסים שאסור להוסיף לפניהם סמנים אנושיים
  const forbiddenPatterns = [
    /^<table/i,                           // טבלאות
    /^<tr/i,                              // שורות בטבלה
    /^<td/i,                              // תאים בטבלה
    /^<th/i,                              // כותרות טבלה
    /^<strong/i,                          // טקסט מודגש
    /^<b>/i,                              // טקסט מודגש
    /^<em/i,                              // טקסט נטוי
    /^<h[1-6]/i,                          // כותרות
    /הריביות בתוכן מעודכנות/,             // השורה הספציפית
    /ריבית פריים/,                        // שורות ריבית
    /עודכן לאחרונה/,                      // שורות עדכון
    /נכון ל/,                             // תאריכים
    /^\d+[%₪]/,                           // מספרים עם אחוזים או שקלים
    /^\[/,                                // שורטקודים
    /^•/,                                 // bullet points
    /^-\s/,                               // רשימות עם מקף
    /^\d+\./,                             // רשימות ממוספרות
  ];
  
  // 🔍 פונקציה לבדיקה אם הפסקה הקודמת היא כותרת
  function isPreviousParagraphHeading(index) {
    if (index <= 0) return false;
    const prev = paragraphs[index - 1].trim();
    // בודק אם הפסקה הקודמת היא כותרת HTML או קצרה מאוד (כמו כותרת)
    return /<h[1-6]/i.test(prev) || 
           /<\/h[1-6]>/i.test(prev) ||
           (prev.length < 100 && prev.length > 5 && !prev.includes('.'));
  }
  
  // 🔍 פונקציה לבדיקה אם הפסקה מתאימה להזרקת סמן
  function isValidForMarker(paragraph, index) {
    const trimmed = paragraph.trim();
    
    // 1. פסקה קצרה מדי
    if (trimmed.length < 100) return false;
    
    // 2. בדיקת דפוסים אסורים
    for (const pattern of forbiddenPatterns) {
      if (pattern.test(trimmed)) return false;
    }
    
    // 3. לא להוסיף אם הפסקה מתחילה בתג HTML (חוץ מ-<p> או <div>)
    if (/^<(?!p|div)[a-z]/i.test(trimmed)) return false;
    
    // 4. לא להוסיף אם הפסקה הקודמת היא כותרת - אז כן להוסיף! (זה מקום טוב)
    // אבל רק אם זו פסקת תוכן אמיתית
    
    // 5. לא להוסיף אם הפסקה מכילה יותר מדי HTML
    const htmlTagCount = (trimmed.match(/<[^>]+>/g) || []).length;
    const textLength = trimmed.replace(/<[^>]+>/g, '').length;
    if (htmlTagCount > 5 && textLength < 200) return false;
    
    // 6. לא להוסיף אם הפסקה מתחילה באות גדולה באנגלית (כנראה קוד או שם)
    if (/^[A-Z]{2,}/.test(trimmed)) return false;
    
    // 7. כן להוסיף רק אם הפסקה מתחילה באות עברית או תג <p>/<div>
    const startsWithHebrew = /^[\u0590-\u05FF]/.test(trimmed.replace(/<[^>]+>/g, '').trim());
    const startsWithParagraphTag = /^<(p|div)[^>]*>/i.test(trimmed);
    
    return startsWithHebrew || startsWithParagraphTag;
  }
  
  for (let i = 1; i < paragraphs.length && markersAdded < maxMarkers; i++) {
    // בדיקה אם הפסקה מתאימה להזרקה
    if (!isValidForMarker(paragraphs[i], i)) continue;
    
    const hasHumanMarker = strongHumanMarkers.some(m => 
      paragraphs[i].toLowerCase().includes(m.toLowerCase().trim())
    );
    
    // 🎯 מעדיפים פסקאות אחרי כותרות!
    const afterHeading = isPreviousParagraphHeading(i);
    const shouldAdd = afterHeading || (i % 3 === 1); // אחרי כותרת או כל פסקה שלישית
    
    if (!hasHumanMarker && shouldAdd) {
      // בחירה אקראית מהסמנים
      const marker = strongHumanMarkers[Math.floor(Math.random() * strongHumanMarkers.length)];
      
      // הוספת הסמן בתחילת הפסקה (אחרי תג פתיחה אם יש)
      const openTagMatch = paragraphs[i].match(/^(<(?:p|div)[^>]*>)/i);
      if (openTagMatch) {
        // יש תג פתיחה - מוסיפים אחריו
        const afterTag = paragraphs[i].slice(openTagMatch[0].length);
        paragraphs[i] = openTagMatch[0] + marker + afterTag.charAt(0).toLowerCase() + afterTag.slice(1);
      } else {
        // אין תג פתיחה - מוסיפים בהתחלה
        paragraphs[i] = marker + paragraphs[i].charAt(0).toLowerCase() + paragraphs[i].slice(1);
      }
      
      changes.push({ type: 'סמן אנושי', added: marker, location: afterHeading ? 'אחרי כותרת' : 'פסקה רגילה' });
      markersAdded++;
    }
  }
  
  if (markersAdded > 0) {
    enhanced = paragraphs.join('\n\n');
  }
  
  return {
    text: enhanced,
    changes: changes,
    changesCount: changes.length
  };
}

/**
 * 🔧 הוספת מגע אנושי אוטומטית
 */
function addHumanTouches(text, analysisResults) {
  let enhanced = text;
  const additions = [];
  const appliedChanges = [];
  
  // 🔥 שומרים את מבנה הפסקאות (ירידות שורה) לפני כל עיבוד
  // מפצלים לפי ירידות שורה ושומרים אותן
  const paragraphParts = enhanced.split(/(\n+)/); // הסוגריים שומרים את ה-\n
  
  // 1. 🎯 גיוון פתיחות משפטים חוזרות - עובדים על כל פסקה בנפרד
  for (let pIdx = 0; pIdx < paragraphParts.length; pIdx++) {
    // אם זה ירידת שורה - לא נוגעים
    if (/^\n+$/.test(paragraphParts[pIdx])) continue;
    if (paragraphParts[pIdx].trim().length === 0) continue;
    
    const sentences = paragraphParts[pIdx].split(/(?<=[.!?])\s+/);
    const starterCounts = {};
    
    // ספירת פתיחות
    sentences.forEach(function(s) {
      const firstWord = s.trim().split(/\s+/)[0];
      if (firstWord && firstWord.length > 2) {
        starterCounts[firstWord] = (starterCounts[firstWord] || 0) + 1;
      }
    });
    
    // החלפת פתיחות חוזרות (יותר מ-2 פעמים)
    Object.keys(starterCounts).forEach(function(starter) {
      if (starterCounts[starter] > 2 && sentenceStarterReplacements[starter]) {
        const alternatives = sentenceStarterReplacements[starter];
        let replaceCount = 0;
        const maxReplace = starterCounts[starter] - 1; // משאיר אחד מקורי
        
        // מחליף רק חלק מההופעות
        sentences.forEach(function(s, idx) {
          if (replaceCount < maxReplace && s.trim().indexOf(starter) === 0) {
            const alt = alternatives[Math.floor(Math.random() * alternatives.length)];
            sentences[idx] = s.replace(starter, alt);
            replaceCount++;
            appliedChanges.push({ type: 'גיוון פתיחה', from: starter, to: alt });
          }
        });
      }
    });
    paragraphParts[pIdx] = sentences.join(' ');
  }
  enhanced = paragraphParts.join(''); // מחבר כולל ירידות השורה
  
  // 2. 🎯 הוספת משפטים קצרים אם הקצב מונוטוני
  // 🔥 תיקון: שומרים על כל סוגי ירידות השורה
  // 🚫 הגבלות: לא בטבלאות, לא בשורות טכניות
  if (analysisResults.rhythm && !analysisResults.rhythm.hasNaturalRhythm) {
    const paragraphsWithBreaks = enhanced.split(/(\n+)/); // שומר את ה-\n
    
    // 🚫 דפוסים שאסור להוסיף בהם משפטים קצרים
    const forbiddenForShortSentences = [
      /<table/i, /<tr/i, /<td/i, /<th/i,               // טבלאות
      /הריביות בתוכן מעודכנות/, /ריבית פריים/,          // שורות ריבית
      /עודכן לאחרונה/, /נכון ל/,                        // תאריכים
      /^\[/, /\[awg/, /\[embed/,                        // שורטקודים
      /<ul/i, /<ol/i, /<li/i,                          // רשימות
    ];
    
    const modifiedParts = paragraphsWithBreaks.map(function(part, partIdx) {
      // אם זה ירידת שורה - לא נוגעים
      if (/^\n+$/.test(part)) return part;
      if (part.trim().length === 0) return part;
      
      // 🚫 בדיקת דפוסים אסורים
      for (const pattern of forbiddenForShortSentences) {
        if (pattern.test(part)) return part;
      }
      
      // עובדים רק על פסקאות ארוכות שמתחילות בעברית
      const textOnly = part.replace(/<[^>]+>/g, '').trim();
      if (!/^[\u0590-\u05FF]/.test(textOnly)) return part;
      
      if (partIdx % 6 === 2 && part.length > 200) { // כל פסקה שלישית ארוכה (מתוך הטקסט בלבד)
        const pSentences = part.split(/(?<=[.!?])\s+/);
        if (pSentences.length > 3) {
          // מוסיף משפט קצר באמצע
          const insertIdx = Math.floor(pSentences.length / 2);
          const shortSentence = shortSentences[Math.floor(Math.random() * shortSentences.length)];
          pSentences.splice(insertIdx, 0, shortSentence);
          appliedChanges.push({ type: 'משפט קצר', added: shortSentence });
        }
        return pSentences.join(' ');
      }
      return part;
    });
    enhanced = modifiedParts.join('');
  }
  
  // 3. 🎯 הוספת ביטוי אישי בתחילת פסקה (אם חסר)
  // 🔥 תיקון: שומרים על כל סוגי ירידות השורה
  // 🚫 הגבלות: לא בטבלאות, לא לפני מודגשים, לא לפני ריביות/תאריכים
  if (!analysisResults.hasHumanTouch) {
    const textParts = enhanced.split(/(\n+)/);
    // מסננים רק חלקי טקסט (לא ירידות שורה)
    const textOnlyParts = textParts.filter(p => !/^\n+$/.test(p) && p.trim().length > 0);
    
    // 🚫 דפוסים שאסור להוסיף לפניהם ביטויים אישיים
    const forbiddenPatternsPersonal = [
      /^<table/i, /^<tr/i, /^<td/i, /^<th/i,           // טבלאות
      /^<strong/i, /^<b>/i, /^<em/i,                    // מודגשים
      /^<h[1-6]/i,                                      // כותרות
      /הריביות בתוכן מעודכנות/, /ריבית פריים/,          // שורות ריבית
      /עודכן לאחרונה/, /נכון ל/,                        // תאריכים
      /^\d+[%₪]/, /^\[/, /^•/, /^-\s/, /^\d+\./,        // רשימות ומספרים
      /^[A-Z]{2,}/                                      // קוד/שמות באנגלית
    ];
    
    // פונקציה לבדיקה אם פסקה מתאימה
    function isValidForPersonalExpression(paragraph) {
      const trimmed = paragraph.trim();
      const textOnly = trimmed.replace(/<[^>]+>/g, '').trim();
      
      // פסקה קצרה מדי
      if (textOnly.length < 100) return false;
      
      // בדיקת דפוסים אסורים
      for (const pattern of forbiddenPatternsPersonal) {
        if (pattern.test(trimmed) || pattern.test(textOnly)) return false;
      }
      
      // לא מתחיל באות עברית
      if (!/^[\u0590-\u05FF]/.test(textOnly) && !/^<(p|div)/i.test(trimmed)) return false;
      
      return true;
    }
    
    if (textOnlyParts.length > 2) {
      // מחפש פסקה מתאימה (לא בהכרח השנייה/שלישית)
      let targetIdx = -1;
      for (let i = 1; i < textOnlyParts.length && i < 5; i++) {
        if (isValidForPersonalExpression(textOnlyParts[i])) {
          targetIdx = i;
          break;
        }
      }
      
      if (targetIdx > 0) {
        const personal = personalExpressions[Math.floor(Math.random() * personalExpressions.length)];
        
        // בודק שהפסקה לא מתחילה כבר בביטוי אישי
        const pStart = textOnlyParts[targetIdx].substring(0, 20).toLowerCase();
        const alreadyPersonal = personalExpressions.some(function(pe) {
          return pStart.indexOf(pe.toLowerCase().trim()) > -1;
        });
        
        if (!alreadyPersonal) {
          const targetText = textOnlyParts[targetIdx];
          
          // הוספת הביטוי בתחילת הפסקה (אחרי תג פתיחה אם יש)
          const openTagMatch = targetText.match(/^(<(?:p|div)[^>]*>)/i);
          let modifiedText;
          if (openTagMatch) {
            const afterTag = targetText.slice(openTagMatch[0].length);
            modifiedText = openTagMatch[0] + personal + afterTag.charAt(0).toLowerCase() + afterTag.slice(1);
          } else {
            modifiedText = personal + targetText.charAt(0).toLowerCase() + targetText.slice(1);
          }
          
          // מחפשים את הטקסט המקורי במערך המלא ומחליפים
          for (let i = 0; i < textParts.length; i++) {
            if (textParts[i] === targetText) {
              textParts[i] = modifiedText;
              break;
            }
          }
          appliedChanges.push({ type: 'ביטוי אישי', added: personal });
          enhanced = textParts.join('');
        }
      }
    }
  }
  
  // 4. 🎯 הוספת סלנג ישראלי (מעט, לא מוגזם)
  if (analysisResults.slangHits < 2) {
    // מחליף מילה פורמלית אחת בסלנג
    const formalToSlang = {
      "מצוין": ["אחלה", "מעולה", "חזק"],
      "נהדר": ["אש", "סוף הדרך", "מטורף"],
      "טוב מאוד": ["סבבה", "אחלה", "בומבה"],
      "בהחלט": ["וואלה", "תכלס", "בטוח"],
      "ללא ספק": ["חד משמעית", "מאה אחוז", "בלי שאלה"],
      "אכן": ["באמת", "נכון", "כן"]
    };
    
    Object.keys(formalToSlang).forEach(function(formal) {
      if (enhanced.indexOf(formal) > -1 && Math.random() > 0.5) {
        const slangOptions = formalToSlang[formal];
        const slang = slangOptions[Math.floor(Math.random() * slangOptions.length)];
        enhanced = enhanced.replace(formal, slang);
        appliedChanges.push({ type: 'סלנג', from: formal, to: slang });
      }
    });
  }
  
  // 5. 🆕 הזרקת "רעש אנושי" (Human Noise Injection) - V5
  // הוספת מילות קישור "שוברות" בתחילת משפטים
  // 🔥 תיקון: עובדים על כל פסקה בנפרד לשמירת ירידות שורה
  // 🔥 תיקון נוסף: רק אם הציון גבוה מאוד (מעל 45) - כי הוספת מחברים יכולה להרע ציונים בינוניים
  if (analysisResults.rawScore > 45) {
    const noiseParagraphs = enhanced.split(/(\n+)/);
    
    for (let npIdx = 0; npIdx < noiseParagraphs.length; npIdx++) {
      if (/^\n+$/.test(noiseParagraphs[npIdx])) continue;
      if (noiseParagraphs[npIdx].trim().length === 0) continue;
      
      const sentencesArray = noiseParagraphs[npIdx].split(/(?<=[.!?])\s+/);
      
      sentencesArray.forEach(function(sentence, idx) {
        // הגנה: מדלג על משפטים ללא עברית (למשל קוד שזלג או פלייסהולדרים)
        if (!/[א-ת]/.test(sentence)) return;

        // מדלג על המשפט הראשון והאחרון
        if (idx > 0 && idx < sentencesArray.length - 1) {
          // סיכוי של 15% להוסיף מילת קישור אנושית למשפט קיים
          if (Math.random() < 0.15 && sentence.length > 20) {
            const connector = humanConnectors[Math.floor(Math.random() * humanConnectors.length)];
            // מוודא שהמשפט לא מתחיל כבר במילת קישור
            const firstWord = sentence.split(/\s+/)[0];
            if (!humanConnectors.includes(firstWord) && !hebrewStopWords.has(firstWord)) {
              sentencesArray[idx] = connector + ' ' + sentence;
              appliedChanges.push({ type: 'רעש אנושי', added: connector });
            }
          }
        }
      });
      noiseParagraphs[npIdx] = sentencesArray.join(' ');
    }
    enhanced = noiseParagraphs.join('');
  }
  
  return {
    text: enhanced,
    suggestions: additions,
    appliedChanges: appliedChanges,
    changesCount: appliedChanges.length
  };
}

// ========================================
// הרצה והחזרת תוצאות
// ========================================

const analysisResults = analyzeText(cleanText);

// 🔧 הרצת התיקון האוטומטי
const SCORE_THRESHOLD = 30; // תיקון מסיבי רק לציונים מעל 30 (ניקוי בסיסי רץ תמיד)

// 🧹 שלב 1: ניקוי בסיסי תמיד! (אימוג'ים, דאשים, תווים מיוחדים, שפות זרות)
const basicCleanResult = basicCleanText(rawText);

let humanizeResult;
let enhanceResult;
let finalFixedHtml;

if (analysisResults.rawScore >= SCORE_THRESHOLD) {
  // ציון גבוה = חשוד כ-AI, צריך לתקן + להוסיף מגע אנושי
  humanizeResult = humanizeText(basicCleanResult.cleanedText, analysisResults);
  // Human touches are now integrated inside humanizeText (running on protected text)
  finalFixedHtml = humanizeResult.humanizedText; 
  
  // מאחד את השינויים
  humanizeResult.changes = basicCleanResult.changes.concat(humanizeResult.changes);
  humanizeResult.totalChanges = basicCleanResult.totalChanges + humanizeResult.totalChanges;
  
  enhanceResult = { changesCount: 0, appliedChanges: [] }; // Dummy for compatibility
} else {
  // ציון נמוך = כבר אנושי, רק ניקוי בסיסי
  humanizeResult = {
    originalText: rawText,
    humanizedText: basicCleanResult.cleanedText,
    changes: basicCleanResult.changes,
    totalChanges: basicCleanResult.totalChanges,
    isModified: basicCleanResult.isModified
  };
  enhanceResult = {
    text: basicCleanResult.cleanedText,
    suggestions: [],
    appliedChanges: [],
    changesCount: 0
  };
  finalFixedHtml = basicCleanResult.cleanedText;
}

// ניתוח הטקסט המתוקן הסופי
// 🔥 תיקון: בודקים גם אם basicCleanResult עשה שינויים!
const hasAnyChanges = humanizeResult.isModified || 
                      enhanceResult.changesCount > 0 || 
                      (basicCleanResult.changes && basicCleanResult.changes.length > 0);

let fixedAnalysis = hasAnyChanges 
  ? analyzeText(finalFixedHtml.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim()) 
  : null;

// 🔍 DEBUG: לוג ציונים
console.log(`\n🔍 DEBUG ציונים:`);
console.log(`   ציון מקורי: ${Math.round(analysisResults.rawScore)}`);
console.log(`   ציון אחרי תיקון: ${fixedAnalysis ? Math.round(fixedAnalysis.rawScore) : 'N/A'}`);
console.log(`   hasAnyChanges: ${hasAnyChanges}`);

// 🚨 בדיקת בטיחות: אם הציון עלה (הורע) - חוזרים לניקוי בסיסי בלבד
if (fixedAnalysis && fixedAnalysis.rawScore > analysisResults.rawScore) {
  console.warn(`⚠️ התיקון המתקדם החמיר את הציון (${Math.round(analysisResults.rawScore)} → ${Math.round(fixedAnalysis.rawScore)})`);
  
  // בודקים אם הניקוי הבסיסי לבד משפר או לא משנה
  const basicOnlyAnalysis = analyzeText(basicCleanResult.cleanedText.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim());
  
  if (basicOnlyAnalysis.rawScore <= analysisResults.rawScore) {
    // הניקוי הבסיסי לא מחמיר - משתמשים בו
    console.warn(`✅ חוזרים לניקוי בסיסי בלבד (ציון: ${Math.round(basicOnlyAnalysis.rawScore)})`);
    finalFixedHtml = basicCleanResult.cleanedText;
    fixedAnalysis = basicOnlyAnalysis;
    humanizeResult.changes = basicCleanResult.changes;
    humanizeResult.isModified = basicCleanResult.isModified;
    humanizeResult.totalChanges = basicCleanResult.totalChanges || 0;
  } else {
    // גם הניקוי הבסיסי מחמיר - חוזרים לטקסט המקורי
    console.warn(`⚠️ גם הניקוי הבסיסי החמיר (${Math.round(basicOnlyAnalysis.rawScore)}), מחזיר לטקסט המקורי`);
    finalFixedHtml = rawText;
    fixedAnalysis = null;
    humanizeResult.changes = [];
    humanizeResult.isModified = false;
    humanizeResult.totalChanges = 0;
  }
}

// 📊 יצירת דוחות שינויים
function generateChangeReports(changes, originalScore, fixedScore) {
  const improvement = originalScore - (fixedScore || originalScore);
  
  // ========================================
  // 🔧 הפרדה בין שינויים בפועל להמלצות
  // ========================================
  const actualChanges = changes.filter(c => !c.type.includes('💡 המלצה'));
  const recommendations = changes.filter(c => c.type.includes('💡 המלצה'));
  
  const actualTotal = actualChanges.reduce((sum, c) => sum + c.count, 0);
  const recommendationsTotal = recommendations.reduce((sum, c) => sum + c.count, 0);
  
  // ========================================
  // 📝 דוח ארוך - מפריד בין שינויים להמלצות
  // ========================================
  let longReport = `📊 דוח תיקונים\n\n`;
  longReport += `📈 ציון: ${originalScore} ← ${fixedScore || '?'} (שיפור: ${improvement > 0 ? '+' : ''}${improvement})\n`;
  longReport += `✅ שינויים שבוצעו: ${actualTotal} ב-${actualChanges.length} קטגוריות\n`;
  if (recommendationsTotal > 0) {
    longReport += `💡 המלצות (לא בוצעו): ${recommendationsTotal} ב-${recommendations.length} קטגוריות\n`;
  }
  longReport += `\n`;
  
  // שינויים שבוצעו בפועל
  if (actualChanges.length > 0) {
    longReport += `━━━ ✅ שינויים שבוצעו ━━━\n\n`;
    actualChanges.forEach((change, index) => {
      longReport += `${index + 1}. ${change.type} (${change.count})\n`;
      
      if (change.details && change.details.length > 0) {
        const seenExamples = new Set();
        for (let i = 0; i < change.details.length; i++) {
          const detail = change.details[i];
          let exampleKey = '';
          let exampleLine = '';
          
          if (detail.from && detail.to !== undefined) {
            exampleKey = `${detail.from}|${detail.to}`;
            exampleLine = `   • "${detail.from}" ← "${detail.to || '(הוסר)'}"`;
          } else if (detail.added) {
            exampleKey = detail.added.trim();
            exampleLine = `   + "${detail.added.trim()}"`;
          }
          
          if (exampleKey && !seenExamples.has(exampleKey)) {
            seenExamples.add(exampleKey);
            longReport += exampleLine + `\n`;
          }
        }
      }
      longReport += `\n`;
    });
  }
  
  // המלצות (לא בוצעו)
  if (recommendations.length > 0) {
    longReport += `━━━ 💡 המלצות לשיפור נוסף ━━━\n\n`;
    recommendations.forEach((change, index) => {
      // מסיר את הprefix "💡 המלצה: " מהכותרת
      const cleanType = change.type.replace('💡 המלצה: ', '');
      longReport += `${index + 1}. ${cleanType} (${change.count})\n`;
      
      if (change.details && change.details.length > 0) {
        const seenExamples = new Set();
        for (let i = 0; i < Math.min(change.details.length, 5); i++) { // רק 5 דוגמאות להמלצות
          const detail = change.details[i];
          let exampleKey = '';
          let exampleLine = '';
          
          if (detail.from && detail.to !== undefined) {
            exampleKey = `${detail.from}|${detail.to}`;
            exampleLine = `   • "${detail.from}" → "${detail.to || '(מומלץ להסיר)'}"`;
          } else if (detail.added) {
            exampleKey = detail.added.trim();
            exampleLine = `   + מומלץ להוסיף: "${detail.added.trim()}"`;
          }
          
          if (exampleKey && !seenExamples.has(exampleKey)) {
            seenExamples.add(exampleKey);
            longReport += exampleLine + `\n`;
          }
        }
        if (change.details.length > 5) {
          longReport += `   ... ועוד ${change.details.length - 5} המלצות\n`;
        }
      }
      longReport += `\n`;
    });
  }
  
  // ========================================
  // 📋 דוח קצר - רק שינויים בפועל + סיכום המלצות
  // ========================================
  let shortReport = `📊 ציון: ${originalScore}←${fixedScore || '?'} (+${improvement}) | ✅ ${actualTotal} שינויים`;
  if (recommendationsTotal > 0) {
    shortReport += ` | 💡 ${recommendationsTotal} המלצות`;
  }
  shortReport += `\n\n`;
  
  actualChanges.forEach(change => {
    let line = `✅ ${change.type}: ${change.count}`;
    
    if (change.details && change.details.length > 0) {
      const firstDetail = change.details[0];
      if (firstDetail.from && firstDetail.to !== undefined) {
        line += ` ("${firstDetail.from}"←"${firstDetail.to}")`;
      }
    }
    
    if (shortReport.length + line.length < 1800) {
      shortReport += line + `\n`;
    }
  });
  
  if (recommendations.length > 0 && shortReport.length < 1700) {
    shortReport += `\n💡 המלצות: `;
    const recTypes = recommendations.map(r => r.type.replace('💡 המלצה: ', '')).join(', ');
    shortReport += recTypes.substring(0, 100);
  }
  
  return { longReport, shortReport };
}

// שילוב כל השינויים לדוח
// 🔧 תיקון: מפרמטים את הדוגמאות של "מגע אנושי" לפורמט אחיד
const humanTouchDetails = (enhanceResult.appliedChanges || []).map(function(change) {
  // המרה לפורמט אחיד: { from, to } או { added }
  if (change.from && change.to) {
    return { from: change.from, to: change.to };
  } else if (change.added) {
    return { added: change.added };
  } else if (change.type === 'סלנג' || change.type === 'גיוון פתיחה' || change.type === 'ביטוי אישי') {
    if (change.from && change.to) {
      return { from: change.from, to: change.to };
    } else if (change.added) {
      return { added: change.added };
    }
  }
  return null;
}).filter(function(d) { return d !== null; });

const allChanges = humanizeResult.changes.concat([{
  type: 'מגע אנושי',
  count: enhanceResult.changesCount,
  description: 'גיוון פתיחות, ביטויים אישיים, סלנג',
  details: humanTouchDetails
}]).filter(function(c) { return c.count > 0; });

const changeReports = generateChangeReports(
  allChanges, 
  Math.round(analysisResults.rawScore), 
  fixedAnalysis ? Math.round(fixedAnalysis.rawScore) : null
);

// 🔍 DEBUG: מידע מפורט לדיבוג
const debugInfo = {
  originalRawScore: Math.round(analysisResults.rawScore),
  fixedRawScore: fixedAnalysis ? Math.round(fixedAnalysis.rawScore) : null,
  wasReverted: fixedAnalysis === null && hasAnyChanges,
  revertReason: fixedAnalysis === null && hasAnyChanges ? 'התיקון החמיר את הציון - בוטל' : null,
  changesAttempted: allChanges.reduce((sum, c) => sum + c.count, 0),
  changesApplied: fixedAnalysis ? allChanges.reduce((sum, c) => sum + c.count, 0) : 0,
  
  // 🔥 פירוט מה גורם לציון - לפני תיקון
  beforeFix: {
    oldMetrics: Math.round(analysisResults.oldMetricsScore),
    newMetrics: Math.round(analysisResults.newMetricsScore),
    advancedMetrics: Math.round(analysisResults.advancedMetricsScore),
    gptDashScore: analysisResults.gptDashScore,
    gptDashCount: analysisResults.gptDashCount,
    humanBonus: analysisResults.humanBonus,
    humanMarkerHits: analysisResults.humanMarkerHits?.length || 0,
    claudeScore: analysisResults.claudeScore,
    repetitionPenalty: analysisResults.repetitionPenalty,
    linkingScore: analysisResults.linkingScore
  },
  
  // 🔥 פירוט מה גורם לציון - אחרי תיקון
  afterFix: fixedAnalysis ? {
    oldMetrics: Math.round(fixedAnalysis.oldMetricsScore),
    newMetrics: Math.round(fixedAnalysis.newMetricsScore),
    advancedMetrics: Math.round(fixedAnalysis.advancedMetricsScore),
    gptDashScore: fixedAnalysis.gptDashScore,
    gptDashCount: fixedAnalysis.gptDashCount,
    humanBonus: fixedAnalysis.humanBonus,
    humanMarkerHits: fixedAnalysis.humanMarkerHits?.length || 0,
    claudeScore: fixedAnalysis.claudeScore,
    repetitionPenalty: fixedAnalysis.repetitionPenalty,
    linkingScore: fixedAnalysis.linkingScore
  } : null
};

return [
  {
    json: {
      // ========================================
      // 📊 ציונים - לפני ואחרי
      // ========================================
      scoreBefore: Math.round(analysisResults.rawScore),
      scoreAfter: fixedAnalysis ? Math.round(fixedAnalysis.rawScore) : Math.round(analysisResults.rawScore),
      improvement: fixedAnalysis ? Math.round(analysisResults.rawScore - fixedAnalysis.rawScore) : 0,
      
      // 🆕 האם בוצע תיקון?
      wasFixed: fixedAnalysis !== null, // 🔥 תיקון: רק אם התיקון באמת הוחל!
      fixReason: fixedAnalysis !== null
        ? 'ציון גבוה - בוצע תיקון אוטומטי' 
        : (hasAnyChanges ? '⚠️ התיקון בוטל - החמיר את הציון' : 'ציון נמוך (' + Math.round(analysisResults.rawScore) + ') - הטקסט כבר אנושי'),
      
      // תאימות לאחור
      score: Math.round(analysisResults.rawScore),
      fixedScore: fixedAnalysis ? Math.round(fixedAnalysis.rawScore) : null,
      
      // 🔍 DEBUG - מידע לדיבוג
      debug: debugInfo,
      
      confidence: analysisResults.confidence,
      explanation: analysisResults.explanation,
      
      // 🔥 PRO Confidence
      proConfidence: analysisResults.proConfidence,
      proSignalCount: analysisResults.proSignalCount,
      
      // ========================================
      // 📝 דוחות שינויים
      // ========================================
      changeReportLong: changeReports.longReport,
      changeReportShort: changeReports.shortReport,
      
      // ========================================
      // 🔧 HTML מתוקן אוטומטית (מוכן לוורדפרס!)
      // ========================================
      fixedHtml: finalFixedHtml,  // HTML מלא עם כל ה-Schema ו-Shortcodes + מגע אנושי
      fixedText: finalFixedHtml,  // תאימות לאחור
      
      // פרטי התיקונים
      fixes: {
        isModified: humanizeResult.isModified || enhanceResult.changesCount > 0,
        totalChanges: humanizeResult.totalChanges + enhanceResult.changesCount,
        changes: humanizeResult.changes,
        humanTouches: enhanceResult.appliedChanges,
        humanTouchesCount: enhanceResult.changesCount,
        additionalSuggestions: enhanceResult.suggestions
      },
      
      // 🆕 רשימת מילים לתיקון (עבור GPT Completion)
      wordsToFix: basicCleanResult.foreignWordsList || [],

      // 🆕 פרומפט לתיקון אוטומטי ב-GPT - מבוסס הקשר (Context Aware)
      fixPrompt: (basicCleanResult.foreignWordsList && basicCleanResult.foreignWordsList.length > 0) 
        ? `You are a Hebrew language expert. The following sentences contain words that were corrupted by foreign characters (like Arabic/Cyrillic) which were removed, leaving a broken Hebrew word.\n\n` +
          `Your task: Identify the broken word in the context, and provide the CORRECTED Hebrew word.\n\n` + 
          basicCleanResult.foreignWordsList.map(w => `Context: "${w.context}"\nBroken Word: "${w.cleaned}"`).join('\n\n') + 
          `\n\nOUTPUT FORMAT:\nReturn ONLY a raw JSON object with a "corrections" array.\nEach item must have "original" (the Broken Word exactly as shown) and "fixed" (the full corrected Hebrew word).\n\nExample:\nInput:\nContext: "שלום לכולם"\nBroken Word: "שלעום"\nOutput:\n{ "corrections": [ { "original": "שלעום", "fixed": "שלום" } ] }`
        : null,
      
      // 🆕 האם נדרש טיפול AI נוסף? (yes/no)
      requiresAIFix: (basicCleanResult.foreignWordsList && basicCleanResult.foreignWordsList.length > 0) ? 'yes' : 'no',

      // ========================================
      // ציונים מפורטים
      // ========================================
      oldMetricsScore: Math.round(analysisResults.oldMetricsScore),
      newMetricsScore: Math.round(analysisResults.newMetricsScore),
      advancedMetricsScore: Math.round(analysisResults.advancedMetricsScore),
      potentialMinScore: analysisResults.potentialMinScore,
      
      // סיכום
      summary: analysisResults.summary + 
        (humanizeResult.isModified ? 
          `\n\n**🔧 תיקון אוטומטי:**\n` +
          `• בוצעו ${humanizeResult.totalChanges} שינויים\n` +
          `• ציון לאחר תיקון: ${fixedAnalysis ? Math.round(fixedAnalysis.rawScore) : 'N/A'}\n` +
          `• שיפור: ${fixedAnalysis ? Math.round(analysisResults.rawScore - fixedAnalysis.rawScore) : 0} נקודות` 
          : ''),
      
      // בעיות והמלצות
      problems: analysisResults.problematicElements,
      suggestions: analysisResults.improvementSuggestions,
      
      // 🔥 PRO Analysis Details
      proAnalysis: {
        perplexity: analysisResults.perplexity,
        ngrams: analysisResults.ngrams,
        zipf: analysisResults.zipf,
        vocabulary: analysisResults.vocabulary,
        repetitionPatterns: analysisResults.repetitionPatterns,
        rhythm: analysisResults.rhythm,
        connectors: analysisResults.connectors
      },
      
      // פרטים מלאים
      details: {
        textLength: analysisResults.textLength,
        wordCount: analysisResults.wordCount,
        phraseHits: analysisResults.phraseHits,
        claudeHits: analysisResults.claudeHits,
        humanMarkerHits: analysisResults.humanMarkerHits,
        hedgingHits: analysisResults.hedgingHits,
        culturalHits: analysisResults.culturalHits,
        recencyHits: analysisResults.recencyHits,
        slangHits: analysisResults.slangHits,
        bigramHits: analysisResults.ngrams?.bigramHits,
        trigramHits: analysisResults.ngrams?.trigramHits,
        avgSentenceLength: analysisResults.avgLength,
        stdDev: analysisResults.stdDev,
        burstinessScore: analysisResults.burstinessScore,
        passiveRatio: analysisResults.passiveRatio,
        complexSentenceRatio: analysisResults.complexSentenceRatio,
        lexicalRichness: analysisResults.lexicalRichness,
        perplexityScore: analysisResults.perplexity?.perplexityScore,
        typeTokenRatio: analysisResults.vocabulary?.typeTokenRatio,
        hasHumanTouch: analysisResults.hasHumanTouch,
        hasEmotionalVariety: analysisResults.hasEmotionalVariety,
        isLowPerplexity: analysisResults.perplexity?.isLowPerplexity,
        hasAINgrams: analysisResults.ngrams?.isAIPattern,
        hasLimitedVocab: analysisResults.vocabulary?.isLimitedVocab
      },
      
      // ========================================
      // 📝 טקסטים
      // ========================================
      originalText: rawText,
      cleanedText: cleanText
    }
  }
];

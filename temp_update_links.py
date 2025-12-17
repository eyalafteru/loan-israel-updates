import sys
import os

raw_data = """הלוואה לפתיחת עסק	הלוואה לפתיחת עסק	https://loan-israel.co.il/Business/loans-for-new-business/
הלוואות סולו לעסקים	הלוואות סולו לעסקים	https://loan-israel.co.il/Business/solo-loans-to-businesses/
הלוואה לעסקים בקשיים	הלוואה לעסקים בקשיים	https://loan-israel.co.il/Business/business-loan-difficulties/
הלוואות לחברות סטארט אפ	הלוואות לחברות סטארט אפ	https://loan-israel.co.il/Business/loans-for-start-up/
הלוואות הון חוזר לעסקים	הלוואות הון חוזר לעסקים	https://loan-israel.co.il/Business/working-capital-loans-to-businesses/
פתרונות מימון ואשראי לעסקים קטנים	פתרונות מימון ואשראי לעסקים קטנים	https://loan-israel.co.il/Business/redit-solutions-for-small-businesses/
הלוואות פרטיות לעסקים	הלוואות פרטיות לעסקים	https://loan-israel.co.il/Business/private_buisiness_loan/
גיוס אשראי לעסקים מבנקים	גיוס אשראי לעסקים מבנקים	https://loan-israel.co.il/Business/business-credit-from-banks/
גיוס אשראי לעסקים גדולים	גיוס אשראי לעסקים גדולים	https://loan-israel.co.il/Business/big-business-credit-recruitment/
הלוואת גישור לעסקים	הלוואת גישור לעסקים	https://loan-israel.co.il/Business/business-bridging-loan/
הלוואה לרכישת עסק פעיל	הלוואה לרכישת עסק	https://loan-israel.co.il/Business/loan-for-the-purchase-of-operating-business/
מרום הקרן להלוואות לעסקים של הסוכנות היהודית	קרן מרום	https://loan-israel.co.il/Business/%d7%9e%d7%a8%d7%95%d7%9d-%d7%94%d7%a7%d7%a8%d7%9f-%d7%9c%d7%94%d7%9c%d7%95%d7%95%d7%90%d7%95%d7%aa-%d7%9c%d7%a2%d7%a1%d7%a7%d7%99%d7%9d-%d7%a9%d7%9c-%d7%94%d7%a1%d7%95%d7%9b%d7%a0%d7%95%d7%aa-%d7%94/
קרן מפרש להלוואות לעסקים	קרן מפרש	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%9e%d7%a4%d7%a8%d7%a9-%d7%9c%d7%94%d7%9c%d7%95%d7%95%d7%90%d7%95%d7%aa-%d7%9c%d7%a2%d7%a1%d7%a7%d7%99%d7%9d/
קרנות פילנתרופיות	קרנות פילנתרופיות	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%a0%d7%95%d7%aa-%d7%a4%d7%99%d7%9c%d7%a0%d7%aa%d7%a8%d7%95%d7%a4%d7%99%d7%95%d7%aa/
הלוואות להון חוזר	הלוואות להון חוזר	https://loan-israel.co.il/Business/working-capital-loans/
הלוואה לעסק בהקמה	הלוואה לעסק בהקמה	https://loan-israel.co.il/Business/business-loan-construction/
עוגן הלוואות (האגודה הישראלית להלוואות ללא ריבית  IFLA)	עוגן הלוואות	https://loan-israel.co.il/Business/israel-free-loan/
הקרן לסיוע לעסקים בערבות המדינה	הקרן לסיוע לעסקים בערבות המדינה	https://loan-israel.co.il/Business/business-assistance-fund-state-guarantee/
קרן BDSK בערבות המדינה	קרן BDSK בערבות המדינה	https://loan-israel.co.il/Business/state-guarantee-fund-bdsk/
קרן קורת	קרן קורת	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%a7%d7%95%d7%a8%d7%aa/
קרן הון סיכון	קרן הון סיכון	https://loan-israel.co.il/Business/venture-capital-funds/
הלוואה חוץ בנקאית לעסקים	הלוואה חוץ בנקאית לעסקים	https://loan-israel.co.il/Business/non-bank-loans-to-businesses/
קרן נס הסוכנות היהודית	קרן נס	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%a0%d7%a1-%d7%94%d7%a1%d7%95%d7%9b%d7%a0%d7%95%d7%aa-%d7%94%d7%99%d7%94%d7%95%d7%93%d7%99%d7%aa/
תכנית מימון לפעילות סולארית	מימון לקולטים סולארים	https://loan-israel.co.il/Business/solar-activity-financing-plan/
הקרן החדשה לסיוע לעסקים קטנים ובינוניים	הקרן החדשה לסיוע לעסקים קטנים ובינוניים	https://loan-israel.co.il/Business/the-new-fund-to-assist-small-and-medium-businesses/
הלוואה בערבות המדינה לפתיחת עסק	הלוואה בערבות המדינה לפתיחת עסק	https://loan-israel.co.il/Business/loan-to-open-a-business/
קרן נתן	קרן נתן	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%a0%d7%aa%d7%9f-%d7%a7%d7%99%d7%a8%d7%a9/
קרן פדרציית ניו-יורק לישראל	קרן פדרציית ניו-יורק לישראל	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%a4%d7%93%d7%a8%d7%a6%d7%99%d7%99%d7%aa-%d7%a0%d7%99%d7%95-%d7%99%d7%95%d7%a8%d7%a7-%d7%9c%d7%99%d7%a9%d7%a8%d7%90%d7%9c/
קרן פיטסבורג לעסקים	קרן פיטסבורג לעסקים	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%a4%d7%99%d7%98%d7%a1%d7%91%d7%95%d7%a8%d7%92-%d7%9c%d7%a2%d7%a1%d7%a7%d7%99%d7%9d/
הלוואה בערבות מדינה לכיסוי אובליגו	הלוואה בערבות מדינה לכיסוי אובליגו	https://loan-israel.co.il/Business/state-guaranteed-loan-to-cover-the-obligo/
מסלולי הלוואות לעסקים של בנק דיסקונט	הלוואות לעסקים של בנק דיסקונט	https://loan-israel.co.il/Business/loans-to-businesses-of-bank-discont/
מסלולי הלוואות לעסקים של בנק מזרחי טפחות	הלוואות לעסקים של בנק מזרחי טפחות	https://loan-israel.co.il/Business/business-loans-routes-mizrahi-tefahot-bank/
מסלולי הלוואות לעסקים של בנק מרכנתיל דיסקונט	הלוואות לעסקים של בנק מרכנתיל דיסקונט	https://loan-israel.co.il/Business/business-loans-routes-mercantile-discount-bank/
הלוואות סולו ללא בטחונות	הלוואות סולו	https://loan-israel.co.il/Business/solo-loans-without-collateral/
הלוואה לעצמאים בערבות המדינה	הלוואה לעצמאים בערבות המדינה	https://loan-israel.co.il/Business/self-employed-loans/
קרן לסיוע לעסקים קטנים במסלול מהיר עד 100,000 ₪	קרן לסיוע לעסקים קטנים	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%9c%d7%a1%d7%99%d7%95%d7%a2-%d7%9c%d7%a2%d7%a1%d7%a7%d7%99%d7%9d-%d7%a7%d7%98%d7%a0%d7%99%d7%9d-%d7%91%d7%9e%d7%a1%d7%9c%d7%95%d7%9c-%d7%9e%d7%94%d7%99%d7%a8-%d7%a2%d7%93-100000/
מסלול סיוע להקמת מפעלים מחוללי שינוי בפריפריה בישראל	מסלול סיוע להקמת מפעלים מחוללי שינוי בפריפריה בישראל	https://loan-israel.co.il/Business/track-assistance-to-set-up-plants-in-israel-causing-a-change-in-the-periphery/
מסלולי הלוואות לעסקים של בנק יהב לעובדי המדינה	הלוואות לעסקים של בנק יהב לעובדי המדינה	https://loan-israel.co.il/Business/tracks-loans-businesses-bank-yahav/
מסלולי הלוואות לעסקים של בנק פועלי אגודת ישראל	מסלולי הלוואות לעסקים של בנק פועלי אגודת ישראל	https://loan-israel.co.il/Business/business-loans-routes-pagi-bank/
הלוואות בערבות מדינה לעסקים במשבר	הלוואות בערבות מדינה לעסקים במשבר	https://loan-israel.co.il/Business/business-crisis-loans/
קרן הזנק רשות החדשנות	קרן הזנק	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%94%d7%96%d7%a0%d7%a7-%d7%a9%d7%9c-%d7%94%d7%9e%d7%93%d7%a2%d7%9f-%d7%94%d7%a8%d7%90%d7%a9%d7%99/
קרן הלוואות לעסקים קטנים	הלוואות לעסקים קטנים	https://loan-israel.co.il/Business/small-business-loan-fund/
קרן הגליל	קרן הגליל	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%94%d7%92%d7%9c%d7%99%d7%9c/
קרן לסיוע לפרויקטים ומכרזים בין לאומיים	קרן לסיוע לפרויקטים ומכרזים בין לאומיים	https://loan-israel.co.il/Business/%d7%a4%d7%a8%d7%95%d7%99%d7%a7%d7%98%d7%99%d7%9d-%d7%95%d7%9e%d7%9b%d7%a8%d7%96%d7%99%d7%9d-%d7%91%d7%99%d7%9f-%d7%9c%d7%90%d7%95%d7%9e%d7%99%d7%99%d7%9d/
קרן דטרויט	קרן דטרויט	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%93%d7%98%d7%a8%d7%95%d7%99%d7%98/
מימון נכסים מניבים	מימון נכסים מניבים	https://loan-israel.co.il/Business/financing-rental-properties/
קרן סיוע לחקלאים	קרן סיוע לחקלאים	https://loan-israel.co.il/Business/farmers-assistance-fund/
סיוע ממשלתי במימון והקצאת קרקעות	סיוע ממשלתי במימון והקצאת קרקעות	https://loan-israel.co.il/Business/state-aid-funding-and-allocation-of-land/
קרן סיוע למסחר	קרן סיוע למסחר	https://loan-israel.co.il/Business/trade-relief-fund/
הלוואות לרכישת ציוד ומכונות	הלוואות לרכישת ציוד ומכונות	https://loan-israel.co.il/Business/loans-for-the-purchase-of-equipment-and-machinery/
הלוואות בערבות מדינה לעסקים בינוניים	הלוואות בערבות מדינה לעסקים בינוניים	https://loan-israel.co.il/Business/medium-business-loans/
הלוואות בערבות מדינה לעסק ותיק	הלוואות בערבות מדינה לעסק ותיק	https://loan-israel.co.il/Business/veteran-business-loan/
הלוואה לעוסק פטור	הלוואה לעוסק פטור	https://loan-israel.co.il/Business/exempt-dealer/
גיוס אשראי לעסקאות נדלן	גיוס אשראי לעסקאות נדלן	https://loan-israel.co.il/Business/credit-recruitment-for-real-estate/
הקרן לעולה העצמאי	הקרן לעולה העצמאי	https://loan-israel.co.il/Business/%d7%94%d7%a7%d7%a8%d7%9f-%d7%9c%d7%a2%d7%95%d7%9c%d7%94-%d7%94%d7%a2%d7%a6%d7%9e%d7%90%d7%99/
מימון נכס מסחרי	מימון נכס מסחרי	https://loan-israel.co.il/Business/commercial-property-financing/
מימון עסקאות נדל”ן	מימון עסקאות נדל”ן	https://loan-israel.co.il/Business/financing-real-estate-transactions/
מסלולי הלוואות לעסקים של בנק אוצר החייל	הלוואות לעסקים של בנק אוצר החייל	https://loan-israel.co.il/Business/business-loans-of-treasury-bank-otzar-hachayal/
מסלולי הלוואות לעסקים של בנק מסד	הלוואות לעסקים של בנק מסד	https://loan-israel.co.il/Business/tracks-loans-businesses-of-bank-massad/
הלוואה בערבות המדינה להרחבת העסק	הלוואה בערבות המדינה להרחבת העסק	https://loan-israel.co.il/Business/expanding-business-loan/
קרן דרומה צפונה לעסקים	קרן דרומה צפונה לעסקים	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%93%d7%a8%d7%95%d7%9e%d7%94-%d7%a6%d7%a4%d7%95%d7%a0%d7%94/
הלוואה בערבות המדינה חרבות ברזל	הלוואה בערבות המדינה חרבות ברזל	https://loan-israel.co.il/Business/%d7%94%d7%9c%d7%95%d7%95%d7%90%d7%94-%d7%91%d7%a2%d7%a8%d7%91%d7%95%d7%aa-%d7%94%d7%9e%d7%93%d7%99%d7%a0%d7%94-%d7%91%d7%a2%d7%a7%d7%91%d7%95%d7%aa-%d7%9e%d7%9c%d7%97%d7%9e%d7%aa-%d7%97%d7%a8%d7%91/
בנק הפועלים לעסקים	בנק הפועלים לעסקים	https://loan-israel.co.il/Business/poalim-bank-for-business/
קרן שמש ליזמים	קרן שמש ליזמים	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%a9%d7%9e%d7%a9-%d7%9c%d7%99%d7%96%d7%9e%d7%99%d7%9d/
מימון ליזמים והלוואה לעצמאים	מימון ליזמים	https://loan-israel.co.il/Business/%d7%9e%d7%99%d7%9e%d7%95%d7%9f-%d7%9c%d7%99%d7%96%d7%9e%d7%99%d7%9d-%d7%95%d7%a2%d7%a6%d7%9e%d7%90%d7%99%d7%99%d7%9d-%d7%9e%d7%aa%d7%97%d7%99%d7%9c%d7%99%d7%9d/
שירותי ניכיון צ'קים	שירותי ניכיון צ'קים	https://loan-israel.co.il/Business/%d7%a9%d7%99%d7%a8%d7%95%d7%aa%d7%99-%d7%a0%d7%99%d7%9b%d7%99%d7%95%d7%9f-%d7%a6%d7%a7%d7%99%d7%9d/
מימון להקמה והרחבה של פרויקטים בתחום התיירות	מימון להקמה והרחבה של פרויקטים בתחום התיירות	https://loan-israel.co.il/Business/funding-for-the-construction-and-expansion-of-tourism-projects/
קרנות סיוע למפעלים במצוקה	קרנות סיוע למפעלים במצוקה	https://loan-israel.co.il/Business/distressed-enterprises-assistance-funds/
אשראי והלוואות לקבלנים	הלוואות לקבלנים	https://loan-israel.co.il/Business/credit-and-loans-contractors/
הלוואות וגיוס אשראי לקבוצות רכישה	הלוואות לקבוצות רכישה	https://loan-israel.co.il/Business/loans-and-credit-recruitment-purchasing-groups/
מסלולי הלוואות לעסקים של בנק הפועלים	הלוואות לעסקים של בנק הפועלים	https://loan-israel.co.il/Business/loans-to-businesses-of-bank-hapoalim/
מסלולי הלוואות לעסקים של בנק ירושלים	הלוואות לעסקים של בנק ירושלים	https://loan-israel.co.il/Business/tracks-loans-businesses-of-bank-of-jerusalem/
הלוואות במסגרת מעוף של משרד הכלכלה	הלוואות במסגרת מעוף של משרד הכלכלה	https://loan-israel.co.il/Business/loans-maof-ministry-of-economy/
גיוס הלוואה בערבות מדינה מבנקים	הלוואה בערבות מדינה מבנקים	https://loan-israel.co.il/Business/guaranteed-loans-banks/
הלוואה בערבות מדינה ליזמים במסלול עסקים בהקמה	הלוואה בערבות מדינה ליזמים	https://loan-israel.co.il/Business/entrepreneurs-loan/
הלוואות בערבות מדינה מסלול הון חוזר	הלוואות בערבות מדינה מסלול הון חוזר	https://loan-israel.co.il/Business/maslol-hon-huzer/
הלוואות בערבות המדינה למפעלים ותעשייה	הלוואות בערבות המדינה למפעלים	https://loan-israel.co.il/Business/enterprises-and-industry-loans/
הלוואות בערבות המדינה לעסקים קטנים	הלוואות בערבות המדינה לעסקים קטנים	https://loan-israel.co.il/Business/small-business-loans/
קרן סולם הלוואות לעסקים במגזר הערבי	קרן סולם	https://loan-israel.co.il/Business/%d7%a7%d7%a8%d7%9f-%d7%94%d7%9c%d7%95%d7%95%d7%90%d7%95%d7%aa-%d7%a1%d7%95%d7%9c%d7%9d/
הלוואה לחברה בע”מ	הלוואה לחברה בע”מ	https://loan-israel.co.il/Business/%d7%94%d7%9c%d7%95%d7%95%d7%90%d7%94-%d7%9c%d7%97%d7%91%d7%a8%d7%94-%d7%91%d7%a2%d7%9e/
הלוואות לעוסק מורשה	הלוואות לעוסק מורשה	https://loan-israel.co.il/Business/authorized-dealer-loan/"""

target_file = r'C:\Users\eyal\עדכון עמודים מיוחדים מאני\קישורי ויקי - מילות מפתח.csv'

lines = raw_data.strip().split('\n')
new_rows = []

for line in lines:
    parts = line.strip().split('\t')
    if len(parts) >= 3:
        kw1 = parts[0].strip()
        kw2 = parts[1].strip()
        url = parts[-1].strip()
        
        keywords = set()
        if kw1: keywords.add(kw1)
        if kw2: keywords.add(kw2)
        
        # Format as URL|Keywords
        new_rows.append(f"{url}|{', '.join(sorted(list(keywords)))}")

# Append to file
try:
    with open(target_file, 'a', encoding='utf-8') as f:
        for row in new_rows:
            f.write(row + '\n')
    print(f"Appended {len(new_rows)} rows to {target_file}")
except Exception as e:
    print(f"Error: {e}")


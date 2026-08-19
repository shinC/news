import re

def extract_text(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    text = re.sub(r'<[^>]+>', ' ', content)
    for ent, rep in [('&amp;','&'),('&quot;','"'),('&#x27;',"'"),('&lt;','<'),('&gt;','>'),('&nbsp;',' ')]:
        text = text.replace(ent, rep)
    text = re.sub(r'&#[0-9a-fx]+;', '', text)
    lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 4]
    skip = ['function ','var ','charset','sendClick','returnFalse','pstatic.net','type=w','se-module-data','data-module','data-link','navermobil']
    filtered = [l for l in lines if not any(x in l for x in skip)]
    return '\n'.join(filtered)

base = '/home/tripod/.gemini/antigravity-ide/brain/43f8a4eb-e61e-44ac-b6b3-7e25b295dc47/.system_generated/steps/'
files = {
    '7월 13일(월)': base + '50/content.md',
    '7월 14일(화)': base + '51/content.md',
    '7월 15일(수)': base + '82/content.md',
    '7월 16일(목)': base + '83/content.md',
}

keywords = ['코스피','코스닥','달러','외국인','기관','개인','%','원','주도주','테마','서킷','사이드카','수급','거래대금','WTI','국채','하락','상승','급락','급등','폭락','종목','발동','매도','매수','이슈','섹터','장중','전일','포인트','억원','조원','코스피200']

for day, path in files.items():
    print()
    print('=' * 70)
    print(f'=== {day} ===')
    print('=' * 70)
    try:
        txt = extract_text(path)
        relevant = [l for l in txt.split('\n') if any(c in l for c in keywords) and len(l) > 10]
        print('\n'.join(relevant[:80]))
    except Exception as e:
        print(f'오류: {e}')

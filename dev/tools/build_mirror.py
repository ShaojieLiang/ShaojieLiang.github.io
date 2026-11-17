"""Prepare a local, field-adapted copy of the reference site's public frontend."""
import sys, os, re, json, hashlib, pathlib, shutil, urllib.request, urllib.parse, concurrent.futures
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup, Comment

ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/'site'; UP=ROOT/'upstream'
BASE='https://teatrlalka.pl'
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fetch-assets',action='store_true',help='Download any missing public assets; the normal build works offline.')
OPTIONS=parser.parse_args()
SITE.mkdir(parents=True,exist_ok=True)
for name in ['home.html','history.html','scripts.min.js','libs.min.js','style.css']:
    if not (UP/name).is_file():raise FileNotFoundError('Missing repository source: '+str(UP/name))


def fragment(source): return BeautifulSoup(source,'html.parser')
def replace_contents(node,source):
    node.clear()
    for item in list(fragment(source).contents):node.append(item)

from resume_content import PROFILE, EVENTS, render_history, render_about, esc
ED_PATH='/pl/historia/1945-49'; PR_PATH='/pl/historia/1950-59'; IN_PATH='/pl/historia/internships'
events=EVENTS

def prepare_common(soup,is_home):
    soup.html['lang']='zh-CN'
    soup.title.string='hello — 个人经历草稿'
    for node in soup.find_all(string=lambda x:isinstance(x,Comment)):node.extract()
    for script in list(soup.find_all('script')):
        if script.get('type')=='text/twig':continue
        src=script.get('src','')
        if src.startswith('/public/theme/js/'):continue
        if 'WebFontConfig' in script.get_text():
            script.string=script.get_text().replace('https://ajax.googleapis.com/ajax/libs/webfont/1.5.18/webfont.js','/public/theme/js/webfont.js')
        else:script.decompose()
    for node in soup.select('noscript, meta[property^="og:"], meta[name^="twitter:"], meta[property="fb:app_id"]'):node.decompose()
    desc=soup.find('meta',attrs={'name':'description'})
    if desc:desc['content']='从国际贸易到数据科学，记录教育、实习与项目实践。'
    symbol=soup.find('symbol',id='sprite-lalka_logo')
    if symbol:
        symbol.attrs.pop('viewbox',None)
        symbol['viewBox']='0 0 128 56'
        replace_contents(symbol,'<title>hello</title><text x="1" y="45" font-family="Georgia, serif" font-weight="bold" font-style="italic" font-size="51" letter-spacing="-4">hello</text>')
    for logo in soup.select('.header__logo a'):logo['title']='hello';logo['aria-label']='hello 首页'
    article=soup.select_one('article[data-page]');article['data-title']='hello — 个人经历';article['data-header-title']='' if is_home else '经历时间线'
    if article.h1:article.h1.string='hello' if is_home else '教育、实习与项目经历'
    for header in soup.select('.js-header-title'):header.string='' if is_home else '经历时间线'
    menu_fields=[('首页','/pl'),('教育经历',ED_PATH),('项目经历',PR_PATH),('全部经历','/pl/historia'),('实习经历',IN_PATH),('工具与方法','/pl/about'),('时间线','/pl/historia'),('关于我','/pl/about')]
    for item,(title,href) in zip(soup.select('.js-menu-item'),menu_fields):
        link=item.find('a');link['href']=href
        if link.find('span'):link.find('span').string=title
        if link.find('img'):link.find('img')['alt']=title
    for a in soup.select('.menu__bar a'):
        a['href']='/pl';a.attrs.pop('data-history',None)
        for span in a.select('span'):span.string='hello'
    small=soup.select_one('.menu__links ul')
    if small:replace_contents(small,'<li><a class="js-menu-left-item" href="/pl">回到首页</a></li><li><a class="js-menu-left-item" href="/pl/historia">全部经历</a></li><li><a class="js-menu-left-item" href="/pl/about">关于我</a></li>')
    cookie=soup.select_one('.coookies__text')
    if cookie:cookie.string='网站还在施工中。部分页面、交互和内容仍在完善，欢迎先逛逛，更多内容会陆续补上。'
    for b in soup.select('.js-cookies-agree'):
        for t in list(b.find_all(string=True)):
            if not t.find_parent('svg'):t.replace_with('知道了' if 'close' not in ' '.join(b.get('class',[])) else '关闭提示')
    for a in soup.select('.coookies a'):a['href']='/pl/about';replace_contents(a,'关于我')
    for n in soup.select('.footer__partner,.footer__icons,.js-newsletter'):n.decompose()
    footer=soup.select_one('footer')
    if footer:replace_contents(footer,'<div class="grid"><div class="grid-t-4"><p class="footer__title">hello</p><p>一段仍在继续的故事。</p></div><div class="grid-t-4"><p class="footer__title">数据与实践</p><p>从国际贸易到数据科学。<br>把研究、分析与开发连起来。</p></div><div class="grid-t-4"><p class="footer__title">了解更多</p><a href="/pl/about">查看关于我</a></div></div>')
    for el in soup.select('[data-comp="Scene"]'):
        settings=json.loads(el.get('data-options','{}'))
        if 'puppets' in settings:
            sets=settings['puppets'];sets=sets if isinstance(sets[0][0],list) else [sets]
            for puppet_set in sets:
                for index,puppet in enumerate(puppet_set):
                    event=events[index%len(events)]
                    if len(puppet)>5:puppet[5]=[event['type'],event['short'],event['period']]
            el['data-options']=json.dumps(settings,ensure_ascii=False,separators=(',',':'))
    # Keep original CSS first; overrides only make Chinese labels and hello fit.
    link=soup.new_tag('link',rel='stylesheet',href='/personal.css');soup.head.append(link)
    main_script=soup.find('script',src=lambda value:value and '/scripts.min.js' in value)
    script=soup.new_tag('script',src='/personal.js');main_script.insert_before(script)
    main_script['onload']='window.initializePersonalSite()'
    for text in list(soup.find_all(string=True)):
        if text.find_parent(['script','style']):continue
        replacements={'Menu':'菜单','Bilety':'经历','Włącz/wyłącz dźwięki':'开启或关闭声音','Następny rok':'下一年','Poprzedni rok':'上一年','Przejdź do głównej treści':'跳到主要内容','Zamknij':'关闭','Teatr Lalka':'hello'}
        stripped=text.strip()
        if stripped in replacements:text.replace_with(replacements[stripped])
    return soup

home=prepare_common(fragment((UP/'home.html').read_text(encoding='utf8')),True)
for selector,value in [('.show__promoter','从国际贸易到数据科学'),('.show__subtitle',PROFILE['headline']),('.show__author','蒙纳士大学 · 数据科学硕士在读'),('.show__title a','hello')]:
    for el in home.select(selector):el.string=value
for a in home.select('.show__title a'):a['href']='/pl/historia'
for side,value in [('.js-left','我的经历'),('.js-right','互动舞台')]:
    for el in home.select(side+' > span'):el.string=value
for ticket in home.select('.ticket-btn'):ticket['href']='/pl/historia';ticket.attrs.pop('target',None);ticket['aria-label']='查看经历时间线'
title=home.select_one('.infobar__title a');title['href']='/pl/historia';replace_contents(title,'<span>经</span><span>历</span>')
info=home.select_one('.infobar--home .js-wrapper')
replace_contents(info,''.join(f'<div class="infobar__item infobar__item--repertoire"><div class="repertoire__comp repertoire__comp--infobar"><div class="repertoire__month--infobar">{e["type"]}</div><div class="repertoire__date">{e["year"]}</div><div class="repertoire__day"></div><ul><li class="repertoire__show"><a href="{e["url"]}" data-sound-hover="underline"><span class="repertoire__hour">{e["start"][5:7]+"月" if len(e["start"])>4 else "入学"}</span><h3 class="repertoire__title">{esc(e["short"])}</h3></a></li></ul></div></div>' for e in events))
for a in home.select('a[href="/pl/kalendarz"]'):a['href']='/pl/historia';replace_contents(a,'查看完整经历')

history=prepare_common(fragment((UP/'history.html').read_text(encoding='utf8')),False)
render_history(history)
import copy
about=copy.deepcopy(home)
render_about(about)
pages={'home.html':home,'history.html':history,'about.html':about}
for name,soup in pages.items():
    for a in soup.select('a[href="/pl/historia"]'):a['href']='/pl/historia/all'
    for section in soup.select('.history-comp__section'):
        section['style']='--step-count:'+str(len(section.select('.js-slider-item')))+';'
    for label in soup.select('.scene h2.sr-only'):label.string='hello，欢迎来到我的空间'
    (SITE/name).write_text(str(soup),encoding='utf8')

asset_urls=set()
def asset(url,base=BASE+'/'):
    url=url.strip().replace('&amp;','&')
    if not url or url.startswith(('data:','#','javascript:')):return
    resolved=urllib.parse.urljoin(base,url);parts=urllib.parse.urlsplit(resolved)
    if parts.netloc!='teatrlalka.pl' or not parts.path.startswith('/public/'):return
    asset_urls.add(urllib.parse.urlunsplit((parts.scheme,parts.netloc,parts.path,'','')))
for soup in pages.values():
    for el in soup.select('[src],[poster],link[href]'):
        for attr in ['src','poster','href']:
            if el.get(attr):asset(el[attr])
    for el in soup.select('[srcset]'):
        for item in el['srcset'].split(','):asset(item.strip().split(' ')[0])
css=(UP/'style.css').read_text(encoding='utf8')
for url in re.findall(r'url\([\"\x27]?([^\)\"\x27]+)',css):asset(url,BASE+'/public/theme/css/style.css')
script=(UP/'scripts.min.js').read_text(encoding='utf8')
matches=list(re.finditer(r'assetsPath="([^"]+)"',script))
for i,m in enumerate(matches):
    end=matches[i+1].start() if i+1<len(matches) else len(script)
    segment=script[m.end():end]
    for name in re.findall(r'(?:imageSrc|altImageSrc|image):"([^"/]+)"',segment):asset(m.group(1)+name+'.png')
for name in re.findall(r'"([^"/]+\.(?:mp3|wav))"',script):asset('/public/theme/sounds/'+name)
asset('/public/theme/js/webfont.js')
asset_urls.discard(BASE+'/public/theme/js/webfont.js')
failures=[];manifest=[]
def fetch(url):
    path=urllib.parse.unquote(urllib.parse.urlsplit(url).path);dest=SITE/path.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        if not dest.exists():
            if not OPTIONS.fetch_assets:raise FileNotFoundError('Missing bundled asset; restore it from Git or explicitly use --fetch-assets')
            encoded=urllib.parse.quote(url,safe=':/?=&%')
            with urllib.request.urlopen(encoded,timeout=35) as response:data=response.read()
            dest.write_bytes(data)
        data=dest.read_bytes()
        return {'path':path,'source':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    except Exception as exc:return {'path':path,'source':url,'error':str(exc)}
print('Checking',len(asset_urls),'bundled assets',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    for i,result in enumerate(pool.map(fetch,sorted(asset_urls)),1):
        (failures if 'error' in result else manifest).append(result)
        if i%25==0:print('Processed',i,flush=True)
webfont=SITE/'public/theme/js/webfont.js';webfont.parent.mkdir(parents=True,exist_ok=True)
if not webfont.exists():
    if not OPTIONS.fetch_assets:raise FileNotFoundError('Missing bundled webfont.js')
    webfont.write_bytes(urllib.request.urlopen('https://ajax.googleapis.com/ajax/libs/webfont/1.5.18/webfont.js',timeout=30).read())
if failures:raise RuntimeError('Missing build assets: '+json.dumps(failures,ensure_ascii=False))
manifest.append({'path':'/public/theme/js/webfont.js','source':'https://ajax.googleapis.com/ajax/libs/webfont/1.5.18/webfont.js','bytes':webfont.stat().st_size})
# Pin the main code to the captured reference version used for the field transformation.
for file,source in [('public/theme/js/scripts.min.js','scripts.min.js'),('public/theme/js/libs.min.js','libs.min.js'),('public/theme/css/style.css','style.css')]:
    target=SITE/file;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(UP/source,target)
# The source server returns an empty Din700 WOFF; reconstruct it from its valid TTF.
bold_woff=SITE/'public/theme/fonts/Din/Din700.woff'
if not bold_woff.stat().st_size:
    from fontTools.ttLib import TTFont
    font=TTFont(SITE/'public/theme/fonts/Din/Din700.ttf')
    font.flavor='woff';font.save(bold_woff)
for item in manifest:
    data=(SITE/item['path'].lstrip('/')).read_bytes()
    item['bytes']=len(data);item['sha256']=hashlib.sha256(data).hexdigest()
    if item['path']=='/public/theme/fonts/Din/Din700.woff':
        item['local_repair']='Rebuilt from source Din700.ttf because source WOFF is empty.'
(ROOT/'asset-manifest.json').write_text(json.dumps({'source':BASE,'assets':manifest,'failures':failures},ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'fields.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'assets':len(manifest),'bytes':sum(a['bytes'] for a in manifest),'failures':failures},ensure_ascii=False),flush=True)

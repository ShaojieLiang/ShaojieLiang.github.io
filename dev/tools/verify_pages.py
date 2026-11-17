"""Check exported routes through a plain static server, without browser automation."""
import argparse, concurrent.futures, hashlib, json, os, pathlib, re, sys, urllib.parse, urllib.request
from bs4 import BeautifulSoup
from export_pages import ROUTES, SITE

parser=argparse.ArgumentParser()
parser.add_argument('directory',type=pathlib.Path)
parser.add_argument('--base',default='http://127.0.0.1:4181')
args=parser.parse_args();root=args.directory.resolve()
urls={'/','/me/','/pl/historia/','/true-camera-mirror/'}
for route in ['']+list(ROUTES):
    page=root/route.lstrip('/')/'index.html'
    soup=BeautifulSoup(page.read_text(encoding='utf8'),'html.parser')
    urls.add(route+'/')
    assert '网站还在施工中' in soup.get_text()
    assert '跳过开场' not in str(soup)
    scripts=[s.get('src') for s in soup.select('script[src]')]
    main=next(src for src in scripts if '/scripts.min.js' in src)
    assert scripts.index('/personal.js')<scripts.index(main)
    assert soup.find('script',src=main)['onload']=='window.initializePersonalSite()'
    for node in soup.select('[href],[src],[data-url],[data-section-path],[data-slider-path],[data-text-path]'):
        for key in ['href','src','data-url','data-section-path','data-slider-path','data-text-path']:
            value=node.get(key,'')
            if value.startswith('/'):
                parsed=urllib.parse.urlsplit(value)
                if parsed.path.startswith('/pl'):assert parsed.path.endswith('/'),value
                urls.add(value)
    for section in soup.select('.history-comp__section'):
        paths=[n['data-slider-path'] for n in section.select('[data-slider-path]')]
        assert len(paths)==len(set(paths))
        assert set(paths)=={n['data-text-path'] for n in section.select('[data-text-path]')}
        assert all(urllib.parse.urlsplit(p).path==section['data-section-path'] for p in paths)
for file in root.rglob('*'):
    if file.is_file() and file.relative_to(root).parts[0] not in {'.git','.venv','venv','dev','dist','__pycache__','node_modules'}:
        rel='/'+file.relative_to(root).as_posix()
        if not rel.startswith('/resources/') and rel!='/.nojekyll':urls.add(rel)
for name in ['scripts.min.js','libs.min.js']:
    rel='public/theme/js/'+name
    assert (root/rel).read_bytes()==(SITE/rel).read_bytes()
assert 'personal-skip' not in (root/'personal.js').read_text(encoding='utf8')
def check(value):
    url=args.base.rstrip('/')+urllib.parse.quote(value.split('#')[0],safe='/?=&%')
    with urllib.request.urlopen(urllib.request.Request(url,headers={'X-Requested-With':'XMLHttpRequest'}),timeout=20) as response:
        body=response.read();assert response.status==200,url
        assert body,url
        if value.startswith('/pl/historia/') and '?' in value:
            soup=BeautifulSoup(body.decode('utf8'),'html.parser')
            assert soup.find(attrs={'data-text-path':value}),value
    return value
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:checked=list(pool.map(check,sorted(urls)))
print(json.dumps({'checked_urls':len(checked),'base':args.base,'static_routes_valid':True,'original_animation_js_preserved':True}))

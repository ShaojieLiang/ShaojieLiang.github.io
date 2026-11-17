"""Check local dependencies, preserved upstream code, and HTTP navigation without a browser."""
import os, sys, pathlib, re, urllib.parse, urllib.request, concurrent.futures, json
from bs4 import BeautifulSoup

root=pathlib.Path(__file__).resolve().parents[1]
site=root/'site'
urls=set(['/pl','/pl/about','/pl/historia'])
content=json.loads((root/'content.json').read_text(encoding='utf8'))
expected_ids={e['id'] for e in content['events']}
all_html=''
for filename in ['home.html','history.html','about.html']:
    page=(site/filename).read_text(encoding='utf8');all_html+=page
    soup=BeautifulSoup(page,'html.parser')
    assert soup.select_one('#content article[data-page]'), filename
    assert soup.find('symbol',id='sprite-lalka_logo').text=='hellohello'
    for el in soup.select('[src],link[href],a[href]'):
        value=el.get('src') or el.get('href')
        if value.startswith('/'):
            urls.add(value)
        else:
            assert value.startswith(('#','data:')), (filename,value)
    for section in soup.select('.history-comp__section'):
        steps=section.select('[data-slider-path]')
        texts={n['data-text-path'] for n in section.select('[data-text-path]')}
        paths=[n['data-slider-path'] for n in steps]
        assert len(paths)==len(set(paths)), 'Repeated-year events must have unique routes'
        if section['data-section-path']=='/pl/historia/all':
            assert {urllib.parse.parse_qs(urllib.parse.urlsplit(p).query)['rok'][0] for p in paths}==expected_ids
        else:
            assert len(steps)=={'/pl/historia/1945-49':2,'/pl/historia/1950-59':4,'/pl/historia/internships':3}[section['data-section-path']]
        for index,node in enumerate(steps):
            assert node['data-slider-path'] in texts
            assert bool(node.select_one('.js-step-prev'))==(index>0)
            assert bool(node.select_one('.js-step-next'))==(index<len(steps)-1)
    for ref in soup.select('use'):
        href=ref.get('xlink:href','')
        assert not href.startswith('#') or soup.find(id=href[1:]), href

assert '待填写' not in all_html and '示意年份' not in all_html
# Only labels may change: keep every puppet's name, position, scale and settings.
home=BeautifulSoup((site/'home.html').read_text(encoding='utf8'),'html.parser')
original=BeautifulSoup((root/'upstream/home.html').read_text(encoding='utf8'),'html.parser')
current_settings=json.loads(home.select_one('[data-comp="Scene"]')['data-options'])
original_settings=json.loads(original.select_one('[data-comp="Scene"]')['data-options'])
assert [[p[:5] for p in group] for group in current_settings['puppets']]==[[p[:5] for p in group] for group in original_settings['puppets']]
assert not re.search(r'(?<!\d)1[3-9]\d{9}(?!\d)',all_html)
visible_text=BeautifulSoup(all_html,'html.parser').get_text(' ',strip=True)
assert not re.search(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}',visible_text)
assert 'mailto:' not in all_html
assert '同月随机留出测试集' in all_html and '本地对照测试' in all_html

for filename in ['public/theme/css/style.css','personal.css']:
    css=(site/filename).read_text(encoding='utf8')
    for value in re.findall(r'url\([\"\x27]?([^\)\"\x27]+)',css):
        if not value.startswith('data:'):
            urls.add(urllib.parse.urljoin('/'+filename,value))

for local,source in [('public/theme/js/scripts.min.js','scripts.min.js'),('public/theme/js/libs.min.js','libs.min.js'),('public/theme/css/style.css','style.css')]:
    assert (site/local).read_bytes()==(root/'upstream'/source).read_bytes(), source

manifest=json.loads((root/'asset-manifest.json').read_text(encoding='utf8'))
assert not manifest['failures']
urls.update(item['path'] for item in manifest['assets'])
def check(url):
    request=urllib.request.Request('http://127.0.0.1:4180'+urllib.parse.quote(url.split('#')[0],safe='/?=&%'),headers={'X-Requested-With':'XMLHttpRequest'})
    try: response=urllib.request.urlopen(request,timeout=10)
    except Exception as error: raise AssertionError((url,str(error))) from error
    with response:
        assert response.status==200, url
        body=response.read()
        assert body, url
        if url.startswith('/pl'):
            assert b'id="content"' in body, url
        elif url.split('?')[0].endswith('.png'):
            assert body.startswith(b'\x89PNG'), url
        elif url.split('?')[0].endswith(('.jpg','.jpeg')):
            assert body.startswith(b'\xff\xd8'), url
    return url
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    checked=list(pool.map(check,sorted(urls)))
print(json.dumps({'http_paths_checked':len(checked),'assets':len(manifest['assets']),'upstream_files_unchanged':3,'timeline_sections':4,'resume_events':len(expected_ids),'puppet_geometry_unchanged':True,'visual_browser_test':False}))

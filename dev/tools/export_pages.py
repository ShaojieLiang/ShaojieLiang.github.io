"""Export the local draft as real static routes for GitHub Pages."""
import argparse, hashlib, json, os, pathlib, re, shutil, sys, urllib.parse
from bs4 import BeautifulSoup

ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
ROUTES={
    '/pl': 'home.html',
    '/pl/about': 'about.html',
    '/pl/historia/all': 'history.html',
    '/pl/historia/1945-49': 'history.html',
    '/pl/historia/1950-59': 'history.html',
    '/pl/historia/internships': 'history.html',
}
def canonical(value):
    parsed=urllib.parse.urlsplit(value)
    if parsed.scheme or parsed.netloc:return value
    if parsed.path in ROUTES:
        return urllib.parse.urlunsplit(('', '', parsed.path+'/', parsed.query, parsed.fragment))
    return value

def render(filename):
    soup=BeautifulSoup((SITE/filename).read_text(encoding='utf8'),'html.parser')
    for node in soup.find_all(True):
        for key,value in list(node.attrs.items()):
            if isinstance(value,str) and value.startswith('/pl'):node[key]=canonical(value)
    return str(soup)

def export(destination):
    destination=destination.resolve()
    destination.mkdir(parents=True,exist_ok=True)
    # Copy only serving files: no résumé PDF, private notes, or local source captures.
    shutil.copytree(SITE/'public',destination/'public',dirs_exist_ok=True)
    # Four obsolete SVG font fallbacks are upstream HTML error pages.
    # Valid WOFF2, WOFF and TTF fonts remain available for every face.
    css_path=destination/'public/theme/css/style.css'
    css=css_path.read_text(encoding='utf8')
    for font_path in (destination/'public/theme/fonts/Din').glob('*.svg'):
        if b'<!doctype html' in font_path.read_bytes()[:200].lower():
            css=re.sub(r',url\("\.\./fonts/Din/'+re.escape(font_path.name)+r'#[^"]+"\) format\("svg"\)', '', css)
            font_path.unlink()
    css_path.write_text(css,encoding='utf8')
    for name in ['personal.js','personal.css','personal-ticket.svg']:
        shutil.copyfile(SITE/name,destination/name)
    pages={name:render(name) for name in set(ROUTES.values())}
    (destination/'index.html').write_text(pages['home.html'],encoding='utf8')
    for route,filename in ROUTES.items():
        folder=destination/route.lstrip('/');folder.mkdir(parents=True,exist_ok=True)
        (folder/'index.html').write_text(pages[filename],encoding='utf8')
    for alias,target in [('me','/'),('pl/historia','/pl/historia/all/')]:
        folder=destination/alias;folder.mkdir(parents=True,exist_ok=True)
        (folder/'index.html').write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}"><title>hello</title><a href="{target}">继续访问 hello</a></html>',encoding='utf8')
    (destination/'.nojekyll').write_text('',encoding='utf8')
    # Use the available touch icon instead of two missing upstream Android icons.
    manifest=destination/'public/theme/favicons/manifest.json'
    manifest.write_text(json.dumps({'name':'hello','short_name':'hello','start_url':'/','icons':[{'src':'/public/theme/favicons/apple-touch-icon.png','sizes':'180x180','type':'image/png'}],'theme_color':'#1e0eb6','background_color':'#ffffff','display':'standalone'},indent=2),encoding='utf8')
    shutil.copyfile(ROOT/'README.github.md',destination/'README.md')
    (destination/'docs').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'readme-assets/cover.svg',destination/'docs/cover.svg')
    files=[p for p in destination.rglob('*') if p.is_file() and '.git' not in p.parts]
    print(json.dumps({'output':str(destination),'files':len(files),'static_routes':list(ROUTES),'bytes':sum(p.stat().st_size for p in files)},ensure_ascii=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=pathlib.Path)
    export(parser.parse_args().destination)

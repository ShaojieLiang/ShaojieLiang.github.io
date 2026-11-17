"""Render curated résumé fields into the reference site's existing components."""
import copy, html, json, pathlib
from bs4 import BeautifulSoup

ROOT=pathlib.Path(__file__).resolve().parents[1]
CONTENT=json.loads((ROOT/'content.json').read_text(encoding='utf8'))
PROFILE=CONTENT['profile']
CATEGORIES=[('education','教育经历','/pl/historia/1945-49'),('internships','实习经历','/pl/historia/internships'),('projects','项目经历','/pl/historia/1950-59')]
EVENTS=sorted(CONTENT['events'],key=lambda event:event['start'])
for event in EVENTS:
    _,event['type'],event['group']=next(c for c in CATEGORIES if c[0]==event['category'])
    event['url']=event['group']+'?rok='+event['id']
    event['all_url']='/pl/historia/all?rok='+event['id']

def esc(text):return html.escape(str(text),quote=True)
def fragment(text):return BeautifulSoup(text,'html.parser')
def contents(node,text):
    node.clear()
    for child in list(fragment(text).contents):node.append(child)

def render_history(history):
    template=copy.deepcopy(history.select_one('[data-section-path="/pl/historia/1950-59"]'))
    cards=[copy.deepcopy(n) for n in template.select('[data-slider-path]')[:3]]
    text_template=copy.deepcopy(template.select_one('[data-text-path]'))
    tabs=history.select_one('[data-comp="Tabs"]')
    for section in list(history.select('.history-comp__section')):section.decompose()
    groups=[('all','全部经历','/pl/historia/all')]+CATEGORIES
    for category,label,path in groups:
        entries=[e for e in EVENTS if category=='all' or e['category']==category]
        section=copy.deepcopy(template)
        section['data-section-path']=path
        section.select_one('.js-year-title').string=label
        section.select_one('.js-panel-toggle')['data-url']=path
        card_list=section.select_one('.js-slider-wrap > ul');card_list.clear()
        text_list=section.select_one('.js-sidePanel > ul');text_list.clear()
        for index,event in enumerate(entries):
            route=event['all_url'] if category=='all' else event['url']
            node=copy.deepcopy(cards[index%len(cards)]);node['data-slider-path']=route
            for a in node.select('a'):a['href']=route
            for a in node.select('.js-history-link'):a['data-history']='false';a.attrs.pop('target',None)
            for image in node.select('img'):image['alt']='原站视觉占位图，非个人经历实拍'
            for span in node.select('.js-step-toggle span'):span.string=event['year']
            toggle=node.select_one('.js-step-toggle');toggle['aria-label']=event['period']+'，'+event['title']
            date=node.select_one('.history-comp__date')
            caption=fragment(f'<small class="personal-event-label">{esc(event["short"])}</small>').small
            date.append(caption)
            for button in node.select('.js-step-prev,.js-step-next'):button.decompose()
            for direction,needed in [('prev',index>0),('next',index<len(entries)-1)]:
                if needed:
                    icon='left' if direction=='prev' else 'right'
                    title='上一段经历' if direction=='prev' else '下一段经历'
                    date.append(fragment(f'<button class="history-comp__button--{direction} js-step-{direction}"><svg class="sprite-arrow_{icon}-small"><use xlink:href="#sprite-arrow_{icon}-small"></use></svg><span class="sr-only">{title}</span></button>').button)
            card_list.append(node)
            detail=copy.deepcopy(text_template);detail['data-text-path']=route
            paragraphs=''.join('<p>'+esc(text)+'</p>' for text in event['details'])
            results=''.join('<p>'+esc(text)+'</p>' for text in event.get('results',[]))
            contents(detail,f'<p class="personal-detail-kind">{esc(event["type"])} · {esc(event["period"])}</p><h2>{esc(event["title"])}</h2><p class="personal-role">{esc(event["role"])}</p><p>{esc(event["summary"])}</p>{paragraphs}'+('<h3>成果与记录</h3>'+results if results else '')+f'<p class="personal-detail-tags">{esc(" / ".join(event["tags"]))}</p><p class="personal-placeholder">配图沿用原站视觉素材，非这段经历的实拍。</p>')
            text_list.append(detail)
        tabs.append(section)
    bar=history.select_one('.infobar--history .js-wrapper')
    contents(bar,''.join(f'<a data-history="replace" href="{path}" class="infobar__btn infobar__btn--history js-tab"><span>{label}</span><span class="infobar__progress"></span></a>' for _,label,path in groups))

def render_about(about):
    article=about.select_one('article[data-page]')
    article.attrs.pop('data-home',None);article['data-info']='';article['data-title']='关于我';article['data-header-title']='关于我'
    skills=''.join(f'<div><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></div>' for item in PROFILE['skills'])
    contents(article,f'<section class="personal-about"><h1>hello</h1><p class="personal-about-name">{esc(PROFILE["name"])} · {esc(PROFILE["headline"])}</p><p>{esc(PROFILE["intro"])}</p><p>{esc(PROFILE["focus"])}</p><h2>工具与方法</h2><div class="personal-skills">{skills}</div><h2>荣誉</h2><p>{"<br>".join(esc(a) for a in PROFILE["awards"])}</p><h2>课堂与工作之外</h2><p>{esc(PROFILE["outside"])}</p><p><a href="/pl/historia/all">沿时间线了解我 →</a></p><p class="personal-site-note">本地草稿：动效与视觉素材参考 Teatr Lalka，经历文字整理自个人简历。当前配图为视觉占位。</p></section>')

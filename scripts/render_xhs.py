#!/usr/bin/env python3
"""
小红书卡片渲染脚本 - GitHub级排版 + 标点级贪婪填充
功能：完美支持自动折行、彻底消除底部留白
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import List

try:
    import markdown
    import yaml
    from playwright.async_api import async_playwright
except ImportError:
    print("缺少依赖，请运行: pip install markdown pyyaml playwright && playwright install chromium")
    sys.exit(1)

def parse_markdown_file(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    metadata = yaml.safe_load(yaml_match.group(1)) if yaml_match else {}
    body = content[yaml_match.end():] if yaml_match else content
    return {'metadata': metadata, 'body': body.strip()}

def generate_cover_html(metadata: dict, theme: str, body_text: str = "") -> str:
    emoji = metadata.get('emoji', '')
    title = metadata.get('title', '标题')
    subtitle = metadata.get('subtitle', '')
    body_html = markdown.markdown(body_text, extensions=['extra', 'nl2br']) if body_text else ""
    
    t_size = 120 if len(title) <= 6 else 100 if len(title) <= 10 else 80 if len(title) <= 18 else 65
    s_size = 72 if len(subtitle) <= 12 else 60 if len(subtitle) <= 20 else 48
    
    bg = "linear-gradient(180deg, #0D1117 0%, #21262D 100%)" if theme == 'terminal' else "linear-gradient(180deg, #f3f3f3 0%, #f9f9f9 100%)"
    t_color = "#39d353" if theme == 'terminal' else "#111"
    s_color = "#888" if theme == 'terminal' else "#333"
    inner_bg = "#0d1117" if theme == 'terminal' else "#F3F3F3"
    border_color = "#333" if theme == 'terminal' else "#ddd"
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:"Noto Sans SC",sans-serif;width:1080px;height:1440px;overflow:hidden;}}
.container{{width:1080px;height:1440px;background:{bg};position:relative;padding:65px;}}
.inner{{background:{inner_bg};border-radius:25px;height:1310px;display:flex;flex-direction:column;padding:80px;box-shadow:0 10px 40px rgba(0,0,0,0.3);}}
.emoji{{font-size:150px;margin-bottom:30px;}}
.title{{font-weight:900;font-size:{t_size}px;line-height:1.3;color:{t_color};margin-bottom:20px; word-wrap:break-word; overflow-wrap:break-word;}}
.subtitle{{font-weight:400;font-size:{s_size}px;color:{s_color};margin-bottom:50px;padding-bottom:20px;border-bottom:2px solid {border_color}; word-wrap:break-word; overflow-wrap:break-word;}}
.cover-body{{flex:1;font-size:38px;line-height:1.6;color:#ccc;overflow:hidden; word-wrap:break-word; overflow-wrap:break-word;}}
.cover-body p{{margin-bottom:20px;}}
.cover-body strong{{color:#39d353;font-weight:700;}}
</style></head><body><div class="container"><div class="inner">
{f'<div class="emoji">{emoji}</div>' if emoji else ""}
<div class="title">{title}</div>
{f'<div class="subtitle">{subtitle}</div>' if subtitle else ""}
<div class="cover-body">{body_html}</div>
</div></div></body></html>'''

def generate_card_html(content: str, theme: str, page_num: int, total: int) -> str:
    html_body = markdown.markdown(content, extensions=['extra', 'nl2br'])
    bg = "linear-gradient(135deg, #0D1117 0%, #161B22 100%)" if theme == 'terminal' else "linear-gradient(180deg, #f3f3f3 0%, #f9f9f9 100%)"
    text_color = "#c9d1d9" if theme == 'terminal' else "#475569"
    inner_bg = "rgba(13, 17, 23, 0.95)" if theme == 'terminal' else "rgba(255, 255, 255, 0.95)"
    h_color = "#39d353" if theme == 'terminal' else "#1e293b"
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:"Noto Sans SC",sans-serif;width:1080px;height:1440px;overflow:hidden;background:transparent;}}
.container{{width:1080px;height:1440px;background:{bg};padding:50px;position:relative;}}
.inner{{background:{inner_bg};border-radius:20px;padding:50px 60px;height:1340px;box-shadow:0 8px 32px rgba(0,0,0,0.2);}}
.content{{
    font-size:36px;
    line-height:1.6;
    color:{text_color};
    word-wrap: break-word;
    overflow-wrap: break-word;
}}
.content pre {{ white-space: pre-wrap; word-break: break-word; background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; }}
.content code {{ font-family: monospace; color: #f0e68c; background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px; }}
.content h1, .content h2 {{color:{h_color};margin-bottom:20px;font-weight:900;font-size:48px;}}
.content p {{margin-bottom:15px;}}
.content strong {{color:#39d353;font-weight:700;}}
.content blockquote {{border-left:8px solid #39d353;padding:15px 30px;background:rgba(57,211,83,0.05);margin:20px 0;border-radius:0 12px 12px 0;font-style:italic;}}
.content blockquote p {{margin-bottom:0;color:#888;font-size:34px;}}
.page-num{{position:absolute;bottom:60px;right:80px;font-size:32px;color:#555;font-weight:700;}}
</style></head><body><div class="container"><div class="inner"><div class="content">{html_body}</div></div><div class="page-num">{page_num}/{total}</div></div></body></html>'''

async def split_content(body: str, theme: str) -> List[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1080, 'height': 1440})
        
        async def fits(text):
            if not text.strip(): return True
            await page.set_content(generate_card_html(text, theme, 1, 1))
            # 极限高度探测，1220px为安全边界
            return await page.evaluate("document.querySelector('.content').scrollHeight <= 1220")

        cards = []
        current_text = ""
        
        # 1. 拆分为 Markdown 段落块
        paragraphs = body.split('\n\n')
        
        for para in paragraphs:
            connector = "\n\n" if current_text else ""
            test_text = current_text + connector + para
            
            if await fits(test_text):
                current_text = test_text
            else:
                # 2. 如果段落放不下，拆分为行
                lines = para.split('\n')
                for i, line in enumerate(lines):
                    line_connector = "\n\n" if current_text and i == 0 else ("\n" if current_text else "")
                    test_line = current_text + line_connector + line
                    
                    if await fits(test_line):
                        current_text = test_line
                    else:
                        # 3. 如果连一行都放不下，按标点符号拆分为短语 (逗号, 句号等)
                        # 这样可以像倒沙子一样填满最后的空间
                        segments = re.split(r'([。！？；，,.]\s*)', line)
                        phrases = []
                        tmp = ""
                        for seg in segments:
                            tmp += seg
                            if re.search(r'[。！？；，,.]\s*$', seg):
                                phrases.append(tmp)
                                tmp = ""
                        if tmp: phrases.append(tmp)
                        
                        for j, phrase in enumerate(phrases):
                            phrase_connector = line_connector if j == 0 else ""
                            test_phrase = current_text + phrase_connector + phrase
                            
                            if await fits(test_phrase):
                                current_text = test_phrase
                            else:
                                # 卡片彻底满了，封版
                                if current_text:
                                    cards.append(current_text)
                                    current_text = phrase # 溢出部分放到下一张卡片
                                else:
                                    # 极端异常：连一个短语都超出一整页
                                    cards.append(phrase)
                                    current_text = ""
        
        if current_text:
            cards.append(current_text)
            
        await browser.close()
        return cards

async def main_task(md_file, output_dir, theme):
    os.makedirs(output_dir, exist_ok=True)
    data = parse_markdown_file(md_file)
    print(f"🎨 执行 Github 级排版 + 标点贪婪填充...")
    card_contents = await split_content(data['body'], theme)
    total = len(card_contents)
    is_single_page = total == 1 and len(card_contents[0]) < 600
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1080, 'height': 1440})
        
        if metadata := data.get('metadata'):
            if is_single_page:
                await page.set_content(generate_cover_html(metadata, theme, body_text=card_contents[0]))
                await page.screenshot(path=os.path.join(output_dir, "cover.png"))
                print("  ✅ 已生成单图 (cover.png)"); await browser.close(); return
            await page.set_content(generate_cover_html(metadata, theme))
            await page.screenshot(path=os.path.join(output_dir, "cover.png"))
            
        for i, content in enumerate(card_contents, 1):
            await page.set_content(generate_card_html(content, theme, i, total))
            await page.screenshot(path=os.path.join(output_dir, f"card_{i}.png"))
            print(f"  ✅ 卡片 {i}/{total} 已生成")
        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--output-dir', '-o', default='output')
    parser.add_argument('--theme', '-t', default='terminal')
    args = parser.parse_args()
    asyncio.run(main_task(args.file, args.output_dir, args.theme))

"""Render the two completed PDFs for page-by-page visual review."""
from pathlib import Path
import argparse
import json
import subprocess

import pdfplumber
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE/'build'/'visual-review')
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for name in ('manuscript', 'supplement'):
        subprocess.run(['pdftoppm', '-png', '-r', '108', str(HERE / f'{name}.pdf'),
                        str(out / name)], check=True)
        document = pdfplumber.open(HERE / f'{name}.pdf')
        pages = []
        thumbnails = []
        for index, page in enumerate(document.pages):
            path = out / f'{name}-{index+1:02}.png'
            text = page.extract_text() or ''
            outside = []
            body_into_footer = []
            for char in page.chars:
                if min(char['x0'], char['top']) < -0.5 or char['x1'] > page.width + 0.5 or char['bottom'] > page.height + 0.5:
                    outside.append(char['text'])
                if char['bottom'] > page.height-53 and abs(char['size']-7.2) > 0.05:
                    body_into_footer.append(char['text'])
            pages.append(dict(page=index+1, characters=len(text), outside_page=outside,
                              body_into_footer=''.join(body_into_footer),
                              replacement_character='\ufffd' in text,
                              text_start=text[:180], image=path.name))
            with Image.open(path) as image:
                image.thumbnail((390, 552))
                thumb = Image.new('RGB', (410, 590), 'white')
                thumb.paste(image, ((410-image.width)//2, 25))
                ImageDraw.Draw(thumb).text((12, 6), f'{name}  {index+1}', fill='black')
                thumbnails.append(thumb)
        for offset in range(0, len(thumbnails), 6):
            sheet = Image.new('RGB', (1230, 1180), '#cbd2d8')
            for j, thumb in enumerate(thumbnails[offset:offset+6]):
                sheet.paste(thumb, ((j % 3)*410, (j//3)*590))
            sheet.save(out / f'{name}-contact-{offset//6+1:02}.png')
        report[name] = dict(page_count=len(document.pages), pages=pages,
                            visual_review_still_required=True)
        document.close()
    (out/'render-summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v['page_count'] for k, v in report.items()}))


if __name__ == '__main__':
    main()

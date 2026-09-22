"""Prepare page pairs and text/layout facts for actual human-visible review."""
from pathlib import Path
import json
import fitz
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RENDER = ROOT / 'tmp/pdfs/20260921-final'


def main():
    report = {}
    pairs = RENDER / 'page-pairs'
    pairs.mkdir(exist_ok=True)
    for name in ('manuscript', 'supplement'):
        doc = fitz.open(HERE / f'{name}.pdf')
        pages = sorted((RENDER / name).glob('page-*.png'))
        assert len(pages) == len(doc), (name, len(pages), len(doc))
        data = {'page_count': len(doc), 'pages': [], 'page_pairs': []}
        all_text = []
        for number, page in enumerate(doc, 1):
            text = page.get_text()
            all_text.append(text)
            spans = [span for block in page.get_text('dict')['blocks']
                     for line in block.get('lines', []) for span in line['spans']]
            outside = [span['text'] for span in spans
                       if span['bbox'][0] < -0.5 or span['bbox'][1] < -0.5
                       or span['bbox'][2] > page.rect.width + .5
                       or span['bbox'][3] > page.rect.height + .5]
            data['pages'].append({'page': number, 'text_characters': len(text),
                                  'image_count': len(page.get_images()),
                                  'text_outside_page': outside,
                                  'first_lines': text.splitlines()[:5]})
        text = '\n'.join(all_text)
        data['allen_cahn_doi_visible_count'] = text.count('90196-2')
        data['unexpanded_placeholders'] = [x for x in ('{{TABLE:', '{{REFERENCES}}') if x in text]
        (RENDER / f'{name}-extracted.txt').write_text(text, encoding='utf-8')
        for start in range(0, len(pages), 2):
            images = [Image.open(p).convert('RGB') for p in pages[start:start + 2]]
            width = sum(im.width for im in images) + 24 * (len(images) + 1)
            height = max(im.height for im in images) + 60
            sheet = Image.new('RGB', (width, height), '#e5e7eb')
            draw = ImageDraw.Draw(sheet)
            x = 24
            for offset, im in enumerate(images):
                draw.text((x, 12), f'{name} page {start + offset + 1}', fill='black')
                sheet.paste(im, (x, 36))
                x += im.width + 24
                im.close()
            path = pairs / f'{name}-{start+1:02d}-{min(start+2,len(pages)):02d}.png'
            sheet.save(path)
            data['page_pairs'].append(path.relative_to(ROOT).as_posix())
        report[name] = data
    (RENDER / 'layout-review-inputs.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: {k: value[k] for k in ('page_count', 'allen_cahn_doi_visible_count',
                                                'unexpanded_placeholders')}
                      for key, value in report.items()}))


if __name__ == '__main__':
    main()

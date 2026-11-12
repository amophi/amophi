"""amophi 프로필 README 에 들어가는 그림을 만든다.

사용:
    python tools/build.py                 # assets/ko, assets/en 에 모두 만든다
    python tools/build.py --only hero     # 일부만
    python tools/build.py --phone         # 좁은 화면용 배치를 강제로 보이게(미리 보기용, 다른 폴더에 저장할 때)

그림마다 넓은 화면용 배치(.dt)와 좁은 화면용 배치(.ph)가 함께 들어 있고,
그려지는 폭이 560px 이하이면 좁은 화면용이 보인다(그림 안의 @media).
문구는 tools/text.json, 실제 화면 그림은 tools/pictures 에 있다.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from svgkit import Canvas, Face, font_dir  # noqa: E402
PICS = os.path.join(HERE, 'pictures')

W = 1200
SCREEN = '#060B18'   # 앱 화면의 바탕(어두운 남색)
PAPER = '#FFFFFF'
INK = '#0B0F17'
SOFT = '#5B6475'
ACCENT = '#3182F6'   # SOVIS 파랑
AMBIENT, SPEECH, DANGER = '#B9BEC8', '#F2DD1B', '#E5262B'   # 환경음 · 사람 소리 · 위협음
THEMES = {
    'dark': {'ink': '#F0F3F6', 'soft': '#9DA7B3', 'inverse': '#F0F3F6', 'on_inverse': '#0B0F17'},
    'light': {'ink': '#1F2328', 'soft': '#59636E', 'inverse': '#0B0F17', 'on_inverse': '#F0F3F6'},
}
RESPONSIVE = '.ph{display:none}@media (max-width:560px){.dt{display:none}.ph{display:inline}}'
FORCE_PHONE = '.dt{display:none}'

# 작업 패널: 차례, 그림(없으면 바탕색), 글자색
WORK = [
    ('sv', 'work_sv.jpg', None, '#FFFFFF'),
    ('androidpanel', None, '#18243A', '#FFFFFF'),
    ('pildong', 'work_pildong.jpg', None, '#FFFFFF'),
    ('solarljos', None, '#F4A300', '#0B0F17'),
    ('highschool', 'work_highschool.jpg', None, '#FFFFFF'),
    ('gcs', None, '#E6E9EE', '#0B0F17'),
    ('dead0', 'work_dead0.jpg', None, '#FFFFFF'),
]


def cycle_css(name, count, hold, fade):
    """count 개의 장면이 hold 초씩 차례로 보이도록, 서서히 바뀌는 CSS 를 만든다.

    움직임이 아니라 투명도만 바꾸므로 '움직임 줄이기' 설정에서도 그대로 둔다.
    애니메이션을 못 쓰는 곳에서는 첫 장면만 보인다(나머지는 opacity 0 속성).
    """
    total = count * hold
    a = (hold - fade) / total * 100
    b = hold / total * 100
    c = (total - fade) / total * 100
    css = (f'@keyframes {name}{{0%{{opacity:1}}{a:.2f}%{{opacity:1}}{b:.2f}%{{opacity:0}}'
           f'{c:.2f}%{{opacity:0}}100%{{opacity:1}}}}'
           f'.{name}{{animation:{name} {total:g}s linear infinite}}')
    for i in range(1, count):
        css += f'.{name}{i}{{animation-delay:{i * hold - total:g}s}}'
    return css


def state(name, index):
    """장면 index 에 붙일 class 와 처음 투명도 속성."""
    cls = name if index == 0 else f'{name} {name}{index}'
    return f' class="{cls}" opacity="{1 if index == 0 else 0}"'


def _side(ax, ay, bx, by, nx, ny, amount, pos):
    """A 에서 B 로 가는 변. 가운데쯤(pos)이 (nx, ny) 쪽으로 amount 만큼 부풀고, 양 끝과 꼭대기에서 매끄럽다."""
    px, py = ax + (bx - ax) * pos + nx * amount, ay + (by - ay) * pos + ny * amount
    h1x, h1y = (bx - ax) * pos / 2, (by - ay) * pos / 2
    h2x, h2y = (bx - ax) * (1 - pos) / 2, (by - ay) * (1 - pos) / 2
    return (f'C{ax + h1x:.1f} {ay + h1y:.1f} {px - h1x:.1f} {py - h1y:.1f} {px:.1f} {py:.1f}'
            f'C{px + h2x:.1f} {py + h2y:.1f} {bx - h2x:.1f} {by - h2y:.1f} {bx:.1f} {by:.1f}')


def overlay(w, h, inset, bulge, radius=84):
    """화면 가장자리를 따라 그려지는 오버레이 한 장면(가운데가 뚫린 도형).

    inset = (위, 오른쪽, 아래, 왼쪽) 띠의 두께.
    bulge = 변마다 (가운데로 더 부푸는 양, 부푸는 위치 0~1). 앱의 파도 모드처럼
            소리가 큰 쪽의 띠가 화면 안쪽으로 둥글게 밀려 들어온다.
    """
    top, right, bottom, left = inset
    (bt, pt), (br, pr), (bb, pb), (bl, pl) = bulge
    x0, y0, x1, y1 = left, top, w - right, h - bottom
    r = radius
    return (
        f'M0 0H{w}V{h}H0Z'
        f'M{x0 + r} {y0}'
        + _side(x0 + r, y0, x1 - r, y0, 0, 1, bt, pt)
        + f'Q{x1} {y0} {x1} {y0 + r}'
        + _side(x1, y0 + r, x1, y1 - r, -1, 0, br, pr)
        + f'Q{x1} {y1} {x1 - r} {y1}'
        + _side(x1 - r, y1, x0 + r, y1, 0, -1, bb, 1 - pb)
        + f'Q{x0} {y1} {x0} {y1 - r}'
        + _side(x0, y1 - r, x0, y0 + r, 1, 0, bl, 1 - pl)
        + f'Q{x0} {y0} {x0 + r} {y0}Z'
    )


def fit(face, text, size, limit, what):
    """글이 limit 보다 넓으면 맞는 크기로 줄여 돌려주고, 줄였다고 알린다."""
    width = face.width(text, size, 0)
    if width <= limit:
        return size
    smaller = size * limit / width
    print(f'  [줄임] {what}: {size:g} -> {smaller:.1f} ("{text}")')
    return smaller


# ---------------------------------------------------------------- 첫 화면
def hero(t, f, css):
    H = 700
    c = Canvas(W, H, t['alt'])
    c.css(css)
    c.css(cycle_css('cy', 3, 5.0, 1.0))
    c.add(f'<rect width="{W}" height="{H}" fill="{SCREEN}"/>')
    # 앱이 소리를 그리는 방식 그대로: 사람 소리(왼쪽 위가 두껍게) → 위협음(양쪽) → 환경음(왼쪽)
    scenes = [
        (SPEECH, (46, 26, 28, 40), ((-6, 0.5), (4, 0.35), (20, 0.38), (34, 0.3))),
        (DANGER, (46, 48, 44, 48), ((4, 0.5), (20, 0.5), (10, 0.5), (20, 0.5))),
        (AMBIENT, (30, 16, 24, 30), ((-4, 0.5), (2, 0.5), (16, 0.62), (44, 0.5))),
    ]
    for i, (color, inset, bulge) in enumerate(scenes):
        c.add(f'<path d="{overlay(W, H, inset, bulge)}" fill="{color}" fill-rule="evenodd"{state("cy", i)}/>')

    # 넓은 화면: 가운데 카드
    x, y, w, h, p = 200, 112, 800, 476, 44
    left, right, mid = x + p, x + w - p, x + w / 2
    d = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER}"/>']
    w1, w2, w3 = (f['xb'].width(word, 40, -0.02) for word in t['title'])
    gap = (right - left - w1 - w2 - w3) / 2
    d.append(c.text(f['xb'], t['title'][0], left, y + 78, 40, INK, track=-0.02))
    d.append(c.text(f['xb'], t['title'][1], left + w1 + gap, y + 78, 40, INK, track=-0.02))
    d.append(c.text(f['xb'], t['title'][2], right, y + 78, 40, INK, anchor='end', track=-0.02))
    for i, line in enumerate(t['facts']):
        size = fit(f['b'], line, 40, w - 2 * p, 'hero fact')
        d.append(c.text(f['b'], line, left, y + 162 + i * 44, size, SOFT, track=-0.02))
    for i, line in enumerate(t['line']):
        size = fit(f['b'], line, 40, w - 2 * p, 'hero line')
        d.append(c.text(f['b'], line, left, y + 318 + i * 44, size, INK, track=-0.02))
    base = y + h - p + 2
    d.append(c.text(f['m'], t['credit'], left, base, 20, SOFT))
    d.append(c.text(f['m'], t['mail'], right, base, 20, SOFT, anchor='end'))
    bw = f['sb'].width(t['button'], 22, 0) + 56
    d.append(f'<rect x="{mid - bw / 2:.1f}" y="{base - 36}" width="{bw:.1f}" height="54" fill="{ACCENT}"/>')
    d.append(c.text(f['sb'], t['button'], mid, base - 1, 22, '#FFFFFF', anchor='middle'))
    c.add(f'<g class="dt">{"".join(d)}</g>')

    # 좁은 화면: 카드를 거의 가득 채우고 글자를 키운다
    x, y, w, h, p = 44, 44, 1112, 612, 52
    m = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER}"/>']
    s1 = fit(f['xb'], t['phone_title'][1], 118, w - 2 * p, 'hero phone title')
    m.append(c.text(f['xb'], t['phone_title'][0], x + p, y + 150, s1, INK, track=-0.03))
    m.append(c.text(f['xb'], t['phone_title'][1], x + p, y + 150 + s1 * 1.08, s1, INK, track=-0.03))
    s2 = min(fit(f['b'], line, 60, w - 2 * p, 'hero phone line') for line in t['phone_line'])
    for i, line in enumerate(t['phone_line']):
        m.append(c.text(f['b'], line, x + p, y + 404 + i * s2 * 1.25, s2, INK, track=-0.02))
    s3 = fit(f['m'], t['phone_fact'], 44, w - 2 * p, 'hero phone fact')
    m.append(c.text(f['m'], t['phone_fact'], x + p, y + h - p + 4, s3, SOFT))
    c.add(f'<g class="ph">{"".join(m)}</g>')
    return c


# ---------------------------------------------------------------- 한 틀, 세 가지 소리
def showcase(t, f, css, theme):
    H = 1080
    ink = THEMES[theme]['ink']
    c = Canvas(W, H, t['alt'])
    c.css(css)
    c.css(cycle_css('cy', 3, 5.0, 1.0))
    pics = [c.picture(os.path.join(PICS, name), 1320, 594)
            for name in ('show_speech.jpg', 'show_danger.jpg', 'show_left.jpg')]

    def frame(x, y, width):
        k = width / 1320
        uses = ''.join(f'<use xlink:href="#{pid}"{state("cy", i)}/>' for i, pid in enumerate(pics))
        return f'<g transform="translate({x} {y}) scale({k:.5f})">{uses}</g>'

    # 넓은 화면
    d = []
    size = fit(f['xb'], t['above'], 128, W - 96, 'showcase above')
    size = min(size, fit(f['xb'], t['below'], 128, W - 96, 'showcase below'))
    d.append(c.text(f['xb'], t['above'], W / 2, 220, size, ink, anchor='middle', track=-0.035))
    d.append(frame(160, 280, 880))
    d.append(c.text(f['xb'], t['below'], W / 2, 830, size, ink, anchor='middle', track=-0.035))
    for i, lines in enumerate(t['captions']):
        rows = ''.join(c.text(f['m'], line, W / 2, 912 + j * 40, 26, ink, anchor='middle')
                       for j, line in enumerate(lines))
        d.append(f'<g{state("cy", i)}>{rows}</g>')
    c.add(f'<g class="dt">{"".join(d)}</g>')

    # 좁은 화면: 틀을 넓히고 글자를 키운다
    m = []
    size = fit(f['xb'], t['above'], 140, W - 96, 'showcase phone above')
    size = min(size, fit(f['xb'], t['below'], 140, W - 96, 'showcase phone below'))
    m.append(c.text(f['xb'], t['above'], W / 2, 150, size, ink, anchor='middle', track=-0.035))
    m.append(frame(48, 196, 1104))
    m.append(c.text(f['xb'], t['below'], W / 2, 838, size, ink, anchor='middle', track=-0.035))
    for i, lines in enumerate(t['phone_captions']):
        cap = min(fit(f['m'], line, 50, W - 96, 'showcase phone caption') for line in lines)
        rows = ''.join(c.text(f['m'], line, W / 2, 928 + j * 58, cap, ink, anchor='middle')
                       for j, line in enumerate(lines))
        m.append(f'<g{state("cy", i)}>{rows}</g>')
    c.add(f'<g class="ph">{"".join(m)}</g>')
    return c


# ---------------------------------------------------------------- 작업 패널
def panel(t, f, css, picture, ground, ink):
    """작업 하나. 실제 화면 그림이 있으면 큰 패널, 없으면 색 띠 하나로 그린다.

    그림이 없는 작업을 그림 크기의 빈 색면으로 두지 않으려고 높이를 나눴다.
    어느 쪽이든 같은 한 줄(해 · 이름 · 사실)이 높이 한가운데에 온다.
    """
    H = 540 if picture else 230
    mid = H / 2
    c = Canvas(W, H, t['alt'])
    c.css(css)
    if picture:
        pid = c.picture(os.path.join(PICS, picture), 1680, 756)
        c.add(f'<use xlink:href="#{pid}" transform="scale({W / 1680:.5f})"/>')
    else:
        c.add(f'<rect width="{W}" height="{H}" fill="{ground}"/>')

    # 넓은 화면: 높이 한가운데에 한 줄
    d = []
    if picture:
        d.append(f'<rect y="{mid - 62:g}" width="{W}" height="124" fill="{SCREEN}" opacity="0.66"/>')
    fact_width = f['m'].width(t['fact'], 26, 0)
    title_size = fit(f['xb'], t['title'], 44, W - 48 - fact_width - 56 - 168, 'panel title')
    d.append(c.text(f['m'], t['year'], 48, mid + 13, 26, ink))
    d.append(c.text(f['xb'], t['title'], 168, mid + 16, title_size, ink, track=-0.01))
    d.append(c.text(f['m'], t['fact'], W - 48, mid + 13, 26, ink, anchor='end'))
    c.add(f'<g class="dt">{"".join(d)}</g>')

    # 좁은 화면: 두 줄로 (이름 / 해와 사실). 그림 패널에서는 아래쪽에 둔다.
    m = []
    if picture:
        m.append(f'<rect y="336" width="{W}" height="204" fill="{SCREEN}" opacity="0.72"/>')
    title_y, row_y = (430, 502) if picture else (104, 180)
    title_size = fit(f['xb'], t['title'], 76, W - 96, 'panel phone title')
    fact_size = fit(f['m'], t['fact'], 46, W - 96 - 160, 'panel phone fact')
    m.append(c.text(f['xb'], t['title'], 48, title_y, title_size, ink, track=-0.01))
    m.append(c.text(f['m'], t['year'], 48, row_y, 46, ink))
    m.append(c.text(f['m'], t['fact'], W - 48, row_y, fact_size, ink, anchor='end'))
    c.add(f'<g class="ph">{"".join(m)}</g>')
    return c


# ---------------------------------------------------------------- 수상·자격 띠
def proof(t, f, css):
    H = 260
    c = Canvas(W, H, t['alt'])
    size, gap, dot = 96, 54, 12
    x = 0.0
    parts = []
    for name in t['names']:
        parts.append(c.text(f['xb'], name, x, 163, size, '#FFFFFF', track=-0.03))
        x += f['xb'].width(name, size, -0.03) + gap
        parts.append(f'<circle cx="{x + dot:.1f}" cy="130" r="{dot}" fill="#FFFFFF"/>')
        x += dot * 2 + gap
    track = ''.join(parts)
    # 같은 줄을 두 번 이어 붙여, 왼쪽으로 한 줄만큼 흐른 뒤 처음으로 돌아가도 끊겨 보이지 않게 한다
    c.css(f'@keyframes mq{{to{{transform:translateX(-{x:.1f}px)}}}}'
          f'.mq{{animation:mq {x / 110:.0f}s linear infinite}}'
          '@media (prefers-reduced-motion:reduce){.mq{animation:none}}')
    c.add(f'<rect width="{W}" height="{H}" fill="{ACCENT}"/>')
    c.add(f'<g class="mq"><g transform="translate(-180 0)">{track}</g>'
          f'<g transform="translate({x - 180:.1f} 0)">{track}</g></g>')
    return c


# ---------------------------------------------------------------- 연락처
def contact(t, f, css, theme, mail='nawwhod@gmail.com'):
    H = 560
    field, ink = THEMES[theme]['inverse'], THEMES[theme]['on_inverse']
    c = Canvas(W, H, t['alt'])
    c.css(css)
    c.add(f'<rect width="{W}" height="{H}" fill="{field}"/>')

    # 넓은 화면: 메일 주소 한 줄이 왼쪽 끝에서 오른쪽 끝까지
    d = []
    size = 100 * (W - 96) / f['r'].width(mail, 100, -0.04)
    d.append(c.text(f['m'], t['line'], 48, 92, 30, ink))
    d.append(c.text(f['r'], mail, 48, 430, size, ink, track=-0.04))
    d.append(c.text(f['m'], t['place'], 48, 516, 22, ink))
    d.append(c.text(f['m'], t['links'], W - 48, 516, 22, ink, anchor='end'))
    c.add(f'<g class="dt">{"".join(d)}</g>')

    # 좁은 화면: @ 뒤에서 두 줄로 나눈다
    m = []
    user, host = mail.split('@')
    size = 100 * (W - 96) / max(f['r'].width(user + '@', 100, -0.04), f['r'].width(host, 100, -0.04))
    size = min(size, 176)
    for i, line in enumerate(t['phone_line']):
        s = fit(f['m'], line, 58, W - 96, 'contact phone line')
        m.append(c.text(f['m'], line, 48, 100 + i * 72, s, ink))
    m.append(c.text(f['r'], user + '@', 48, 330, size, ink, track=-0.04))
    m.append(c.text(f['r'], host, 48, 330 + size * 1.02, size, ink, track=-0.04))
    c.add(f'<g class="ph">{"".join(m)}</g>')
    return c


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=os.path.join(ROOT, 'assets'))
    parser.add_argument('--only', default='')
    parser.add_argument('--phone', action='store_true', help='좁은 화면용 배치를 강제로 보이게(미리 보기용)')
    args = parser.parse_args()
    only = set(filter(None, args.only.split(',')))
    css = FORCE_PHONE if args.phone else RESPONSIVE

    fonts = font_dir()
    f = {key: Face(os.path.join(fonts, f'Pretendard-{name}.otf'), key)
         for key, name in (('r', 'Regular'), ('m', 'Medium'), ('sb', 'SemiBold'),
                           ('b', 'Bold'), ('xb', 'ExtraBold'))}
    with open(os.path.join(HERE, 'text.json'), encoding='utf-8') as fh:
        text = json.load(fh)

    for lang, t in text.items():
        out = os.path.join(args.out, lang)
        os.makedirs(out, exist_ok=True)
        jobs = {}
        if not only or 'hero' in only:
            jobs['hero'] = hero(t['hero'], f, css)
        if not only or 'showcase' in only:
            for theme in THEMES:
                jobs[f'showcase-{theme}'] = showcase(t['showcase'], f, css, theme)
        if not only or 'work' in only:
            for key, picture, ground, ink in WORK:
                jobs[f'work-{key}'] = panel(t['work'][key], f, css, picture, ground, ink)
        if not only or 'proof' in only:
            jobs['proof'] = proof(t['proof'], f, css)
        if not only or 'contact' in only:
            for theme in THEMES:
                jobs[f'contact-{theme}'] = contact(t['contact'], f, css, theme)
        for name, canvas in jobs.items():
            path = os.path.join(out, name + '.svg')
            data = canvas.render()
            with open(path, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(data)
            print(f'{lang}/{name}.svg  {len(data) // 1024}KB')


if __name__ == '__main__':
    main()

"""SVG 그림을 만드는 데 쓰는 작은 도구 모음.

- Face: 글꼴에서 글자 도형과 폭, 글자 사이 간격(커닝)을 꺼낸다.
- Canvas: 글자를 도형으로 넣고, 같은 글자는 한 번만 정의해 다시 쓴다.

글자를 도형으로 넣는 까닭: README 의 그림은 <img> 로 불려 와서 바깥 글꼴을 쓸 수 없다.
도형으로 넣으면 글꼴이 없는 기기에서도 똑같이 보인다.
"""
import base64
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


def _fmt(value):
    """소수 둘째 자리까지만 쓰고 끝의 0 은 뗀다."""
    text = f'{value:.2f}'.rstrip('0').rstrip('.')
    return text if text not in ('-0', '') else '0'


class Face:
    """글꼴 파일 하나. 글자 도형, 폭, 커닝을 돌려준다."""

    def __init__(self, path, key):
        self.key = key
        self.font = TTFont(path)
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.upm = self.font['head'].unitsPerEm
        self.metrics = self.font['hmtx'].metrics
        self._pairs = self._load_kerning()
        self._outlines = {}

    def _load_kerning(self):
        """GPOS 의 kern 기능에서 글자 쌍 간격을 읽는다. 읽지 못하면 간격 없이 쓴다."""
        try:
            table = self.font['GPOS'].table
            wanted = set()
            for record in table.FeatureList.FeatureRecord:
                if record.FeatureTag == 'kern':
                    wanted.update(record.Feature.LookupListIndex)
            subtables = []
            for index in sorted(wanted):
                lookup = table.LookupList.Lookup[index]
                for sub in lookup.SubTable:
                    if lookup.LookupType == 9:
                        if sub.ExtensionLookupType != 2:
                            continue
                        sub = sub.ExtSubTable
                    elif lookup.LookupType != 2:
                        continue
                    coverage = {name: i for i, name in enumerate(sub.Coverage.glyphs)}
                    if sub.Format == 1:
                        pairs = {}
                        for name, i in coverage.items():
                            for rec in sub.PairSet[i].PairValueRecord:
                                value = rec.Value1.XAdvance if rec.Value1 is not None else 0
                                pairs[(name, rec.SecondGlyph)] = value or 0
                        subtables.append((1, coverage, pairs, None, None))
                    else:
                        subtables.append((2, coverage, sub.Class1Record,
                                          sub.ClassDef1.classDefs, sub.ClassDef2.classDefs))
            return subtables
        except Exception:
            return []

    def kern(self, left, right):
        for kind, coverage, data, class1, class2 in self._pairs:
            if left not in coverage:
                continue
            if kind == 1:
                if (left, right) in data:
                    return data[(left, right)]
                continue
            record = data[class1.get(left, 0)].Class2Record[class2.get(right, 0)]
            value = record.Value1.XAdvance if record.Value1 is not None else 0
            return value or 0
        return 0

    def shape(self, text, track=0.0):
        """글자마다 (글리프 이름, x 위치)와 전체 폭을 글꼴 단위로 돌려준다. track 은 em 단위 자간."""
        x = 0
        placed = []
        prev = None
        for ch in text:
            name = self.cmap.get(ord(ch))
            if name is None:
                raise KeyError(f'글꼴에 없는 글자: {ch!r} (U+{ord(ch):04X})')
            if prev is not None:
                x += self.kern(prev, name)
            placed.append((name, x))
            x += self.metrics[name][0] + track * self.upm
            prev = name
        if placed:
            x -= track * self.upm
        return placed, x

    def width(self, text, size, track=0.0):
        return self.shape(text, track)[1] * size / self.upm

    def outline(self, name):
        if name not in self._outlines:
            pen = SVGPathPen(self.glyphs, ntos=lambda v: str(int(round(v))))
            self.glyphs[name].draw(pen)
            self._outlines[name] = pen.getCommands()
        return self._outlines[name]


class Canvas:
    """SVG 한 장. 조각(문자열)을 모아 마지막에 한 번에 내보낸다."""

    def __init__(self, width, height, title):
        self.width = width
        self.height = height
        self.title = title
        self._glyph_ids = {}
        self._glyph_defs = []
        self._defs = []
        self._css = []
        self._body = []

    # ----- 글자
    def text(self, face, text, x, y, size, fill, anchor='start', track=0.0, extra=''):
        """글자 한 줄을 도형으로 넣은 조각을 돌려준다. y 는 글자 밑줄(baseline)."""
        placed, total = face.shape(text, track)
        scale = size / face.upm
        if anchor == 'middle':
            x -= total * scale / 2
        elif anchor == 'end':
            x -= total * scale
        uses = []
        for name, gx in placed:
            d = face.outline(name)
            if not d:
                continue
            key = (face.key, name)
            if key not in self._glyph_ids:
                gid = f'g{len(self._glyph_ids)}'
                self._glyph_ids[key] = gid
                self._glyph_defs.append(f'<path id="{gid}" d="{d}"/>')
            pos = f' x="{_fmt(gx)}"' if gx else ''
            uses.append(f'<use xlink:href="#{self._glyph_ids[key]}"{pos}/>')
        return (f'<g transform="translate({_fmt(x)} {_fmt(y)}) scale({scale:.5f} -{scale:.5f})" '
                f'fill="{fill}"{extra}>{"".join(uses)}</g>')

    # ----- 그림
    def picture(self, path, width, height):
        """JPEG/PNG 파일을 그림 안에 넣어 두고, 다시 쓸 수 있는 이름(id)을 돌려준다."""
        with open(path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('ascii')
        kind = 'jpeg' if path.lower().endswith(('.jpg', '.jpeg')) else 'png'
        pid = f'p{len(self._defs)}'
        self._defs.append(f'<image id="{pid}" width="{width}" height="{height}" '
                          f'preserveAspectRatio="none" xlink:href="data:image/{kind};base64,{data}"/>')
        return pid

    def define(self, fragment):
        self._defs.append(fragment)

    def css(self, rule):
        self._css.append(rule)

    def add(self, fragment):
        self._body.append(fragment)

    def render(self):
        style = f'<style>{"".join(self._css)}</style>' if self._css else ''
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" role="img">'
            f'<title>{self.title}</title>{style}'
            f'<defs>{"".join(self._glyph_defs)}{"".join(self._defs)}</defs>'
            f'{"".join(self._body)}</svg>\n'
        )


def font_dir():
    """Pretendard 글꼴이 있는 폴더. PRETENDARD_DIR 가 있으면 그곳을 쓴다."""
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in (os.environ.get('PRETENDARD_DIR'),
                      os.path.join(here, 'fonts'),
                      os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Fonts'),
                      r'C:\Windows\Fonts'):
        if candidate and os.path.exists(os.path.join(candidate, 'Pretendard-ExtraBold.otf')):
            return candidate
    raise SystemExit('Pretendard 글꼴을 찾지 못했습니다. PRETENDARD_DIR 로 폴더를 알려 주세요.')


def smooth_closed(points, tension=1.0):
    """점들을 지나는 닫힌 곡선(Catmull-Rom)을 SVG path 문자열로 돌려준다."""
    n = len(points)
    out = [f'M{_fmt(points[0][0])} {_fmt(points[0][1])}']
    for i in range(n):
        p0, p1 = points[(i - 1) % n], points[i]
        p2, p3 = points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        out.append(f'C{_fmt(c1[0])} {_fmt(c1[1])} {_fmt(c2[0])} {_fmt(c2[1])} {_fmt(p2[0])} {_fmt(p2[1])}')
    return ''.join(out) + 'Z'

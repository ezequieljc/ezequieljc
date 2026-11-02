#!/usr/bin/env python3
"""Gera os SVGs animados do perfil em ../assets/.

    python3 gerar/gerar.py

Precisa de fonttools e brotli para embutir a fonte 0xProto. A animação é só CSS,
porque o GitHub exibe SVG como imagem e não roda JavaScript.
"""
import base64, html, io, json, os, sys
from fontTools import subset
from fontTools.ttLib import TTFont

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, '..', 'assets')
FONTES = os.path.expanduser('~/.local/share/fonts/nerd-fonts/0xProto')

C = dict(fundo='#1d1b1c', escuro='#161415', preto='#100f0f', claro='#2b2627', sel='#3a2a2d',
         txt='#d9d1d1', fraco='#6e6466', medio='#b5abac', forte='#eee8e8', red='#b8414c',
         red2='#d86a73', amarelo='#d2a65e', verde='#8fa870', ciano='#7ea6a3', rosa='#c77d9b',
         laranja='#c97c55')

GLIFOS = ''.join(chr(c) for c in range(32, 127)) + ''.join(chr(c) for c in range(0xA0, 0x100)) + \
    '●✓↑↓←→·…—'


def fonte(arq):
    op = subset.Options(flavor='woff2', layout_features=[], hinting=False, notdef_outline=True)
    f = TTFont(os.path.join(FONTES, arq))
    s = subset.Subsetter(op)
    s.populate(text=GLIFOS)
    s.subset(f)
    f.flavor = 'woff2'
    b = io.BytesIO()
    f.save(b)
    return base64.b64encode(b.getvalue()).decode()


REG, BOLD = fonte('0xProtoNerdFontMono-Regular.ttf'), fonte('0xProtoNerdFontMono-Bold.ttf')
FONT_CSS = (f"@font-face{{font-family:P;src:url(data:font/woff2;base64,{REG}) format('woff2')}}"
            f"@font-face{{font-family:P;font-weight:700;src:url(data:font/woff2;base64,{BOLD}) format('woff2')}}")


class Svg:
    def __init__(self, w, h, titulo):
        self.w, self.h, self.titulo = w, h, titulo
        self.els, self.base, self.anim, self.n = [], [], [], 0

    def add(self, s):
        self.els.append(s)

    def r(self, x, y, w, h, fill, rx=0, extra=''):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"' +
                 (f' rx="{rx}"' if rx else '') + f' {extra}/>')

    def t(self, x, y, s, fill=None, size=14, bold=False, extra=''):
        a = f'font-size="{size}" fill="{fill or C["txt"]}"' + (' font-weight="700"' if bold else '')
        self.add(f'<text x="{x}" y="{y}" {a} {extra}>{html.escape(s)}</text>')

    def g(self, id_):
        self.add(f'<g id="{id_}">')

    def fim(self):
        self.add('</g>')

    def degraus(self, id_, prop, pontos, T, base=None):
        """Valores discretos: pontos = [(segundo, valor), ...]."""
        self.n += 1
        nome = f'a{self.n}'
        pontos = sorted(pontos)
        if pontos[0][0] > 0:
            raise ValueError('o primeiro ponto precisa ser t=0')
        q = ''.join(f'{t / T * 100:.3f}%{{{prop}:{v}}}' for t, v in pontos)
        self.anim.append(f'@keyframes {nome}{{{q}100%{{{prop}:{pontos[-1][1]}}}}}'
                         f'#{id_}{{animation:{nome} {T}s step-end infinite}}')
        if base is not None:
            self.base.append(f'#{id_}{{{prop}:{base}}}')

    def visivel(self, id_, intervalos, T, base=0):
        """Mostra o elemento nos intervalos (ini, fim); base é o estado sem animação."""
        p = [(0, 0)]
        for a, b in intervalos:
            if a == 0:
                p = []
            p.append((a, 1))
            if b < T:
                p.append((b, 0))
        self.degraus(id_, 'opacity', p, T, base)

    def css(self, s):
        self.anim.append(s)

    def salvar(self, nome):
        css = (f"{FONT_CSS}text{{font-family:P,ui-monospace,monospace;white-space:pre}}"
               + ''.join(self.base) +
               '@media (prefers-reduced-motion:no-preference){' + ''.join(self.anim) + '}')
        s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
             f'width="{self.w}" height="{self.h}" role="img"><title>{html.escape(self.titulo)}</title>'
             f'<style>{css}</style>' + ''.join(self.els) + '</svg>')
        with open(os.path.join(SAIDA, nome), 'w', encoding='utf-8') as f:
            f.write(s)
        print(f'{nome}: {len(s) // 1024} KB')


def topo():
    W, H, T = 880, 430, 24
    s = Svg(W, H, 'Desktop i3: Ezequiel escreve o próprio README colando cada linha do histórico de clipboard')
    s.r(0, 0, W, H, C['escuro'], 12)

    # barra
    s.add(f'<path d="M12 0H{W-12}a12 12 0 0 1 12 12V30H0V12A12 12 0 0 1 12 0Z" fill="{C["preto"]}"/>')
    s.add(f'<circle cx="22" cy="15" r="7" fill="none" stroke="{C["red"]}" stroke-width="3"/>')
    x = 42
    for i in range(1, 6):
        if i == 1:
            s.r(x - 5, 7, 18, 16, C['red'], 3)
        s.t(x, 20, str(i), C['forte'] if i == 1 else C['fraco'], 12, i == 1)
        x += 22
    s.t(W / 2 - 18, 20, '14:28', C['medio'], 12)
    s.t(W - 76, 20, 'BR', C['medio'], 12)
    s.t(W - 46, 20, '34%', C['medio'], 12)

    # editor (canivt)
    ex, ey, ew, eh = 10, 38, 548, 382
    s.g('borda-ed')
    s.r(ex, ey, ew, eh, C['fundo'], 0, f'stroke="{C["red"]}" stroke-width="2"')
    s.fim()
    s.t(ex + 14, ey + 21, '~/ezequieljc/README.md', C['medio'], 13)
    s.g('sujo')
    s.t(ex + 14 + 23 * 8.06, ey + 21, '●', C['amarelo'], 13)
    s.fim()
    s.r(ex + 2, ey + 31, ew - 4, 1, C['claro'])
    lx, ly, lh = ex + 46, ey + 58, 26
    for i in range(1, 12):
        s.t(ex + 14, ly + (i - 1) * lh, f'{i:>2}', C['fraco'], 14)
    linhas = {'l1': (1, '# Ezequiel', C['red2'], True),
              'l3': (3, 'Trabalho com IA e produtos digitais na Septium Digital.', C['forte'], False),
              'l5': (5, 'Nas horas vagas, faço o que me falta no Linux.', C['forte'], False)}
    for id_, (n, txt, cor, b) in linhas.items():
        s.g(id_)
        s.t(lx, ly + (n - 1) * lh, txt, cor, 14, b)
        s.fim()
    s.g('cursor')
    s.r(0, -13, 9, 17, C['txt'])
    s.fim()
    s.r(ex + 2, ey + eh - 28, ew - 4, 1, C['claro'])
    s.t(ex + 14, ey + eh - 10, 'Ctrl+S Salvar   Ctrl+V Colar   Ctrl+Q Sair', C['fraco'], 12)
    s.g('salvo')
    s.t(ex + ew - 66, ey + eh - 10, 'salvo', C['verde'], 12, True)
    s.fim()

    # fastfetch
    fx, fy, fw, fh = 566, 38, 304, 382
    s.r(fx, fy, fw, fh, C['fundo'], 0, f'stroke="{C["claro"]}" stroke-width="2"')
    s.t(fx + 16, fy + 32, 'ezequiel', C['red2'], 14, True)
    s.t(fx + 16 + 8 * 8.68, fy + 32, '@t480', C['txt'], 14)
    s.t(fx + 16, fy + 52, '-------------', C['fraco'], 14)
    dados = [('OS', 'Debian 13'), ('WM', 'i3'), ('Host', 'ThinkPad T480'), ('Teclado', 'Corne v4'),
             ('Tema', 'QuielRed'), ('Fonte', '0xProto'), ('Código', 'Python, JS, QML, Bash')]
    y = fy + 80
    for k, v in dados:
        s.t(fx + 16, y, k, C['red2'], 14, True)
        s.t(fx + 90, y, v, C['txt'], 14)
        y += 26
    x = fx + 16
    for c in ('preto', 'red', 'verde', 'amarelo', 'laranja', 'rosa', 'ciano', 'forte'):
        s.r(x, y + 4, 28, 16, C[c])
        x += 28

    # janela do CopyQ
    px, py, pw, rh = 150, 120, 580, 34
    s.g('copyq')
    s.r(px, py, pw, rh * 4 + 16, C['fundo'], 0, f'stroke="{C["red"]}" stroke-width="2"')
    s.g('selecao')
    s.r(px + 8, py + 8, pw - 16, rh, C['red'])
    s.fim()
    itens = ['# Ezequiel', 'Trabalho com IA e produtos digitais na Septium Digital.',
             'Nas horas vagas, faço o que me falta no Linux.', 'sudo apt install -y copyq']
    for i, it in enumerate(itens):
        yy = py + 8 + i * rh + 22
        s.t(px + 18, yy, str(i + 1), C['medio'], 12)
        s.t(px + 40, yy, it, C['forte'], 14)
    s.fim()

    # teclas
    def tecla(id_, txt):
        w = len(txt) * 8.68 + 28
        s.g(id_)
        s.r(W / 2 - w / 2, 346, w, 34, C['preto'], 6, f'stroke="{C["red"]}" stroke-width="1.5"')
        s.t(W / 2 - w / 2 + 14, 368, txt, C['forte'], 14, True)
        s.fim()
    for id_, txt in (('k-sv', 'Super + V'), ('k-dn', '↓'), ('k-en', 'Enter'), ('k-cs', 'Ctrl + S')):
        tecla(id_, txt)

    # ciclos: tecla Super+V, janela aberta, Enter, linha colada
    copy = [(1.9, 3.5), (5.6, 7.4), (9.6, 12.0)]
    s.visivel('k-sv', [(1.5, 2.3), (5.2, 5.9), (9.2, 9.9)], T)
    s.visivel('copyq', copy, T)
    s.visivel('k-dn', [(6.4, 6.8), (10.3, 10.7), (10.9, 11.2)], T)
    s.visivel('k-en', [(3.1, 3.6), (7.0, 7.5), (11.6, 12.1)], T)
    s.degraus('selecao', 'transform', [(0, 'translateY(0)'), (6.5, f'translateY({rh}px)'),
                                       (7.4, 'translateY(0)'), (10.4, f'translateY({rh}px)'),
                                       (11.0, f'translateY({rh * 2}px)'), (12.0, 'translateY(0)')], T,
              'translateY(0)')
    s.visivel('l1', [(3.5, T)], T, 1)
    s.visivel('l3', [(7.4, T)], T, 1)
    s.visivel('l5', [(12.0, T)], T, 1)
    s.visivel('sujo', [(3.5, 13.8)], T)
    s.visivel('k-cs', [(13.4, 14.2)], T)
    s.visivel('salvo', [(13.8, T)], T, 1)
    cx = lambda n: lx + n * 8.68
    cy = lambda ln: ly + (ln - 1) * lh
    s.degraus('cursor', 'transform', [(0, f'translate({cx(0)}px,{cy(1)}px)'),
                                      (3.5, f'translate({cx(10)}px,{cy(1)}px)'),
                                      (4.2, f'translate({cx(0)}px,{cy(3)}px)'),
                                      (7.4, f'translate({cx(55)}px,{cy(3)}px)'),
                                      (8.1, f'translate({cx(0)}px,{cy(5)}px)'),
                                      (12.0, f'translate({cx(46)}px,{cy(5)}px)')], T,
              f'translate({cx(46)}px,{cy(5)}px)')
    s.css('@keyframes pisca{0%,49%{fill-opacity:1}50%,100%{fill-opacity:.15}}'
          '#cursor rect{animation:pisca 1s linear infinite}')
    s.degraus('borda-ed', 'opacity', [(0, 1)] + sum([[(a, .45), (b, 1)] for a, b in copy], []), T, 1)
    s.salvar('topo.svg')


def cartao(titulo, lingua, desc, alt):
    W, H = 430, 270
    s = Svg(W, H, alt)
    s.r(1, 1, W - 2, H - 2, C['fundo'], 10, f'stroke="{C["claro"]}" stroke-width="2"')
    s.t(18, 30, titulo, C['forte'], 16, True)
    s.t(W - 18, 30, lingua, C['fraco'], 12, False, 'text-anchor="end"')
    s.r(2, 44, W - 4, 1, C['claro'])
    s.r(2, 212, W - 4, 1, C['claro'])
    for i, d in enumerate(desc):
        s.t(18, 234 + i * 19, d, C['medio'], 12.5)
    return s


def cryptochar():
    herois = json.load(open(os.path.join(BASE, 'herois.json'), encoding='utf-8'))
    T = len(herois) * 3
    s = cartao('CryptoChar', 'jogar no navegador',
               ['RPG em pixel art: cada herói nasce de uma chave', 'secp256k1, como uma paper wallet do Bitcoin.'],
               'CryptoChar: heróis em pixel art gerados a partir de chaves criptográficas')
    for i, h in enumerate(herois):
        ini = i * 3
        s.g(f'h{i}')
        s.add(f'<image x="16" y="46" width="147" height="168" href="{h["png"]}" '
              'style="image-rendering:pixelated"/>')
        s.t(182, 78, 'genoma', C['fraco'], 12)
        hx = h['hex']
        s.t(182, 100, ' '.join(hx[j:j + 4] for j in range(0, 16, 4)), C['ciano'], 13)
        s.t(182, 120, ' '.join(hx[j:j + 4] for j in range(16, 32, 4)), C['ciano'], 13)
        s.t(182, 158, h['nome'], C['red2'], 14, True)
        s.t(182, 182, 'mesma chave, mesmo herói', C['medio'], 12.5)
        s.fim()
        s.visivel(f'h{i}', [(ini, ini + 3)], T, 1 if i == 0 else 0)
    faiscas = [(90, 170, -46, -70), (90, 170, 40, -84), (90, 170, -66, -28), (90, 170, 62, -38),
               (90, 170, -18, -96), (90, 170, 22, -56)]
    for i, (x, y, dx, dy) in enumerate(faiscas):
        s.r(x, y, 4, 4, C['amarelo'] if i % 2 else C['laranja'], 0, f'id="f{i}" opacity="0"')
        s.css(f'@keyframes fa{i}{{0%{{opacity:1;transform:translate(0,0)}}12%{{opacity:0;'
              f'transform:translate({dx}px,{dy}px)}}100%{{opacity:0;transform:translate({dx}px,{dy}px)}}}}'
              f'#f{i}{{animation:fa{i} 3s ease-out infinite}}')
    s.salvar('cryptochar.svg')


def micruxsip():
    T = 13
    s = cartao('MicruxSip', 'Python + GTK',
               ['Softphone SIP para Linux com a cara e o jeito', 'de usar do MicroSIP do Windows.'],
               'MicruxSip: discador SIP fazendo uma ligação para o ramal 1042')
    ox, oy = 18, 54
    s.r(ox, oy, 162, 150, '#f4f3f2', 4)
    s.r(ox + 6, oy + 6, 150, 24, '#ffffff', 3, 'stroke="#c8c6c4"')
    digitos = '1042'
    tempos = [0.8, 1.4, 2.0, 2.6]
    for i in range(4):
        s.g(f'd{i}')
        s.t(ox + 14 + i * 10, oy + 23, digitos[i], '#2e2e2e', 15)
        s.fim()
        s.visivel(f'd{i}', [(tempos[i], 11.5)], T, 1)
    teclas = '123456789*0#'
    for i, k in enumerate(teclas):
        x = ox + 6 + (i % 3) * 51
        y = oy + 36 + (i // 3) * 28
        s.r(x, y, 48, 25, '#ffffff', 3, 'stroke="#d5d3d1"')
        if k in digitos:
            ti = tempos[digitos.index(k)]
            s.r(x, y, 48, 25, C['red'], 3, f'id="t{k}" opacity="0"')
            s.visivel(f't{k}', [(ti, ti + .3)], T)
        s.t(x + 20, y + 18, k, '#2e2e2e', 14)
    s.t(198, 76, 'conta', C['fraco'], 12)
    s.add(f'<circle cx="203" cy="94" r="4" fill="{C["verde"]}"/>')
    s.t(214, 99, 'Online', C['txt'], 13)
    s.t(198, 128, 'chamada', C['fraco'], 12)

    def estado(id_, txt, cor, ini, fim):
        s.g(id_)
        s.t(198, 150, txt, cor, 14, True)
        s.fim()
        s.visivel(id_, [(ini, fim)], T, 1 if id_ == 'e2' else 0)
    estado('e0', 'discando…', C['medio'], .8, 3.2)
    estado('e1', 'chamando 1042', C['amarelo'], 3.2, 5.0)
    estado('e2', 'em chamada', C['verde'], 5.0, 11.0)
    estado('e3', 'encerrada', C['fraco'], 11.0, 11.8)
    s.g('timer')
    for i in range(6):
        s.g(f'c{i}')
        s.t(198 + 92, 150, f'00:0{i}', C['medio'], 13)
        s.fim()
        s.visivel(f'c{i}', [(5 + i, 6 + i)], T, 1 if i == 5 else 0)
    s.fim()
    s.g('onda')
    for i in range(16):
        h = (6, 16, 10, 24, 14, 30, 12, 20)[i % 8]
        s.r(198 + i * 12, 186 - h / 2, 7, h, C['red'], 1, f'id="b{i}"')
        s.css(f'@keyframes on{i}{{0%,100%{{transform:scaleY(.35)}}50%{{transform:scaleY(1.1)}}}}'
              f'#b{i}{{transform-origin:{198 + i * 12 + 3.5}px 186px;'
              f'animation:on{i} {0.7 + i % 5 * .17:.2f}s ease-in-out infinite}}')
    s.fim()
    s.visivel('onda', [(5, 11)], T, 1)
    s.salvar('micruxsip.svg')


def canivt():
    T = 12
    s = cartao('canivt', 'Python, um arquivo',
               ['Gerenciador de arquivos e editor para o terminal,', 'com favoritos e acesso a servidores Samba.'],
               'canivt: gerenciador de arquivos no terminal abrindo uma pasta num servidor Samba')
    side = 150
    s.r(2, 45, side - 2, 167, C['escuro'])
    s.t(14, 66, ' FAVORITOS', C['fraco'], 12, True)
    favs = [('1', 'ezequiel'), ('2', 'Documentos'), ('3', 'Downloads')]
    for i, (k, n) in enumerate(favs):
        y = 86 + i * 20
        s.r(14, y - 12, 16, 16, C['red'])
        s.t(18, y + 1, k, C['preto'], 12, True)
        s.t(36, y + 1, n, C['txt'], 12.5)
    s.t(14, 160, ' SERVIDORES', C['fraco'], 12, True)
    s.g('srv')
    s.r(2, 168, side - 2, 22, C['sel'])
    s.fim()
    s.r(14, 170, 16, 16, C['red'])
    s.t(18, 183, '4', C['preto'], 12, True)
    s.t(36, 183, 'nas/dados', C['txt'], 12.5)
    s.visivel('srv', [(6, T)], T, 1)

    def lista(id_, cam, itens):
        s.g(id_)
        s.t(side + 12, 66, cam, C['medio'], 12.5)
        for i, (ic, n, cor) in enumerate(itens):
            s.t(side + 18, 92 + i * 22, f'{ic} {n}', cor, 13)
        s.fim()
    d, a = '', ''
    lista('la', '/home/ezequiel/Documentos', [(d, 'notas', C['ciano']), (d, 'projetos', C['ciano']),
                                              (a, 'lista.txt', C['txt']), (a, 'ideias.md', C['txt']),
                                              (a, 'contas.ods', C['txt'])])
    lista('lb', ' nas / dados', [(d, 'backup', C['ciano']), (d, 'fotos', C['ciano']),
                                       (d, 'videos', C['ciano']), (a, 'leia-me.txt', C['txt'])])
    s.visivel('la', [(0, 6)], T)
    s.visivel('lb', [(6, T)], T, 1)
    s.add(f'<g id="sel"><rect x="{side + 8}" y="77" width="{430 - side - 18}" height="22" '
          f'fill="{C["red"]}" fill-opacity=".28"/><rect x="{side + 8}" y="77" width="3" height="22" '
          f'fill="{C["red"]}"/></g>')
    s.degraus('sel', 'transform', [(i * .9, f'translateY({v * 22}px)') for i, v in
                                   enumerate([0, 1, 2, 3, 2, 1])] +
              [(6, 'translateY(0)'), (7.2, 'translateY(22px)'), (8.4, 'translateY(44px)'),
               (9.6, 'translateY(66px)')], T, 'translateY(0)')
    s.salvar('canivt.svg')


def debian():
    T = 13
    s = cartao('my-debian-setup', 'Bash + QML',
               ['Do Debian com XFCE recém-instalado ao meu', 'ambiente, com um único instalador.'],
               'my-debian-setup: instalador transformando um desktop XFCE no tema QuielRed')
    passos = ['Pacotes do sistema', 'Temas e comandos', 'Configurações', 'canivt', 'Ajustes finais']
    s.t(18, 68, '$ ./instalar.sh', C['txt'], 13)
    for i, p in enumerate(passos):
        y = 92 + i * 20
        ini = 1 + i * 1.5
        s.g(f'p{i}')
        s.t(18, y, f'{i + 1}/5', C['fraco'], 12.5)
        s.t(50, y, p, C['medio'], 12.5)
        s.fim()
        s.g(f'k{i}')
        s.t(198, y, '✓', C['verde'], 13, True)
        s.fim()
        s.visivel(f'p{i}', [(ini, T)], T, 1)
        s.visivel(f'k{i}', [(ini + 1.2, T)], T, 1)
    s.g('pronto')
    s.t(18, 200, 'Pronto!', C['verde'], 13, True)
    s.fim()
    s.visivel('pronto', [(8.8, T)], T, 1)
    mx, my, mw, mh = 232, 66, 180, 118
    s.r(mx - 4, my - 4, mw + 8, mh + 8, C['preto'], 4)
    s.r(mx + mw / 2 - 26, my + mh + 4, 52, 10, C['claro'])
    s.g('xfce')
    s.r(mx, my, mw, mh, '#3d6d9e')
    s.r(mx, my + mh - 12, mw, 12, '#dcdad5')
    s.r(mx + 4, my + mh - 10, 22, 8, '#3d6d9e')
    s.r(mx + 12, my + 12, 12, 12, '#dcdad5')
    s.r(mx + 12, my + 34, 12, 12, '#dcdad5')
    s.fim()
    s.g('quiel')
    s.r(mx, my, mw, mh, C['escuro'])
    s.r(mx, my, mw, 9, C['preto'])
    s.r(mx + 4, my + 2, 12, 5, C['red'])
    s.r(mx + 4, my + 13, 104, 101, C['fundo'], 0, f'stroke="{C["red"]}"')
    s.r(mx + 112, my + 13, 68, 48, C['fundo'], 0, f'stroke="{C["claro"]}"')
    s.r(mx + 112, my + 65, 68, 49, C['fundo'], 0, f'stroke="{C["claro"]}"')
    for i, w in enumerate((60, 84, 44, 72, 30)):
        s.r(mx + 12, my + 22 + i * 12, w, 4, C['claro'] if i % 2 else C['red2'])
    s.fim()
    s.visivel('xfce', [(0, 8.8)], T)
    s.visivel('quiel', [(8.8, T)], T, 1)
    s.salvar('debian.svg')


os.makedirs(SAIDA, exist_ok=True)
topo(); cryptochar(); micruxsip(); canivt(); debian()

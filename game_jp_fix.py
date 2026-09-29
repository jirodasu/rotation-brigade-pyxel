import pyxel
from game_jp import Game as JapaneseGame

CHARS = '→、あうかけしすずせそただつでとなにのはへまみめもらりるわをんァアイウカガキクコゴサシジスセタダッテトドブプベボマミムメャョラルレロンヴ・ー一上下与中人体作使停全再出列別利前力助動勝北単合味員回団囲圧在基壊大始害対少巨常度弱強弾当待後御復急戦打援撃操支攻敗敵方旅旋時晶最本果機次止残殻済減溜火灼点烈熱爪獣現用甲砕破示空竜第範粉結翼行表被装補見計象距転軽通遠選量鉄開闘防降隊離露風！（）＋－／：？ＨＰ'
GLYPH = {ch: i for i, ch in enumerate(CHARS)}
CELL = 12
COLS = 16


class Game(JapaneseGame):
    def text_width(self, text, scale=1):
        return sum((10 if ch in GLYPH else 4) * scale for ch in str(text))

    def jtext(self, x, y, text, col=7, scale=1):
        cx = x
        pyxel.pal(7, col)
        for ch in str(text):
            if ch in GLYPH:
                i = GLYPH[ch]
                sx = (i % COLS) * CELL
                sy = (i // COLS) * CELL
                if scale == 1:
                    pyxel.blt(cx, y, 1, sx, sy, 12, 12, 0)
                    cx += 10
                else:
                    for yy in range(12):
                        for xx in range(12):
                            if pyxel.image(1).get(sx + xx, sy + yy) != 0:
                                pyxel.rect(cx + xx * scale, y + yy * scale, scale, scale, col)
                    cx += 10 * scale
            else:
                pyxel.text(cx, y + (2 if scale == 1 else 4), ch, col)
                cx += 4 * scale
        pyxel.pal()

import pyxel
from game_v3 import Unit, BOSSES, FRONT, MIDDLE, BACK, EVENT_FRAMES
from game_v4 import Game as BaseGame

W, H = 300, 430
ATLAS_CHARS = '→あうかけしせそだでとなにのはへまめもらりるわをんァアイカガキクコゴサシジスセタダテトドブベボミムメャョラルレロンヴ・ー一上下与中人体停全再出列別利前力助動勝北単合味員回団囲圧在基壊大始害対少巨常度弱強弾待後御復急戦打援撃支攻敗敵方旅旋時晶最本果機次止残殻減溜火灼点烈熱爪獣現甲砕破空竜範粉結翼行被装補計象距転軽通遠選量鉄開闘防降隊離露風！（）＋－／：？ＨＰ'
GLYPH = {ch: i for i, ch in enumerate(ATLAS_CHARS)}
CELL = 12
COLS = 16

JP_NAMES = {'A': 'アレン', 'B': 'ベル', 'C': 'クロード', 'M': 'ミラ', 'S': 'セラ', 'R': 'レイン', 'G': 'ガルド'}
BOSS_NAMES = ['鉄巨人ゴルム', '翼竜ヴァルガ', '晶殻獣カルサイト']
BOSS_DESC = ['単体攻撃の圧力', '前列への範囲攻撃', '弱点露出に火力を合わせる']
ACTION_JP = {'NORMAL': '通常', 'SMASH': '強打', 'CHARGE': '溜め', 'CRUSH': '粉砕', 'CLAW': '爪撃', 'WING': '翼撃', 'DIVE': '急降下', 'GALE': '烈風', 'FLY HIGH': '上空旋回', 'BREATH': '灼熱ブレス', 'CRYSTAL': '晶弾', 'PRESS': '圧壊', 'PRESS+': '圧壊＋', 'CORE OPEN': 'コア露出'}

class Game(BaseGame):
    def __init__(self):
        pyxel.init(W, H, title='回転旅団', fps=30)
        pyxel.mouse(True)
        pyxel.image(1).load(0, 0, 'assets/jp_atlas.png')
        self.u = {
            'A': Unit('A', 'ALLEN', 60, 20, 16), 'B': Unit('B', 'BELL', 55, 22, 14),
            'C': Unit('C', 'CLAUDE', 75, 14, 20, 'DEF', 10), 'M': Unit('M', 'MIRA', 48, 12, 12, 'ATK', 10),
            'S': Unit('S', 'SERA', 75, 8, 0, 'DEF', 6), 'R': Unit('R', 'RAIN', 50, 14, 10, 'RANGED', 18),
            'G': Unit('G', 'GALD', 55, 17, 16, 'ATK', 6)}
        self.bi=0; self.state='TITLE'; self.sel=0; self.events=[]; self.ei=-1; self.tick=0; self.paused=False
        self.turn=1; self.bhp=1; self.bmax=1; self.form=[[None]*4 for _ in range(3)]
        self.dealt=0; self.taken=0; self.final=None; self.final_state='READY'
        pyxel.run(self.update, self.draw)

    def click(self,x,y,w,h):
        return pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and x<=pyxel.mouse_x<x+w and y<=pyxel.mouse_y<y+h

    def update(self):
        if self.state=='TITLE':
            for i in range(3):
                if self.click(24,122+i*62,252,48): self.bi=i; self.reset(); return
        elif self.state=='READY':
            if self.click(54,376,192,40): self.resolve()
        elif self.state=='PLAY': self.update_play()
        elif self.state=='DECISION':
            if self.click(12,376,132,40): self.sel=0; self.commit()
            elif self.click(156,376,132,40): self.sel=1; self.commit()
        elif self.state in ('WIN','LOSE'):
            if self.click(70,376,160,40): self.reset()

    def update_play(self):
        if self.click(12,376,132,40): self.paused=not self.paused
        elif self.click(156,376,132,40): self.next_event(); return
        if not self.paused:
            self.tick+=1
            if self.tick>=EVENT_FRAMES: self.next_event()

    def name(self,k): return BOSS_NAMES[self.bi] if k=='BOSS' else JP_NAMES[k]
    def action_name(self,raw): return ACTION_JP.get(raw,raw)
    def target_text(self,kind):
        if kind=='front_all': return '前列全員'
        if kind=='low': return '前列・最少ＨＰ'
        if kind=='high': return '前列・最大ＨＰ'
        return 'ダメージなし'

    def role_jp(self,r,u):
        if r==FRONT: return f'攻撃 {u.atk}'
        if r==MIDDLE:
            if u.mid=='ATK': return f'攻撃支援 ＋{u.mv}'+('' if u.ready else ' 使用済')
            if u.mid=='DEF': return f'防御支援 －{u.mv}'+('' if u.ready else ' 使用済')
            if u.mid=='RANGED': return f'遠距離 {u.mv}'
            return '待機'
        if u.key=='S': return '回復 4'
        return f'回復 {u.back}' if u.back else '待機'

    def text_width(self,text,scale=1):
        return sum((10 if ch in GLYPH else 4)*scale for ch in str(text))

    def jtext(self,x,y,text,col=7,scale=1):
        cx=x; pyxel.pal(7,col)
        for ch in str(text):
            if ch in GLYPH:
                i=GLYPH[ch]; sx=(i%COLS)*CELL; sy=(i//COLS)*CELL
                if scale==1:
                    pyxel.blt(cx,y,1,sx,sy,12,12,0); cx+=10
                else:
                    for yy in range(12):
                        for xx in range(12):
                            if pyxel.image(1).pget(sx+xx,sy+yy)!=0: pyxel.rect(cx+xx*scale,y+yy*scale,scale,scale,col)
                    cx+=10*scale
            else:
                pyxel.text(cx,y+(2 if scale==1 else 4),ch,col); cx+=4*scale
        pyxel.pal()

    def center_text(self,y,text,col=7,scale=1): self.jtext((W-self.text_width(text,scale))//2,y,text,col,scale)

    def cell_rect(self,k):
        for r,row in enumerate(self.form):
            for c,x in enumerate(row):
                if x==k: return (54+c*60,139+r*42,56,36)
        return None

    def pos(self,k):
        if k=='BOSS': return (150,31)
        q=self.cell_rect(k); return (q[0]+q[2]//2,q[1]+q[3]//2) if q else None

    def draw(self):
        pyxel.cls(1)
        if self.state=='TITLE': self.draw_title(); return
        self.draw_header(); self.draw_forecast(); self.draw_formation(); self.draw_readout(); self.draw_controls()
        if self.state=='PLAY' and self.events: self.draw_fx(self.current_event())
        if self.state in ('WIN','LOSE'): self.draw_result()

    def draw_title(self):
        self.center_text(20,'回転旅団',10,2); self.center_text(52,'隊列ローテーション戦闘',6); self.center_text(88,'敵を選んで開始',7)
        for i in range(3):
            y=122+i*62; pyxel.rect(24,y,252,48,0); pyxel.rectb(24,y,252,48,10 if i==0 else 5)
            self.jtext(36,y+7,BOSS_NAMES[i],10 if i==0 else 7); self.jtext(36,y+26,BOSS_DESC[i],6)
        self.center_text(328,'タップ／マウス操作のみ',5)

    def draw_header(self):
        pyxel.rect(6,6,288,54,0); pyxel.rectb(6,6,288,54,5)
        self.jtext(12,10,self.name('BOSS'),10); self.jtext(205,10,f'第{self.turn}ターン',7)
        self.bar(12,28,276,8,self.bhp,self.bmax,8,2); self.jtext(12,40,f'残り {self.bhp}／{self.bmax}',7)
        if self.dealt: self.jtext(210,40,f'与ダメ {self.dealt}',10)

    def draw_forecast(self):
        pyxel.rect(6,66,288,64,0); pyxel.rectb(6,66,288,64,5); self.jtext(12,70,'次の敵行動',10)
        t0=self.turn+1 if self.state=='DECISION' else self.turn
        for i in range(3):
            t=t0+i; raw,power,kind=self.action(t); x=12+i*94
            pyxel.rect(x,88,88,35,1); pyxel.rectb(x,88,88,35,10 if i==0 else 5)
            self.jtext(x+4,91,f'{t}：{self.action_name(raw)}',10 if i==0 else 7)
            self.jtext(x+4,106,f'{power}ダメージ' if power else 'ダメージなし',8 if power>=36 else 6 if power else 5)
        self.jtext(12,124,'敵の攻撃は前列だけ',8)

    def draw_formation(self):
        e=self.current_event() if self.state=='PLAY' and self.events else None
        labels=['前列','中列','後列']; subs=['攻撃・被弾','支援','回復']
        for r in range(3):
            y=139+r*42; self.jtext(4,y+4,labels[r],8 if r==FRONT else 7); self.jtext(4,y+19,subs[r],5)
            if r==FRONT: pyxel.line(52,y-3,296,y-3,8)
            for c,k in enumerate(self.form[r]):
                x=54+c*60; dim=e is not None and k not in (e['s'],e['d']); bg=1 if dim else 0; bd=5 if dim else 13 if r==FRONT else 9 if r==MIDDLE else 12
                if e and k==e['s']: bd=10
                elif e and k==e['d']: bd=8 if e['k']=='DAMAGE' else 11
                pyxel.rect(x,y,56,36,bg); pyxel.rectb(x,y,56,36,bd)
                if k is None: self.jtext(x+20,y+11,'・',5); continue
                u=self.u[k]; self.jtext(x+3,y+2,JP_NAMES[k],5 if dim else 7)
                self.jtext(x+3,y+15,f'ＨＰ {max(0,u.hp)}／{u.max_hp}',5 if dim else 8 if u.hp<=u.max_hp*.35 else 11)
                self.jtext(x+3,y+27,self.role_jp(r,u),5 if dim else 6)
                mark,color=self.unit_mark_jp(k)
                if mark: pyxel.rect(x+31,y+1,23,10,0); self.jtext(x+33,y+1,mark,color)

    def unit_mark_jp(self,key):
        mark,color=None,6
        for e in self.visible_events():
            if e['k']=='DAMAGE' and e['d']=='BOSS' and e['s']==key: mark,color=f'与{e["n"]}',10
            elif e['k']=='DAMAGE' and e['s']=='BOSS' and e['d']==key: mark,color=f'被{e["n"]}',8
            elif e['k']=='HEAL' and e['d']==key: mark,color=f'＋{e["n"]}',11
            elif e['k']=='SUPPORT' and e['s']==key: mark,color=f'支{e["n"]}',10
            elif e['k']=='GUARD' and e['s']==key: mark,color=f'防{e["n"]}',6
        return mark,color

    def visible_events(self): return self.events[:self.ei+1] if self.state=='PLAY' else self.events

    def event_label(self,e):
        if e['k']=='DAMAGE': return '敵攻撃' if e['s']=='BOSS' else '味方攻撃'
        if e['k']=='HEAL': return '回復行動'
        if e['k']=='SUPPORT': return '攻撃支援'
        if e['k']=='GUARD': return '防御支援'
        return '待機'

    def event_summary(self,e):
        s,d,n=self.name(e['s']),self.name(e['d']),e['n']
        if e['k']=='DAMAGE': return f'{s}→{d} －{n}'
        if e['k']=='HEAL': return f'{s}→{d} ＋{n}'
        if e['k']=='SUPPORT': return f'{s}→{d} 攻撃＋{n}'
        if e['k']=='GUARD': return f'{s}→{d} 軽減{n}'
        return f'{s}：待機'

    def draw_readout(self):
        pyxel.rect(6,270,288,98,0); pyxel.rectb(6,270,288,98,5)
        if self.state=='READY':
            self.jtext(12,278,'戦闘の見方',10); self.jtext(12,296,'前列は攻撃、中列は支援、後列は回復',7)
            self.jtext(12,314,'敵のダメージは前列にだけ当たる',8); self.jtext(12,334,'行動は一人ずつ表示します',6); return
        if not self.events: return
        if self.state=='PLAY':
            e=self.current_event(); col=8 if e['k']=='DAMAGE' else 11 if e['k']=='HEAL' else 10
            self.jtext(12,277,f'現在 {self.ei+1}／{len(self.events)}  {self.event_label(e)}',col); self.jtext(12,295,self.event_summary(e),7)
            if e.get('before') is not None and e.get('after') is not None: self.jtext(12,314,f'ＨＰ {e["before"]} → {e["after"]}',col)
            if self.ei>0: self.jtext(12,338,'一つ前：'+self.event_summary(self.events[self.ei-1]),5)
        else:
            self.jtext(12,277,f'第{self.turn}ターン結果',10); self.jtext(174,277,f'与 {self.dealt}／被 {self.taken}',10); self.jtext(12,295,'キャラ別与ダメ',6)
            hits=[e for e in self.events if e['k']=='DAMAGE' and e['d']=='BOSS']
            for i,e in enumerate(hits[:4]): self.jtext(12+(i%2)*142,311+(i//2)*18,f'{self.name(e["s"])} {e["n"]}',10)
            incoming=[e for e in self.events if e['k']=='DAMAGE' and e['s']=='BOSS']
            if incoming: self.jtext(12,349,'敵からの被害：'+'／'.join(f'{self.name(e["d"])}－{e["n"]}' for e in incoming[:3]),8)
            else: self.jtext(12,349,'敵からの被害：なし',5)

    def draw_controls(self):
        if self.state=='READY': self.button_jp(54,376,192,40,'戦闘開始',True)
        elif self.state=='DECISION': self.button_jp(12,376,132,40,'ローテーション',True); self.button_jp(156,376,132,40,'そのまま',False)
        elif self.state=='PLAY': self.button_jp(12,376,132,40,'再開' if self.paused else '一時停止',False); self.button_jp(156,376,132,40,'次の行動',True)
        elif self.state in ('WIN','LOSE'): self.button_jp(70,376,160,40,'もう一度',True)

    def button_jp(self,x,y,w,h,label,on):
        pyxel.rect(x,y,w,h,5 if on else 2); pyxel.rectb(x,y,w,h,10 if on else 6); tw=self.text_width(label); self.jtext(x+(w-tw)//2,y+13,label,10 if on else 7)

    def draw_fx(self,e):
        a,b=self.pos(e['s']),self.pos(e['d'])
        if not a or not b: return
        k=e['k']; col=8 if k=='DAMAGE' else 11 if k=='HEAL' else 10; phase=min(1.0,self.tick/max(1,EVENT_FRAMES-1))
        if a!=b:
            pyxel.line(a[0],a[1],b[0],b[1],col); px=int(a[0]+(b[0]-a[0])*phase); py=int(a[1]+(b[1]-a[1])*phase); pyxel.circ(px,py,2,col)
        if 5<=self.tick<=13:
            shake=1 if self.tick%2==0 else -1
            if e['d']=='BOSS': pyxel.rectb(5+shake,5,290,56,col)
            else:
                q=self.cell_rect(e['d'])
                if q: pyxel.rectb(q[0]+shake-2,q[1]-2,q[2]+4,q[3]+4,col)
        if k not in ('DAMAGE','HEAL','SUPPORT','GUARD'): return
        txt=('－' if k in ('DAMAGE','GUARD') else '＋')+str(e['n'])
        if e['d']=='BOSS': self.popup(230,35,txt,col)
        else:
            q=self.cell_rect(e['d'])
            if q: self.popup(q[0]+q[2]//2,q[1]+10,txt,col)

    def popup(self,cx,y,text,color):
        w=self.text_width(text,2); x=max(2,min(W-w-4,cx-w//2)); pyxel.rect(x-4,y-4,w+8,26,0); self.jtext(x,y,text,color,2)

    def draw_result(self):
        win=self.state=='WIN'; col=10 if win else 8; pyxel.rect(52,154,196,78,0); pyxel.rectb(52,154,196,78,col)
        self.center_text(168,'勝利' if win else '敗北',col,2); self.center_text(204,f'第{self.turn}ターン・残り{self.alive()}人',7)

    def bar(self,x,y,w,h,v,m,fg,bg):
        pyxel.rect(x,y,w,h,bg)
        if m: pyxel.rect(x,y,int(w*max(0,v)/m),h,fg)
        pyxel.rectb(x,y,w,h,7)

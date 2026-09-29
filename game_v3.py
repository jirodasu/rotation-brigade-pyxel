import pyxel

W,H=256,360
FRONT,MIDDLE,BACK=0,1,2
ROWS=["FRONT","MID","BACK"]
COLORS={"A":10,"B":9,"C":6,"M":12,"S":11,"R":14,"G":15}
EVENT_FRAMES=22
BIG={
"0":["111","101","101","101","111"],"1":["010","110","010","010","111"],
"2":["111","001","111","100","111"],"3":["111","001","111","001","111"],
"4":["101","101","111","001","001"],"5":["111","100","111","001","111"],
"6":["111","100","111","101","111"],"7":["111","001","010","010","010"],
"8":["111","101","111","101","111"],"9":["111","101","111","001","111"],
"+":["000","010","111","010","000"],"-":["000","000","111","000","000"]}

class Unit:
    def __init__(self,key,name,hp,atk,back=0,mid=None,mv=0):
        self.key,self.name,self.max_hp,self.hp=key,name,hp,hp
        self.atk,self.back,self.mid,self.mv=atk,back,mid,mv; self.ready=True
    @property
    def alive(self): return self.hp>0
    def reset(self): self.hp=self.max_hp; self.ready=True

BOSSES=[
 {"name":"GOLM","hp":700,"desc":"SINGLE-TARGET PRESSURE","p":[("NORMAL",16,"low"),("NORMAL",16,"low"),("SMASH",36,"low"),("NORMAL",16,"low"),("CHARGE",0,"none"),("CRUSH",46,"low")]},
 {"name":"VALGA","hp":660,"desc":"FRONT-ROW AREA ATTACKS","p":[("CLAW",12,"low"),("WING",12,"front_all"),("DIVE",22,"high"),("GALE",18,"front_all"),("FLY HIGH",0,"none"),("BREATH",46,"front_all")]},
 {"name":"CALCITE","hp":400,"desc":"TIME DAMAGE WITH CORE OPEN","p":[("CRYSTAL",16,"low"),("PRESS",22,"low"),("CORE OPEN",0,"none"),("CRYSTAL",16,"low"),("PRESS+",28,"low"),("CORE OPEN",0,"none")],"deadline":15},]

class Game:
    def __init__(self):
        pyxel.init(W,H,title="ROTATION BRIGADE",fps=30); pyxel.mouse(True)
        self.u={"A":Unit("A","ALLEN",60,20,16),"B":Unit("B","BELL",55,22,14),
          "C":Unit("C","CLAUDE",75,14,20,"DEF",10),"M":Unit("M","MIRA",48,12,12,"ATK",10),
          "S":Unit("S","SERA",75,8,0,"DEF",6),"R":Unit("R","RAIN",50,14,10,"RANGED",18),
          "G":Unit("G","GALD",55,17,16,"ATK",6)}
        self.bi=0; self.state="TITLE"; self.sel=0; self.events=[]; self.ei=-1; self.tick=0; self.paused=False
        self.turn=1; self.bhp=1; self.bmax=1; self.form=[[None]*4 for _ in range(3)]
        self.dealt=0; self.taken=0; self.final=None; self.final_state="READY"
        pyxel.run(self.update,self.draw)

    def click(self,x,y,w,h): return pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and x<=pyxel.mouse_x<x+w and y<=pyxel.mouse_y<y+h
    def boss(self): return BOSSES[self.bi]
    def action(self,t): return self.boss()["p"][(t-1)%len(self.boss()["p"])]
    def name(self,k): return self.boss()["name"] if k=="BOSS" else self.u[k].name
    def alive(self): return sum(x.alive for x in self.u.values())
    def front_n(self): return sum(k is not None and self.u[k].alive for k in self.form[FRONT])
    def confirm(self): return pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN)

    def reset(self):
        for x in self.u.values(): x.reset()
        self.form=[["A","B","C",None],["M","G",None,"R"],[None,"S",None,None]]
        self.bhp=self.bmax=self.boss()["hp"]; self.turn=1; self.sel=0; self.events=[]; self.ei=-1
        self.tick=0; self.paused=False; self.dealt=0; self.taken=0; self.state="READY"

    def update(self):
        if self.state=="TITLE":
            if pyxel.btnp(pyxel.KEY_UP): self.bi=(self.bi-1)%3
            if pyxel.btnp(pyxel.KEY_DOWN): self.bi=(self.bi+1)%3
            for i in range(3):
                if self.click(30,104+i*42,196,32): self.bi=i; self.reset(); return
            if self.confirm(): self.reset()
        elif self.state=="READY":
            if self.confirm() or self.click(88,330,80,22): self.resolve()
        elif self.state=="PLAY": self.update_play()
        elif self.state=="DECISION":
            if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A): self.sel=0
            if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D): self.sel=1
            if self.click(12,330,108,22): self.sel=0; self.commit()
            elif self.click(136,330,108,22): self.sel=1; self.commit()
            elif self.confirm(): self.commit()
        elif self.state in ("WIN","LOSE"):
            if pyxel.btnp(pyxel.KEY_R) or self.confirm() or self.click(73,330,110,22): self.reset()
            if pyxel.btnp(pyxel.KEY_X): self.state="TITLE"
        if pyxel.btnp(pyxel.KEY_Q): pyxel.quit()

    def update_play(self):
        if pyxel.btnp(pyxel.KEY_SPACE) or self.click(12,304,108,20): self.paused=not self.paused
        if self.confirm() or self.click(136,304,108,20): self.next_event(); return
        if not self.paused:
            self.tick+=1
            if self.tick>=EVENT_FRAMES: self.next_event()

    def commit(self):
        if self.sel==0: self.rotate()
        self.turn+=1; self.resolve()

    def rotate(self):
        old=[r[:] for r in self.form]; self.form=[old[MIDDLE],old[BACK],old[FRONT]]
        for c,k in enumerate(self.form[MIDDLE]):
            if k is not None and old[MIDDLE][c]!=k: self.u[k].ready=True

    def snap(self): return (self.bhp,{k:(x.hp,x.ready) for k,x in self.u.items()},[r[:] for r in self.form],self.dealt,self.taken)
    def restore(self,s):
        self.bhp,us,f,self.dealt,self.taken=s
        for k,(hp,ready) in us.items(): self.u[k].hp=hp; self.u[k].ready=ready
        self.form=[r[:] for r in f]
    def record(self,src,dst,kind,n,detail="",col=None): self.events.append({"s":src,"d":dst,"k":kind,"n":n,"detail":detail,"col":col,"snap":self.snap()})

    def resolve(self):
        self.events=[]; self.dealt=0; self.taken=0; initial=self.snap(); self.calc(); self.final=self.snap(); self.final_state=self.state
        if self.events: self.restore(initial); self.state="PLAY"; self.ei=-1; self.paused=False; self.next_event()
    def next_event(self):
        self.ei+=1
        if self.ei>=len(self.events): self.ei=max(0,len(self.events)-1); self.restore(self.final); self.state=self.final_state; return
        self.restore(self.events[self.ei]["snap"]); self.tick=0

    def calc(self):
        self.ally_phase()
        if self.bhp<=0: self.bhp=0; self.state="WIN"; return
        if self.front_n()==0: self.state="LOSE"; return
        self.enemy_phase(); self.cleanup()
        if self.alive()==0 or self.front_n()==0: self.state="LOSE"; return
        self.back_phase(); self.cleanup()
        if self.boss().get("deadline") and self.turn>=self.boss()["deadline"] and self.bhp>0: self.state="LOSE"; return
        self.state="DECISION"; self.sel=0

    def ally_phase(self):
        mult=.2 if self.bi==2 and self.turn%3!=0 else 1
        for c in range(4):
            fk,mk=self.form[FRONT][c],self.form[MIDDLE][c]
            if fk is not None and self.u[fk].alive:
                a=self.u[fk]; dmg=a.atk; bonus=0
                if mk is not None:
                    m=self.u[mk]
                    if m.alive and m.mid=="ATK" and m.ready:
                        m.ready=False; bonus=m.mv; dmg+=bonus; self.record(mk,fk,"SUPPORT",bonus,"ATTACK BONUS",c)
                hit=max(1,int(round(dmg*mult))); self.bhp=max(0,self.bhp-hit); self.dealt+=hit
                detail=f"BASE {a.atk}"+(f" +SUP {bonus}" if bonus else "")+(" / ARMOR x0.2" if mult<1 else "")
                self.record(fk,"BOSS","DAMAGE",hit,detail,c)
            elif mk is not None and self.u[mk].alive and self.u[mk].mid=="RANGED":
                m=self.u[mk]; hit=max(1,int(round(m.mv*mult))); self.bhp=max(0,self.bhp-hit); self.dealt+=hit
                self.record(mk,"BOSS","DAMAGE",hit,"RANGED / ARMOR x0.2" if mult<1 else "RANGED",c)

    def enemy_phase(self):
        act,pwr,kind=self.action(self.turn)
        if pwr<=0 or kind=="none": self.record("BOSS","BOSS","WAIT",0,act); return
        fs=[(c,self.u[k]) for c,k in enumerate(self.form[FRONT]) if k is not None and self.u[k].alive]
        if not fs: return
        if kind=="front_all":
            for c,x in fs: self.enemy_hit(c,x,pwr,act)
        elif kind=="high":
            c,x=max(fs,key=lambda z:(z[1].hp,-z[0])); self.enemy_hit(c,x,pwr,act)
        else:
            c,x=min(fs,key=lambda z:(z[1].hp,z[0])); self.enemy_hit(c,x,pwr,act)

    def enemy_hit(self,c,target,pwr,act):
        red=0; mk=self.form[MIDDLE][c]
        if mk is not None:
            m=self.u[mk]
            if m.alive and m.mid=="DEF" and m.ready: red=m.mv; m.ready=False; self.record(mk,target.key,"GUARD",red,"DAMAGE REDUCTION",c)
        dmg=max(1,pwr-red); target.hp=max(0,target.hp-dmg); self.taken+=dmg
        detail=act+(f" / {pwr}-{red}" if red else "")+(" / DOWN" if not target.alive else "")
        self.record("BOSS",target.key,"DAMAGE",dmg,detail,c)

    def back_phase(self):
        for c,k in enumerate(self.form[BACK]):
            if k is None or not self.u[k].alive: continue
            b=self.u[k]
            if k=="S":
                for r in (FRONT,MIDDLE):
                    t=self.form[r][c]
                    if t is not None and self.u[t].alive:
                        x=self.u[t]; old=x.hp; x.hp=min(x.max_hp,x.hp+4); n=x.hp-old
                        if n: self.record("S",t,"HEAL",n,"LINE RECOVERY",c)
            elif b.back:
                old=b.hp; b.hp=min(b.max_hp,b.hp+b.back); n=b.hp-old
                if n: self.record(k,k,"HEAL",n,"SELF RECOVERY",c)

    def cleanup(self):
        for r in range(3):
            for c,k in enumerate(self.form[r]):
                if k is not None and not self.u[k].alive: self.form[r][c]=None

    def role(self,r,x):
        if r==FRONT: return f"ATK {x.atk}"
        if r==MIDDLE:
            if x.mid=="ATK": return f"SUP +{x.mv}"+("" if x.ready else " USED")
            if x.mid=="DEF": return f"DEF -{x.mv}"+("" if x.ready else " USED")
            if x.mid=="RANGED": return f"RNG {x.mv}"
            return "NO ACT"
        if x.key=="S": return "HEAL 4"
        return f"REC {x.back}" if x.back else "NO ACT"

    def shown_turn(self): return self.turn+1 if self.state=="DECISION" else self.turn
    def target_text(self,k): return "FRONT ALL" if k=="front_all" else "FRONT LOW" if k=="low" else "FRONT HIGH" if k=="high" else "NO DAMAGE"
    def current_event(self): return self.events[max(0,min(self.ei,len(self.events)-1))] if self.events else None

    def draw(self):
        pyxel.cls(1)
        if self.state=="TITLE": self.draw_title(); return
        self.draw_header(); self.draw_forecast(); self.draw_formation(); self.draw_readout(); self.draw_controls()
        if self.state=="PLAY" and self.events: self.draw_fx(self.current_event())
        if self.state in ("WIN","LOSE"): self.result()

    def draw_title(self):
        pyxel.text(70,24,"ROTATION BRIGADE",10); pyxel.text(51,40,"ROTATE / STAY TACTICAL BATTLE",6); pyxel.text(74,70,"CHOOSE A BOSS",7)
        for i,b in enumerate(BOSSES):
            y=104+i*42; on=i==self.bi; pyxel.rect(30,y,196,32,5 if on else 0); pyxel.rectb(30,y,196,32,10 if on else 6)
            pyxel.text(40,y+6,f"{i+1}. {b['name']}",10 if on else 7); pyxel.text(40,y+18,b["desc"],6)
        pyxel.text(42,250,"ENEMY DAMAGE HITS FRONT ROW ONLY",8); pyxel.text(52,276,"UP/DOWN + Z / TAP A BOSS",5)

    def draw_header(self):
        b=self.boss(); pyxel.rect(4,4,248,50,0); pyxel.rectb(4,4,248,50,5)
        pyxel.text(9,8,f"{b['name']}   TURN {self.turn}",10); pyxel.text(189,8,f"ALIVE {self.alive()}/7",7)
        self.bar(9,18,238,7,self.bhp,self.bmax,8,2); pyxel.text(9,28,f"BOSS HP {self.bhp}/{self.bmax}",7)
        if self.dealt: pyxel.text(176,28,f"OUT -{self.dealt}",10)
        t=self.shown_turn(); n,p,k=self.action(t); pyxel.text(9,41,f"NEXT: {n} {p}DMG",8 if p>=36 else 7); pyxel.text(145,41,self.target_text(k),10 if p else 6)

    def draw_forecast(self):
        t0=self.shown_turn()
        for i in range(3):
            t=t0+i; n,p,k=self.action(t); x=4+i*84; pyxel.rect(x,58,80,30,0); pyxel.rectb(x,58,80,30,10 if i==0 else 5)
            pyxel.text(x+4,62,f"T{t} {n[:9]}",10 if i==0 else 7); pyxel.text(x+4,72,f"{p} DMG",8 if p>=36 else 6)
            mark="F.ALL" if k=="front_all" else "F.1" if p else "---"; pyxel.text(x+48,72,mark,10 if p else 5)

    def cell_rect(self,k):
        for r,row in enumerate(self.form):
            for c,x in enumerate(row):
                if x==k: return (36+c*54,96+r*34,53,29)
        return None
    def pos(self,k):
        if k=="BOSS": return (128,24)
        q=self.cell_rect(k); return (q[0]+q[2]//2,q[1]+q[3]//2) if q else None

    def draw_formation(self):
        e=self.current_event() if self.state=="PLAY" else None; src=e["s"] if e else None; dst=e["d"] if e else None
        pyxel.text(4,92,"ENEMY ATTACKS FRONT ONLY",8)
        for r in range(3):
            y=96+r*34; pyxel.text(2,y+10,ROWS[r],8 if r==FRONT else 6)
            if r==FRONT: pyxel.line(34,y-2,252,y-2,8)
            for c,k in enumerate(self.form[r]):
                x=36+c*54; dim=e is not None and k not in (src,dst); bg=1 if dim else 0; bd=5 if dim else 13 if r==FRONT else 9 if r==MIDDLE else 12
                if k==src: bd=10
                elif k==dst: bd=8 if e and e["k"]=="DAMAGE" else 11
                pyxel.rect(x,y,53,29,bg); pyxel.rectb(x,y,53,29,bd)
                if k is None: pyxel.text(x+21,y+11,"--",5); continue
                u=self.u[k]; pyxel.rect(x+3,y+3,7,7,COLORS[k]); pyxel.text(x+5,y+4,k,0); pyxel.text(x+13,y+3,u.name[:6],5 if dim else 7)
                pyxel.text(x+3,y+12,f"HP {max(0,u.hp):02}/{u.max_hp:02}",5 if dim else 8 if u.hp<=u.max_hp*.35 else 11); pyxel.text(x+3,y+21,self.role(r,u)[:12],5 if dim else 6)
                if k==src: pyxel.tri(x+44,y+3,x+50,y+6,x+44,y+9,10)
                if k==dst: pyxel.rectb(x+43,y+3,7,7,8)

    def short(self,e):
        s,d,k,n=self.name(e["s"]),self.name(e["d"]),e["k"],e["n"]
        if k=="DAMAGE": return f"{s}>{d} -{n}HP"
        if k=="HEAL": return f"{s}>{d} +{n}HP"
        if k=="SUPPORT": return f"{s}>{d} ATK+{n}"
        if k=="GUARD": return f"{s}>{d} GUARD-{n}"
        return f"{s}: {e['detail']}"

    def draw_readout(self):
        pyxel.rect(4,202,248,94,0); pyxel.rectb(4,202,248,94,5)
        if self.state=="READY":
            pyxel.text(10,210,"BATTLE FLOW",10); pyxel.text(10,224,"FRONT attacks / MID supports / BACK recovers",7)
            pyxel.text(10,238,"Enemy damage can hit FRONT only.",8); pyxel.text(10,254,"Actions play one-by-one with damage popups.",6); return
        if not self.events: return
        if self.state=="PLAY":
            e=self.current_event(); s,d,k,n=self.name(e["s"]),self.name(e["d"]),e["k"],e["n"]
            col=8 if k=="DAMAGE" else 11 if k=="HEAL" else 10; pyxel.text(10,208,f"ACTION {self.ei+1}/{len(self.events)}",10)
            pyxel.text(10,221,f"{s}  >  {d}",7)
            result=f"{n} DAMAGE" if k=="DAMAGE" else f"+{n} HP" if k=="HEAL" else f"ATK +{n}" if k=="SUPPORT" else f"GUARD -{n}" if k=="GUARD" else "NO DAMAGE"
            pyxel.text(10,236,result,col); pyxel.text(10,249,e["detail"][:38],6)
            y=265
            for old in self.events[max(0,self.ei-2):self.ei]: pyxel.text(10,y,self.short(old)[:40],5); y+=9
        else:
            pyxel.text(10,208,f"TURN {self.turn} RESULT",10); pyxel.text(151,208,f"OUT {self.dealt} / IN {self.taken}",10)
            lines=[self.short(e) for e in self.events if e["k"] in ("DAMAGE","HEAL")][-6:]
            for i,line in enumerate(lines): pyxel.text(10,222+i*10,line[:43],7 if i>=len(lines)-2 else 6)

    def draw_controls(self):
        if self.state=="READY": self.button(88,330,80,22,"START",True)
        elif self.state=="DECISION": pyxel.text(14,307,"NEXT TURN: choose formation movement",6); self.button(12,330,108,22,"ROTATE",self.sel==0); self.button(136,330,108,22,"STAY",self.sel==1)
        elif self.state=="PLAY": self.button(12,304,108,20,"RESUME" if self.paused else "PAUSE",False); self.button(136,304,108,20,"NEXT ACTION",True)
        elif self.state in ("WIN","LOSE"): self.button(73,330,110,22,"RETRY",True)

    def draw_fx(self,e):
        a,b=self.pos(e["s"]),self.pos(e["d"]); k=e["k"]
        if not a or not b: return
        col=8 if k=="DAMAGE" else 11 if k=="HEAL" else 10; phase=min(1,self.tick/max(1,EVENT_FRAMES-1))
        if a!=b:
            pyxel.line(a[0],a[1],b[0],b[1],col); px=int(a[0]+(b[0]-a[0])*phase); py=int(a[1]+(b[1]-a[1])*phase); pyxel.circ(px,py,2,col)
        if 5<=self.tick<=13:
            shake=1 if self.tick%2==0 else -1
            if e["d"]=="BOSS": pyxel.rectb(5+shake,5,246,49,col); pyxel.rectb(6+shake,6,244,47,col)
            else:
                q=self.cell_rect(e["d"])
                if q: pyxel.rectb(q[0]+shake-2,q[1]-2,q[2]+4,q[3]+4,col)
        if k in ("DAMAGE","HEAL","SUPPORT","GUARD"):
            prefix="-" if k in ("DAMAGE","GUARD") else "+"; txt=prefix+str(e["n"]); w=self.big_w(txt,2); x=max(2,min(W-w-2,b[0]-w//2)); y=max(92,b[1]-22-int(phase*5))
            self.big_text(x+1,y+1,txt,0,2); self.big_text(x,y,txt,col,2)

    def result(self):
        win=self.state=="WIN"; col=10 if win else 8; pyxel.rect(50,120,156,64,0); pyxel.rectb(50,120,156,64,col)
        pyxel.text(101,132,"VICTORY" if win else "DEFEAT",col); pyxel.text(75,150,f"TURN {self.turn} / ALIVE {self.alive()}",7); pyxel.text(75,166,"Z / TAP RETRY",6)
    def button(self,x,y,w,h,label,on):
        pyxel.rect(x,y,w,h,5 if on else 2); pyxel.rectb(x,y,w,h,10 if on else 6); pyxel.text(x+(w-len(label)*4)//2,y+7,label,10 if on else 7)
    def bar(self,x,y,w,h,v,m,fg,bg):
        pyxel.rect(x,y,w,h,bg); pyxel.rect(x,y,int(w*max(0,v)/m),h,fg) if m else None; pyxel.rectb(x,y,w,h,7)
    def big_w(self,t,s): return max(0,len(t)*4*s-s)
    def big_text(self,x,y,t,col,s=2):
        for i,ch in enumerate(t):
            pat=BIG.get(ch)
            if not pat: continue
            ox=x+i*4*s
            for rr,bits in enumerate(pat):
                for cc,bit in enumerate(bits):
                    if bit=="1": pyxel.rect(ox+cc*s,y+rr*s,s,s,col)

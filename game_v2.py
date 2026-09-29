import pyxel

W,H=256,320
FRONT,MIDDLE,BACK=0,1,2
ROWS=["FRONT","MID","BACK"]
COLORS={"A":10,"B":9,"C":6,"M":12,"S":11,"R":14,"G":15}

class Unit:
    def __init__(self,key,name,hp,atk,back=0,mid=None,mv=0):
        self.key,self.name,self.max_hp,self.hp=key,name,hp,hp
        self.atk,self.back,self.mid,self.mv=atk,back,mid,mv
        self.ready=True
    @property
    def alive(self): return self.hp>0
    def reset(self): self.hp=self.max_hp; self.ready=True

BOSSES=[
 {"name":"GOLM","hp":700,"desc":"SINGLE-TARGET PRESSURE","p":[("NORMAL",16,"low"),("NORMAL",16,"low"),("SMASH",36,"low"),("NORMAL",16,"low"),("CHARGE",0,"none"),("CRUSH",46,"low")]},
 {"name":"VALGA","hp":660,"desc":"FRONT-ROW AREA ATTACKS","p":[("CLAW",12,"low"),("WING",12,"front_all"),("DIVE",22,"high"),("GALE",18,"front_all"),("FLY HIGH",0,"none"),("BREATH",46,"front_all")]},
 {"name":"CALCITE","hp":400,"desc":"TIME DAMAGE WITH CORE OPEN","p":[("CRYSTAL",16,"low"),("PRESS",22,"low"),("CORE OPEN",0,"none"),("CRYSTAL",16,"low"),("PRESS+",28,"low"),("CORE OPEN",0,"none")],"deadline":15},
]

class Game:
    def __init__(self):
        pyxel.init(W,H,title="ROTATION BRIGADE")
        pyxel.mouse(True)
        self.u={
          "A":Unit("A","ALLEN",60,20,16),"B":Unit("B","BELL",55,22,14),
          "C":Unit("C","CLAUDE",75,14,20,"DEF",10),"M":Unit("M","MIRA",48,12,12,"ATK",10),
          "S":Unit("S","SERA",75,8,0,"DEF",6),"R":Unit("R","RAIN",50,14,10,"RANGED",18),
          "G":Unit("G","GALD",55,17,16,"ATK",6)}
        self.bi=0; self.state="TITLE"; self.sel=0; self.events=[]; self.ei=-1; self.tick=0; self.paused=False
        self.turn=1; self.bhp=1; self.bmax=1; self.form=[[None]*4 for _ in range(3)]
        self.dealt=0; self.taken=0
        pyxel.run(self.update,self.draw)

    def click(self,x,y,w,h): return pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and x<=pyxel.mouse_x<x+w and y<=pyxel.mouse_y<y+h
    def boss(self): return BOSSES[self.bi]
    def action(self,t): return self.boss()["p"][(t-1)%len(self.boss()["p"])]
    def name(self,k): return self.boss()["name"] if k=="BOSS" else self.u[k].name
    def alive(self): return sum(x.alive for x in self.u.values())
    def front_n(self): return sum(k is not None and self.u[k].alive for k in self.form[FRONT])

    def reset(self):
        for x in self.u.values(): x.reset()
        self.form=[["A","B","C",None],["M","G",None,"R"],[None,"S",None,None]]
        self.bhp=self.bmax=self.boss()["hp"]
        self.turn=1; self.sel=0; self.events=[]; self.ei=-1; self.tick=0; self.paused=False; self.dealt=0; self.taken=0; self.state="READY"

    def update(self):
        if self.state=="TITLE":
            if pyxel.btnp(pyxel.KEY_UP): self.bi=(self.bi-1)%3
            if pyxel.btnp(pyxel.KEY_DOWN): self.bi=(self.bi+1)%3
            for i in range(3):
                if self.click(30,91+i*38,196,30): self.bi=i; self.reset(); return
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN): self.reset()
        elif self.state=="READY":
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN) or self.click(88,290,80,22): self.resolve()
        elif self.state=="PLAY": self.update_play()
        elif self.state=="DECISION":
            if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A): self.sel=0
            if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D): self.sel=1
            if self.click(16,290,102,22): self.sel=0; self.commit()
            elif self.click(138,290,102,22): self.sel=1; self.commit()
            elif pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN): self.commit()
        elif self.state in ("WIN","LOSE"):
            if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_Z) or self.click(73,290,110,22): self.reset()
            if pyxel.btnp(pyxel.KEY_X): self.state="TITLE"
        if pyxel.btnp(pyxel.KEY_Q): pyxel.quit()

    def update_play(self):
        if pyxel.btnp(pyxel.KEY_SPACE) or self.click(8,290,72,22): self.paused=not self.paused
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN) or self.click(176,290,72,22): self.next_event(); return
        if not self.paused:
            self.tick+=1
            if self.tick>=34: self.next_event()

    def commit(self):
        if self.sel==0: self.rotate()
        self.turn+=1; self.resolve()

    def rotate(self):
        old=[r[:] for r in self.form]
        self.form=[old[MIDDLE],old[BACK],old[FRONT]]
        for c,k in enumerate(self.form[MIDDLE]):
            if k is not None and old[MIDDLE][c]!=k: self.u[k].ready=True

    def snap(self):
        return (self.bhp,{k:(x.hp,x.ready) for k,x in self.u.items()},[r[:] for r in self.form],self.dealt,self.taken)
    def restore(self,s):
        self.bhp,us,f,self.dealt,self.taken=s
        for k,(hp,ready) in us.items(): self.u[k].hp=hp; self.u[k].ready=ready
        self.form=[r[:] for r in f]
    def record(self,src,dst,kind,n,detail="",col=None): self.events.append({"s":src,"d":dst,"k":kind,"n":n,"detail":detail,"col":col,"snap":self.snap()})

    def resolve(self):
        self.events=[]; self.dealt=0; self.taken=0
        initial=self.snap(); self.calc(); self.final=self.snap(); self.final_state=self.state
        if self.events:
            self.restore(initial); self.state="PLAY"; self.ei=-1; self.paused=False; self.next_event()

    def next_event(self):
        self.ei+=1
        if self.ei>=len(self.events):
            self.ei=max(0,len(self.events)-1); self.restore(self.final); self.state=self.final_state; return
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
                a=self.u[fk]; dmg=a.atk
                if mk is not None:
                    m=self.u[mk]
                    if m.alive and m.mid=="ATK" and m.ready:
                        m.ready=False; dmg+=m.mv; self.record(mk,fk,"SUPPORT",m.mv,"ATTACK BONUS",c)
                hit=max(1,int(round(dmg*mult))); self.bhp=max(0,self.bhp-hit); self.dealt+=hit
                self.record(fk,"BOSS","DAMAGE",hit,"ARMOR x0.2" if mult<1 else "FRONT ATTACK",c)
            elif mk is not None and self.u[mk].alive and self.u[mk].mid=="RANGED":
                m=self.u[mk]; hit=max(1,int(round(m.mv*mult))); self.bhp=max(0,self.bhp-hit); self.dealt+=hit
                self.record(mk,"BOSS","DAMAGE",hit,"RANGED / ARMOR x0.2" if mult<1 else "RANGED ATTACK",c)

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
            if m.alive and m.mid=="DEF" and m.ready:
                red=m.mv; m.ready=False; self.record(mk,target.key,"GUARD",red,"DAMAGE REDUCTION",c)
        dmg=max(1,pwr-red); target.hp=max(0,target.hp-dmg); self.taken+=dmg
        self.record("BOSS",target.key,"DAMAGE",dmg,act+(" / DOWN" if not target.alive else ""),c)

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

    def pos(self,k):
        if k=="BOSS": return (128,20)
        for r,row in enumerate(self.form):
            for c,x in enumerate(row):
                if x==k: return (54+c*56,96+r*32)
        return None

    def role(self,r,x):
        if r==FRONT: return f"ATK {x.atk}"
        if r==MIDDLE:
            if x.mid=="ATK": return f"SUP +{x.mv}"+("" if x.ready else " USED")
            if x.mid=="DEF": return f"GUARD {x.mv}"+("" if x.ready else " USED")
            if x.mid=="RANGED": return f"RNG {x.mv}"
            return "NO ACT"
        if x.key=="S": return "HEAL 4"
        return f"REC {x.back}" if x.back else "NO ACT"

    def draw(self):
        pyxel.cls(1)
        if self.state=="TITLE": self.draw_title(); return
        self.draw_header(); self.draw_forecast(); self.draw_formation(); self.draw_readout(); self.draw_controls()
        if self.state=="PLAY" and self.events: self.draw_fx(self.events[self.ei])
        if self.state in ("WIN","LOSE"): self.result()

    def draw_title(self):
        pyxel.text(74,22,"ROTATION BRIGADE",10); pyxel.text(50,36,"FORMATION BATTLE PROTOTYPE",6); pyxel.text(64,62,"CHOOSE A BOSS",7)
        for i,b in enumerate(BOSSES):
            y=91+i*38; on=i==self.bi; pyxel.rect(30,y,196,30,5 if on else 0); pyxel.rectb(30,y,196,30,10 if on else 6)
            pyxel.text(40,y+5,f"{i+1}. {b['name']}",10 if on else 7); pyxel.text(40,y+17,b["desc"],6)
        pyxel.text(58,226,"UP/DOWN + Z / TAP",5)

    def draw_header(self):
        b=self.boss(); shake=0
        if self.state=="PLAY" and self.events:
            e=self.events[self.ei]
            if e["d"]=="BOSS" and e["k"]=="DAMAGE" and self.tick<7: shake=-1 if self.tick%2==0 else 1
        pyxel.text(6+shake,5,f"{b['name']}  TURN {self.turn}",10); pyxel.text(178,5,f"ALIVE {self.alive()}/7",7)
        self.bar(6+shake,16,244,7,self.bhp,self.bmax,8,2); pyxel.text(8+shake,26,f"HP {self.bhp}/{self.bmax}",7)
        if self.dealt: pyxel.text(166,26,f"DEALT {self.dealt}",10)

    def draw_forecast(self):
        pyxel.rect(6,36,244,37,0); pyxel.rectb(6,36,244,37,5); pyxel.text(10,40,"ENEMY FORECAST - HITS FRONT ONLY",6)
        t0=self.turn+(1 if self.state=="DECISION" else 0)
        for i in range(3):
            t=t0+i; n,p,k=self.action(t); target="FRONT ALL" if k=="front_all" else "-" if p<=0 else "FRONT 1"; x=10+i*80
            pyxel.text(x,51,f"T{t} {n}",10 if i==0 else 7); pyxel.text(x,61,f"{p}DMG {target}",8 if p>=36 else 6)

    def draw_formation(self):
        ae=self.events[self.ei] if self.state=="PLAY" and self.events else None
        for r in range(3):
            y=82+r*32; pyxel.text(2,y+3,ROWS[r],7 if r==FRONT else 6); pyxel.text(2,y+13,("TARGET" if r==FRONT else "SUPPORT" if r==MIDDLE else "RECOVER"),8 if r==FRONT else 5)
            for c,k in enumerate(self.form[r]):
                x=28+c*56; bg=0; bd=8 if r==FRONT else 5
                if k and ae:
                    if k==ae["s"]: bg,bd=4,10
                    elif k==ae["d"]: bg,bd=(2,8) if ae["k"]=="DAMAGE" else (3,11)
                    else: bd=5
                pyxel.rect(x,y,52,28,bg); pyxel.rectb(x,y,52,28,bd)
                if k is None: pyxel.text(x+21,y+11,"--",5); continue
                u=self.u[k]; pyxel.rect(x+2,y+2,7,7,COLORS[k]); pyxel.text(x+4,y+3,k,0); pyxel.text(x+12,y+2,u.name[:6],7)
                pyxel.text(x+3,y+11,f"HP {max(0,u.hp):02}/{u.max_hp:02}",8 if u.hp<=u.max_hp*.35 else 11); pyxel.text(x+3,y+20,self.role(r,u)[:12],6)
        pyxel.line(26,80,252,80,8); pyxel.text(169,76,"ENEMY TARGET ROW",8)

    def draw_readout(self):
        pyxel.rect(6,180,244,102,0); pyxel.rectb(6,180,244,102,5)
        if not self.events:
            pyxel.text(12,188,"BATTLE READOUT",10); pyxel.text(12,204,"ATTACKER -> TARGET -> DAMAGE",7); pyxel.text(12,218,"RED DAMAGE / GREEN HEAL / YELLOW SUPPORT",6); pyxel.text(12,236,"ENEMY DAMAGE CAN ONLY HIT FRONT.",8); return
        e=self.events[self.ei]; s,d,k,n=self.name(e["s"]),self.name(e["d"]),e["k"],e["n"]
        col=8 if k=="DAMAGE" else 11 if k=="HEAL" else 10
        pyxel.text(12,187,f"ACTION {self.ei+1}/{len(self.events)}",6); pyxel.text(165,187,f"TURN DMG {self.dealt}",10)
        pyxel.text(12,202,s,10); pyxel.text(12,213,"->",6); pyxel.text(24,213,d,col)
        result="NO DAMAGE" if k=="WAIT" else f"-{n} HP DAMAGE" if k=="DAMAGE" else f"+{n} HP RECOVER" if k=="HEAL" else f"{k} {n}"
        pyxel.text(12,227,result,col); pyxel.text(12,240,e["detail"],6)
        summary=[f"{self.name(x['s'])[:2]}:{x['n']}" for x in self.events if x["k"]=="DAMAGE" and x["d"]=="BOSS"]
        if summary: pyxel.text(12,254,"ALLY " + "  ".join(summary[:6]),7)
        pyxel.text(12,268,f"TAKEN THIS TURN {self.taken}",8 if self.taken else 5)

    def draw_controls(self):
        if self.state=="READY": self.button(88,290,80,22,"START",True)
        elif self.state=="DECISION": self.button(16,290,102,22,"ROTATE",self.sel==0); self.button(138,290,102,22,"STAY",self.sel==1)
        elif self.state=="PLAY": self.button(8,290,72,22,"RESUME" if self.paused else "PAUSE",False); pyxel.text(92,298,"AUTO",6); self.button(176,290,72,22,"NEXT",True)
        elif self.state in ("WIN","LOSE"): self.button(73,290,110,22,"RETRY",True)

    def draw_fx(self,e):
        a,b=self.pos(e["s"]),self.pos(e["d"]); k=e["k"]
        if not a or not b: return
        col=8 if k=="DAMAGE" else 11 if k=="HEAL" else 10
        if a!=b: pyxel.line(a[0],a[1],b[0],b[1],col)
        if k in ("DAMAGE","HEAL","SUPPORT","GUARD"):
            txt=("-" if k=="DAMAGE" else "+")+str(e["n"]) if k!="GUARD" else f"BLOCK {e['n']}"; rise=min(8,self.tick//3)
            x=max(2,min(W-len(txt)*4-2,b[0]-len(txt)*2)); y=b[1]-18-rise; pyxel.rect(x-3,y-3,len(txt)*4+6,12,0); pyxel.text(x-1,y,txt,col); pyxel.text(x,y,txt,col)
        if k=="DAMAGE" and self.tick<8:
            if e["d"]=="BOSS": pyxel.rectb(5,14,246,11,7 if self.tick%2 else 8)
            else:
                p=self.pos(e["d"])
                if p: pyxel.rectb(p[0]-27,p[1]-16,54,30,7 if self.tick%2 else 8)

    def result(self):
        col=10 if self.state=="WIN" else 8; pyxel.rect(50,92,156,54,0); pyxel.rectb(50,92,156,54,col); pyxel.text(103,104,"VICTORY" if self.state=="WIN" else "DEFEAT",col); pyxel.text(76,118,f"TURN {self.turn} / ALIVE {self.alive()}",7)

    def button(self,x,y,w,h,label,on):
        pyxel.rect(x,y,w,h,5 if on else 2); pyxel.rectb(x,y,w,h,10 if on else 6); pyxel.text(x+(w-len(label)*4)//2,y+8,label,10 if on else 7)
    def bar(self,x,y,w,h,v,m,fg,bg):
        pyxel.rect(x,y,w,h,bg); pyxel.rect(x,y,int(w*max(0,v)/m),h,fg) if m else None; pyxel.rectb(x,y,w,h,7)

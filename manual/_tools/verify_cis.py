# 겸용 펌프(옥내소화전 + 간이스프링클러) v5.1.0 독립 검증 — 앱 엔진(index.html <script id="cis-engine"> cisCalc)과 따로 짠 파이썬 구현을 무작위 대조
# usage: python3 -I verify_cis.py <index.html> [건수]
#  · 원문: NFPC 103A · 102(제2025-25호) 제4조 · 제5조 · 제13조 / NFTC 103A(제2024-58호) 2.1.1.2 · 2.2.1 · 2.5.1 · 2.5.3.3 · 2.10.1 · 2.10.2
#           NFTC 102(제2026-34호) 2.1.1 · 2.1.2 · 2.2.1.3 · 2.2.1.4 · 2.3.1 · 2.3.5 · 2.9.1 · 2.9.2 / NFTC 604(제2023-44호) 2.1.1 · 2.1.2
#  · KS 강관 내경 = 외경 − 2 × 두께 (KS D 3507 · KS D 3562 Sch40) — 이 파일에서 다시 계산 · 참고값은 앱과 같은 값을 따로 옮겨 적음
import sys,json,math,random,subprocess,os,tempfile
html=open(sys.argv[1],encoding='utf-8').read(); N=int(sys.argv[2]) if len(sys.argv)>2 else 50000
a=html.index('<script id="cis-engine">')+len('<script id="cis-engine">'); eng=html[a:html.index('</script>',a)]
# 간이 기준 유형 (개수, 방수량, 분) — NFPC 103A 제4조①2호 · 제5조①(단서 80 L/min)
BASE={'A2':(2,50,10),'A5':(5,50,20),'AP2':(2,80,10),'AP5':(5,80,20)}
OD={'3507':{25:(34.0,3.2),32:(42.7,3.5),40:(48.6,3.5),50:(60.5,3.8),65:(76.3,4.2),80:(89.1,4.2),100:(114.3,4.5),125:(139.8,4.5),150:(165.2,5.0),200:(216.3,5.8)},
    '3562':{25:(34.0,3.4),32:(42.7,3.6),40:(48.6,3.7),50:(60.5,3.9),65:(76.3,5.2),80:(89.1,5.5),100:(114.3,6.0),125:(139.8,6.6),150:(165.2,7.1),200:(216.3,8.2)}}
INNER={'SCH10':({d:round(o-2*t,2) for d,(o,t) in OD['3507'].items()},120),'SCH40':({d:round(o-2*t,2) for d,(o,t) in OD['3562'].items()},120),
 'STS':({25:27.6,32:36.8,40:42.8,50:54.8,65:70.0,80:85.0,100:108.2,125:133.4,150:160.0,200:210.0},150),
 'CPVC':({25:26.6,32:35.1,40:40.9,50:52.5,65:62.7,80:79.4,100:101.6,125:127.0,150:154.1,200:203.2},150)}
FIT={25:[0.9,0.54,1.5,0.27,0.18,7.5,4.5,2.0],32:[1.2,0.72,1.8,0.36,0.24,10.5,5.4,2.5],40:[1.5,0.90,2.1,0.45,0.30,13.8,6.5,3.1],50:[2.1,1.20,3.0,0.60,0.39,16.5,8.4,4.0],
 65:[2.4,1.30,3.6,0.75,0.48,19.5,10.2,4.6],80:[3.0,1.80,4.5,0.90,0.60,24.0,12.0,5.7],100:[4.2,2.40,6.3,1.20,0.81,37.5,16.5,7.6],125:[5.1,3.00,7.5,1.50,0.99,42.0,21.0,10.0],
 150:[6.0,3.60,9.0,1.80,1.20,49.5,24.0,12.0],200:[6.5,3.70,14.0,4.00,1.40,70.0,33.0,15.0]}
HOSE={1:(26,None),2:(12,None),3:(7,None),4:(3,None),5:(0,14)}
K={1:1.1,2:1.15}; HP=[3,5,7.5,10,15,20,25,30,40,50,60,75,100,125,150,200]; FK=['e90','e45','teeB','teeS','gate','ball','angle','check']
MPA=9.80665e-3
def loss(segs,pt,lim):
    inner,C=INNER[pt]; F=0.0; vo=0
    for s in segs:
        Di=inner[s['dia']]; L=s['len']+sum(s[k]*FIT[s['dia']][i] for i,k in enumerate(FK))
        F+=10.67*L*(s['flow']/60000)**1.852/(C**1.852*(Di/1000)**4.87)
        v=(s['flow']/60000)/(math.pi*(Di/2000)**2); vo+= v>lim(s)
    return F,vo
def py(sp,ss,h,hs,c,cs,bf):
    Fc,v1=loss(cs,c['pipeType'],lambda s:4)
    n,q,t=BASE[sp['baseType']]; sQ=n*q; sD=n*q*t/1000
    sF,v2=loss(ss,sp['pipeType'],lambda s:6 if s['kind']=='br' else 10)
    sJ=math.ceil((sp['actualHead']+Fc+sF+10)*1.1)
    hA=min(2 if bf==1 else 5,max(1,h['hydrants'])); hQ=130*hA; hD=hA*{1:2.6,2:5.2,3:7.8}[bf]
    hF,v3=loss(hs,h['pipeType'],lambda s:4); r,fx=HOSE[h['hoseType']]; hG=fx if fx is not None else r*h['hoseLen']/100
    hJ=math.ceil((h['actualHead']+Fc+hF+hG+17)*1.1)
    mx=c['mode']=='max'; Q=max(sQ,hQ) if mx else sQ+hQ; D=max(sD,hD) if mx else sD+hD
    R=0 if c['roofEx'] else hD/3; Dt=D+R          # 옥상수조는 옥내소화전 유효수량에만(NFTC 102 2.1.2)
    J=max(sJ,hJ); P=0.163*(Q/1000)*J*K[c['transType']]/(c['pumpEff']/100); hp=P*1.341; Php=next((x for x in HP if x>=hp), math.ceil(hp/5)*5)
    S=J*MPA; ok=S<1.2 or all(x=='SCH40' for x in (h['pipeType'],sp['pipeType'],c['pipeType']))
    Th=(J-h['lowHead']-hG)*MPA
    return dict(Fc=Fc,sJ=sJ,hJ=hJ,sD=sD,hD=hD,Q=Q,D=D,Dt=Dt,J=J,Pkw=P,Php=Php,S=S,ok=ok,prv=Th>0.7,vo=v1+v2+v3,hi=bf>1)
random.seed(20261016); cases=[]
def segs(fl,sizes,kind=False):
    return [dict(**({'kind':random.choice(['br','oth'])} if kind else {}),flow=random.choice(fl),dia=random.choice(sizes),len=round(random.uniform(0,80),1),**{k:random.randint(0,6) for k in FK}) for _ in range(random.randint(1,4))]
for _ in range(N):
    bf=random.randint(1,3); P=list(INNER)
    sp=dict(baseType=random.choice(list(BASE)),actualHead=round(random.uniform(3,120),1),pipeType=random.choice(P))
    h=dict(hydrants=random.randint(1,7),actualHead=round(random.uniform(5,150),1),hoseLen=random.choice([15,30]),hoseType=random.randint(1,5),pipeType=random.choice(P),lowHead=round(random.uniform(-10,30),1))
    c=dict(pumpDia=100,pumpEff=random.randint(10,80),transType=random.randint(1,2),mode=random.choice(['sum','max']),roofEx=random.randint(0,1),pipeType=random.choice(P))
    cases.append((sp,segs([50*k for k in range(1,11)],list(FIT),True),h,segs([130*k for k in range(1,6)],[40,50,65,80,100,125,150,200]),c,segs([10*k for k in range(10,120)],[50,65,80,100,125,150,200]),bf))
tf=os.path.join(tempfile.gettempdir(),'_cis_cases.json'); json.dump(cases,open(tf,'w'))
js=os.path.join(tempfile.gettempdir(),'_cis_run.js')
open(js,'w',encoding='utf-8').write("var window=globalThis;\n"+eng+"\nconst cs=require(process.argv[2]);process.stdout.write(JSON.stringify(cs.map(a=>{const x=cisCalc(...a);"
 "return {Fc:x.Fc,sJ:x.SP.J,hJ:x.H.J,sD:x.SP.D,hD:x.H.D,Q:x.C.Clpm,D:x.C.D,Dt:x.C.Dt,J:x.C.J,Pkw:x.C.Pkw,Php:x.C.Php,S:x.C.Pdis,ok:x.C.pipePressOK,prv:x.H.needPRV,vo:x.C.velOverN,hi:x.C.hiRise}})));")
E=json.loads(subprocess.check_output(['node','--max-old-space-size=4096',js,tf])); bad=[]
for i,(cs,e) in enumerate(zip(cases,E)):
    p=py(*cs)
    for k in p:
        if isinstance(p[k],bool) or k in('vo','Php','hJ','sJ','J','Q'):
            if p[k]!=e[k]: bad.append((i,k,p[k],e[k])); break
        elif abs(p[k]-e[k])>1e-9*max(1,abs(p[k])): bad.append((i,k,p[k],e[k])); break
print(f'검사 {N}건 · 불일치 {len(bad)}건'); print(bad[:5])
print(f'판정 분포 — 최대값 단서 {sum(1 for c in cases if c[4]["mode"]=="max")}건 · 고층 경고 {sum(1 for e in E if e["hi"])}건 · 배관 부적합 {sum(1 for e in E if not e["ok"])}건 · 감압장치 {sum(1 for e in E if e["prv"])}건 · 유속 초과 포함 {sum(1 for e in E if e["vo"])}건 · 간이 전양정 채택 {sum(1 for e in E if e["sJ"]>=e["hJ"])}건')

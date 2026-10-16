// 스모크: 페이지 로드 · 콘솔 오류 · 탭 4개 렌더 · 계산식 안내 · 엔진 값
const {chromium}=require(process.env.MM_PW||'playwright');const {setup,server}=require('./serve.js');const path=require('path');
(async()=>{const repo=path.resolve(__dirname,'../..');const srv=await server(repo,8918);
const b=await chromium.launch();const ctx=await b.newContext({viewport:{width:1400,height:900},serviceWorkers:'block'});await setup(ctx);
const pg=await ctx.newPage();const errs=[];pg.on('pageerror',e=>errs.push('PE '+e.message));pg.on('console',m=>{if(m.type()==='error')errs.push('CE '+m.text())});
await pg.goto('http://127.0.0.1:8918/index.html');await pg.waitForFunction(()=>window.__mmCis,null,{timeout:30000});
const r={};for(const t of [0,1,2,3]){await pg.evaluate(t=>window.__mmCis.setTab(t),t);await pg.waitForTimeout(400);r['tab'+t]=(await pg.evaluate(()=>document.body.innerText.length));}
await pg.evaluate(()=>window.__mmCis.setShowFormula(true));await pg.waitForTimeout(300);r.modal=await pg.evaluate(()=>!!document.querySelector('.fml-box'));
const st=await pg.evaluate(()=>window.__mmCis.get());
r.X=await pg.evaluate(s=>{const x=window.CISENG.calc(s.spSys,s.spSegs,s.hSys,s.hSegs,s.cPump,s.cSegs,s.buildingFloor);const f=v=>+v.toFixed(3);
 return {Fc:f(x.Fc),SP:{A:x.SP.A,Q:x.SP.Clpm,D:f(x.SP.D),F:f(x.SP.F),J:x.SP.J},H:{A:x.H.A,Q:x.H.Clpm,D:f(x.H.D),F:f(x.H.F),G:f(x.H.G),J:x.H.J,Tl:f(x.H.Plow)},
  C:{Q:x.C.Clpm,J:x.C.J,D:f(x.C.D),R:f(x.C.R),Dt:f(x.C.Dt),Pkw:f(x.C.Pkw),HP:x.C.Php,S:f(x.C.Pdis),ok:x.C.pipePressOK,vo:x.C.velOverN,head:x.C.hHead}}},st);
console.log(JSON.stringify(r));console.log('ERR',errs.length,errs.slice(0,5).join(' | '));await b.close();srv.close();})();

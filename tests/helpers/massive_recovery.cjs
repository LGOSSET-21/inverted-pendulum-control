const fs=require('fs');
const file=require('node:path').join(__dirname,'../../visualization/massive-recovery.html');
const html=fs.readFileSync(file,'utf8');
function create(){
 const elements={}; const ctx=new Proxy({},{get:()=>()=>{}});
 const document={getElementById(id){return elements[id]??= {value:id==='scenario'?'aligned':'',clientWidth:1000,clientHeight:620,classList:{add(){},remove(){}},getContext:()=>ctx,getBoundingClientRect:()=>({left:0,top:0,width:1000,height:620}),setPointerCapture(){}}}};
 const box={Math,Array,document,window:{devicePixelRatio:1,addEventListener(){}},performance:{now:()=>0},requestAnimationFrame(){},console};
 const code=html.match(/<script>([\s\S]*?)<\/script>/)[1].replace('reset();requestAnimationFrame(frame);','reset();globalThis.test={derivative,rk4,stepPhysics,reset,points,paint, get s(){return s},get phase(){return phase},get view(){return view},get drag(){return drag},cv,scenario,document,get history(){return history},get trail(){return trail},run(n){for(let i=0;i<n/DT;i++)stepPhysics()}};');
 return new Function('document','window','performance','requestAnimationFrame','return '+code.trimStart().replace('globalThis.test=', 'return '))(document,box.window,box.performance,box.requestAnimationFrame);
}
function grab(t,m){t.paint();const p=t.points(t.s)[m],v=t.view;const e={clientX:v.ox+p[0]*v.scale,clientY:v.oy-p[1]*v.scale,pointerId:1,button:0,isPrimary:true,preventDefault(){}};t.cv.onpointerdown(e);return e;}
module.exports={create,grab};

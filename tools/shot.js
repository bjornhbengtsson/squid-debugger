const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch();
 const f='file://'+require('path').resolve(__dirname,'../design/power-path-v2.html');
 const p=await b.newPage({viewport:{width:1280,height:900}});
 await p.goto(f); await p.waitForTimeout(1500);
 await p.screenshot({path:require('path').resolve(__dirname,'s_light.png'),fullPage:true});
 const el=await p.$('.diagram svg');
 await el.screenshot({path:require('path').resolve(__dirname,'diag_check.png')});
 // high-res export for Altium
 const p2=await b.newPage({viewport:{width:2400,height:2100},deviceScaleFactor:1});
 await p2.goto(f); await p2.waitForTimeout(1500);
 await p2.addStyleTag({content:'.sheet{max-width:none}'});
 await (await p2.$('.diagram svg')).screenshot({path:require('path').resolve(__dirname,'../design/power-block-diagram-v2.png')});
 const p3=await b.newPage({viewport:{width:1280,height:900},colorScheme:'dark'});
 await p3.goto(f); await p3.waitForTimeout(1500);
 await p3.screenshot({path:require('path').resolve(__dirname,'s_dark.png'),clip:{x:0,y:0,width:1280,height:1500}});
 const p4=await b.newPage({viewport:{width:400,height:900}});
 await p4.goto(f); await p4.waitForTimeout(1000);
 console.log('phone overflow', await p4.evaluate(()=>document.documentElement.scrollWidth));
 await b.close();
})();

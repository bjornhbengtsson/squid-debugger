import math
E96=[1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76]
def e96(x):
    d=10**math.floor(math.log10(x)); return min((v*d for v in E96+[10.0]), key=lambda v:abs(v-x))
Vr=2.5; Vh=3.3; Rb=10e3; Rpu=10e3
def th(Rt,Rh):
    a=1/Rb; h=1/Rh; g=1/(Rh+Rpu)
    f=Vr+Rt*(Vr*a+(Vr-Vh)*g); r=Vr+Rt*(Vr*a+Vr*h); return f,r
def design(name,vf,vr):
    # solve: dV = Rt*(2.5h+0.8g); vf = Vr+Rt*(Vr/Rb -0.8g)
    best=None
    for rt in [v*10**k for k in (2,3,4) for v in E96]:
        for rh in [v*10**k for k in (4,5,6) for v in E96]:
            f,r=th(rt,rh); err=abs(f-vf)+abs(r-vr)
            if best is None or err<best[0]: best=(err,rt,rh,f,r)
    e,rt,rh,f,r=best
    # tolerance: Vref 2.5 +-0.2%, comparator offset +-40mV max
    lo=th(rt,rh)[0]*(Vr-0.045)/Vr; hi=th(rt,rh)[0]*(Vr+0.045)/Vr
    print(f"{name:10s} PR1 Rt={rt/1e3:.3g}k Rb=10k Rhyst={rh/1e3:.3g}k  fall={f:.3f}V rise={r:.3f}V hyst={1000*(r-f):.0f}mV  fall-range~{lo:.2f}-{hi:.2f}")
design('3V3 STG-A',3.00,3.12)
design('3V3 STG-B',2.90,3.02)
design('5V  STG-A',4.50,4.70)
design('5V  STG-B',4.35,4.55)
design('5VRF',4.50,4.70)
design('12V',11.0,11.5)
for n,v in [('3V3',3.8),('5V',5.75),('12V',13.5)]:
    rt=e96(Rb*(v/1.06-1)); t=1.06*(1+rt/Rb)
    print(f"OV {n}: Rt={rt/1e3:.3g}k Rb=10k trip typ {t:.2f} (min {1.01*(1+rt/Rb):.2f}, max {1.10*(1+rt/Rb):.2f})  Idiv@nom={1e6*v/(rt+Rb):.0f}uA")
for R in (100,80,59,22.1): print('ILM',R,'k ->',round(65.2/R**0.861,2),'A typ')
for C,I in [(22e-6,1),(44e-6,1),(44e-6,0.3),(20e-6,1)]: print('droop',C,I,round(5e-6*I/C,3))
print('LM4040 bias R from 3V3_AUX: ',[(v,round((v-2.5)/2.0e3*1e6)) for v in (2.8,3.3)],'uA w/ 2.0k')
print('MIC2544 Rset for 0.5A:',230/0.5)

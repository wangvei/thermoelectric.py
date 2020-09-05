import numpy as np
from numpy.linalg import norm
from scipy.interpolate import PchipInterpolator
import matplotlib as mpl
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import matplotlib.ticker
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import ScalarFormatter
from mpl_toolkits import mplot3d
from matplotlib.colors import LightSource
import seaborn as sns
from accum import accum
from thermoelectricProperties import thermoelectricProperties

Si = thermoelectricProperties(latticeParameter=5.401803661945516e-10, dopantElectricCharge=1, electronEffectiveMass=1.08*thermoelectricProperties.me, energyMin=0.0, energyMax=1, dielectric=11.7, numKpoints=800, numBands=8, numQpoints=201, numEnergySampling=1000)
vfrac = 0.05
ml = 0.98*thermoelectricProperties.me # longitudinal effective mass
mt = 0.19*thermoelectricProperties.me # transverse effective mass
bulk_module = 98 # Bulk module (GPA)
rho = 2329  # mass density (Kg/m3)
sp = np.sqrt(bulk_module/rho) # speed of sound
Lv = np.array([[1,1,0],[0,1,1],[1,0,1]])*Si.latticeParameter/2
a_rp = np.cross(Lv[1],Lv[2])/np.dot(Lv[0],np.cross(Lv[1],Lv[2]))
b_rp = np.cross(Lv[2],Lv[0])/np.dot(Lv[1],np.cross(Lv[2],Lv[0]))
a_rp = np.cross(Lv[0],Lv[1])/np.dot(Lv[2],np.cross(Lv[0],Lv[1]))
RLv = np.array([a_rp, b_rp, a_rp])
e = Si.energyRange()
T= Si.temp(TempMin=300, TempMax=301, dT=100)
h= Si.bandGap(Eg_o=1.17, Ao=4.73e-4, Bo=636, Temp=T)
alpha = np.array(0.5*np.tile([1],(1,len(h[0]))))

n = np.array([20])
cc = np.expand_dims(10**n, axis=0)*1e6
kp, band = Si.electronBandStructure(path2eigenval='EIGENVAL', skipLines=6)
kp_rl = 2*np.pi*np.matmul(kp,RLv)
kp_mag = norm(kp_rl, axis=1)
min_band = np.argmin(band[400:600, 4], axis=0)
max_band = np.argmax(band[400:600, 4], axis=0)
kp_vel = kp_mag[401 + max_band:401 + min_band]
energy_vel = band[401 + max_band:401 + min_band, 4] - band[401 + min_band, 4]
enrg_sorted_idx = np.argsort(energy_vel, axis=0)
gVel = Si.electronGroupVelocity(kp=kp_vel[enrg_sorted_idx], energy_kp=energy_vel[enrg_sorted_idx], energyRange=e)
DoS = (1+vfrac)*Si.electronDoS(path2DoS='DOSCAR', headerLines=6, unitcell_volume=2*19.70272e-30, numDoSpoints=2000, valleyPoint=1118, energyRange=e)
JD_f, JD_n = Si.fermiLevel(carrierConcentration=cc, energyRange=e, DoS= DoS, Nc=None, Ao=5.3e21, Temp=T)
fermi, cc_sc = Si.fermiLevelSelfConsistent(carrierConcentration=cc, Temp=T, energyRange=e, DoS=DoS, fermilevel=JD_f)
dis, dfdE = Si.fermiDistribution(energyRange=e, Temp=T, fermiLevel=fermi)

# np.savetxt("Ef",fermi/T/thermoelectricProperties.kB)
# exit()
LD_nondegenerate = np.sqrt(4*np.pi*Si.dielectric*thermoelectricProperties.e0*thermoelectricProperties.kB/thermoelectricProperties.e2C*T/cc_sc) # screening length

m_CB = 0.23*thermoelectricProperties.me*(1+5*alpha*thermoelectricProperties.kB*T)     # conduction band effective mass

Nc = 2*(m_CB*thermoelectricProperties.kB*T/thermoelectricProperties.hBar**2/2/np.pi/thermoelectricProperties.e2C)**(3/2)

fermi_int = np.loadtxt("f", delimiter=',')

LD = np.sqrt(1/(Nc/Si.dielectric/thermoelectricProperties.e0/thermoelectricProperties.kB/T*thermoelectricProperties.e2C*(fermi_int[1]+15*alpha*thermoelectricProperties.kB*T/4*fermi_int[0])))

tau_p_pb, tau_p_npb= Si.tau_p(energyRange=e, alpha=alpha, Dv=2.94, DA=9.5, T=T, vs=sp, D=DoS, rho=rho)

tau_ion = Si.tau_Strongly_Screened_Coulomb(D=DoS, LD=LD, N=cc_sc)

tau = Si.matthiessen(e, 6*tau_p_npb, 6*tau_ion)


uo = np.arange(0.01,0.3,0.01)
tau0 = np.arange(5e-16,1e-15,1e-16)
print(uo.shape,tau0.shape)
xv, yv = np.meshgrid(uo,np.log10(tau0)+16)
Coeff_f = Si.phenomenological(U= uo, tauo = tau0, E = e, DoS=DoS, vg=gVel, Ef=fermi, dfdE=dfdE, Temp=T, tau_b=tau)
PF_f = Coeff_f[0]*Coeff_f[1]**2
print("done")
sns.set()
sns.set_context("paper", font_scale=2, rc={"lines.linewidth": 4})
sns.set_style("ticks", {"xtick.major.size": 2, "ytick.major.size": 2})

plt.figure(figsize=(6.5, 6.5))
ax = plt.axes(projection='3d')
ax.set_axis_on()
ax.grid(False)
ax.view_init(15, -40)
ax.xaxis.pane.set_edgecolor('black')
ax.yaxis.pane.set_edgecolor('black')
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False

surf_s0 = ax.plot_surface(xv, yv, -1*Coeff_f[1]*1e6, color='orange', edgecolor='black', linewidth=0.15, alpha=0.9, rstride=1, cstride=1, shade=True, antialiased=False)  # , cmap=cm.rainbow , cmap=cm.rainbow

ax.set_xlabel('U$_o$ (eV)', fontsize=20, labelpad=15)
ax.set_ylabel('tau$_o$ [log$_{10}$(fs)]', fontsize=20, labelpad=25)
ax.zaxis.set_rotate_label(False)  # disable automatic rotation
ax.set_zlabel('Power factor\n (mW/mK$^2$)', fontsize=20, labelpad=15, rotation=90)
ax.tick_params(axis="y", labelsize=20)
ax.tick_params(axis="x", labelsize=20)
ax.tick_params(axis="z", labelsize=20)
plt.show()
exit()
# fig_0 = plt.figure(figsize=(6.5,4.5))
# ax_0 = fig_0.add_subplot(111)
# ax_0.plot(g[0],h[0], 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_0.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
# ax_0.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_0.tick_params(axis="x", labelsize=16)
# ax_0.set_ylabel('Band gap (eV)', fontsize=16, labelpad=10)
# ax_0.tick_params(axis="y", labelsize=16)
# fig_0.tight_layout()

# fig_1 = plt.figure(figsize=(6.5,4.5))
# ax_1 = fig_1.add_subplot(111)
# ax_1.plot(g[0],alpha[0], 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_1.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
# ax_1.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_1.tick_params(axis="x", labelsize=16)
# ax_1.set_ylabel('Nonparabolic term (eV$^{-1}$)', fontsize=16, labelpad=10)
# ax_1.tick_params(axis="y", labelsize=16)
# fig_1.tight_layout()

# fig_2 = plt.figure(figsize=(6.5,4.5))
# ax_2 = fig_2.add_subplot(111)
# ax_2.plot(e[0],DoS_no_inc[0], 'None', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_2.plot(e[0],DoS[0], 'None', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# # ax_2.plot(e[0],dos_nonparabolic[0], 'None', linestyle='-', color='steelblue',
# #           markersize=6, linewidth=1.5,
# #           markerfacecolor='white',
# #           markeredgecolor='steelblue',
# #           markeredgewidth=1)
# # ax_2.plot(e[0],dos_parabolic[0], 'None', linestyle='-', color='olive',
# #           markersize=6, linewidth=1.5,
# #           markerfacecolor='white',
# #           markeredgecolor='olive',
# #           markeredgewidth=1)
# ax_2.yaxis.set_major_formatter(ScalarFormatter())
# ax_2.set_xlabel('Energy (eV)', fontsize=16, labelpad=10)
# ax_2.tick_params(axis="x", labelsize=16)
# ax_2.set_ylabel('Density of state (#/eV/m$^3$)', fontsize=16, labelpad=10)
# ax_2.tick_params(axis="y", labelsize=16)
# ax_2.ticklabel_format(axis="y", style="sci", scilimits=None)
# fig_2.tight_layout()

# fig_3 = plt.figure(figsize=(6.5,4.5))
# ax_3 = fig_3.add_subplot(111)
# ax_3.plot(e[0],dos_nonparabolic[0], 'None', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_3.plot(e[0],dos_nonparabolic[-1], 'None', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_3.yaxis.set_major_formatter(ScalarFormatter())
# ax_3.set_xlabel('Energy (eV)', fontsize=16, labelpad=10)
# ax_3.tick_params(axis="x", labelsize=16)
# ax_3.set_ylabel('Density of state (#/eV/m$^3$)', fontsize=16, labelpad=10)
# ax_3.tick_params(axis="y", labelsize=16)
# ax_3.ticklabel_format(axis="y", style="sci", scilimits=None)
# fig_3.tight_layout()

# fig_4 = plt.figure(figsize=(6.5,4.5))
# ax_4 = fig_4.add_subplot(111)
# ax_4.plot(e[0],-1*gVel[0]*1e-5, 'None', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_4.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
# ax_4.set_xlabel('Energy (eV)', fontsize=16, labelpad=10)
# ax_4.tick_params(axis="x", labelsize=16)
# ax_4.set_ylabel('Group velocity (x10$^5$ m/s)', fontsize=16, labelpad=10)
# fig_4.tight_layout()

# fig_5 = plt.figure(figsize=(6.5,4.5))
# ax_5 = fig_5.add_subplot(111)
# ax_5.plot(band[1::,], 'None', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_5.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
# ax_5.set_xlabel('BZ tour', fontsize=16, labelpad=10)
# ax_5.tick_params(axis="x", labelsize=16)
# ax_5.set_ylabel('Energy (eV)', fontsize=16)
# ax_5.tick_params(axis="y", labelsize=16)
# ax_5.set_xticks([0,199,399,599,799])
# ax_5.set_xticklabels(["W", "L","$\Gamma$", "X", "W"])
# fig_5.tight_layout()

# fig_6 = plt.figure(figsize=(6.5,4.5))
# ax_6 = fig_6.add_subplot(111)
# ax_6.plot(e[0],dis_no_inc[0], 'None', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_6.plot(e[0],dis[0], 'None', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_6.plot(e[0],dis_no_inc[-1], 'None', linestyle='-.', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_6.plot(e[0],dis[-1], 'None', linestyle='-.', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_6.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
# ax_6.set_xlabel('Energy (eV)', fontsize=16, labelpad=10)
# ax_6.tick_params(axis="x", labelsize=16)
# ax_6.set_ylabel('Fermi distribution', fontsize=16, labelpad=10)
# ax_6.tick_params(axis="y", labelsize=16)
# fig_6.tight_layout()

# fig_7 = plt.figure(figsize=(6.5,4.5))
# ax_7 = fig_7.add_subplot(111)
# ax_7.plot(e[0],dfdE_no_inc[0], 'None', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_7.plot(e[0],dfdE[0], 'None', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_7.plot(e[0],dfdE_no_inc[-1], 'None', linestyle='-.', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_7.plot(e[0],dfdE[-1], 'None', linestyle='-.', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_7.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
# ax_7.set_xlabel('Energy (eV)', fontsize=16, labelpad=10)
# ax_7.tick_params(axis="x", labelsize=16)
# ax_7.set_ylabel('Fermi window (eV$^{-1}$)', fontsize=16)
# ax_7.tick_params(axis="y", labelsize=16)
# fig_7.tight_layout()

# fig_8 = plt.figure(figsize=(6.5,4.5))
# ax_8 = fig_8.add_subplot(111)
# ax_8.plot(g[0],cc_no_inc[0], 'o', linestyle='None', color='black',
#           markersize=12, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='black',
#           markeredgewidth=1,zorder=0)
# ax_8.plot(g[0],JD_n_no_inc[0], 'o', linestyle='-.', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)

# ax_8.plot(g[0],cc_sc_no_inc[0], 'o', linestyle='-.', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)

# ax_8.plot(g[0],cc[0], 'o', linestyle='None', color='black',
#           markersize=12, linewidth=1.5,
#           markerfacecolor='black',
#           markeredgecolor='black',
#           markeredgewidth=1,zorder=0)
# ax_8.plot(g[0],JD_n[0], 'o', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)

# ax_8.plot(g[0],cc_sc[0], 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)

# ax_8.yaxis.set_major_formatter(ScalarFormatter())
# ax_8.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_8.tick_params(axis="x", labelsize=16)
# ax_8.set_ylabel('Carrier concentration( #/m$^{3}$)', fontsize=16)
# ax_8.tick_params(axis="y", labelsize=16)
# ax_8.ticklabel_format(axis="y", style="sci", scilimits=None)
# fig_8.tight_layout()


fig_8_2 = plt.figure(figsize=(6.5,4.5))
ax_8_2 = fig_8_2.add_subplot(111)
ax_8_2.plot(g[0],cc_no_inc[0], 'D', linestyle='None', color='black',
          markersize=12, linewidth=1.5,
          markerfacecolor='black',
          markeredgecolor='black',
          markeredgewidth=1,zorder=0)

ax_8_2.plot(g[0],cc_sc_no_inc[0], 'D', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)

ax_8_2.plot(g[0],cc[0], 'o', linestyle='None', color='black',
          markersize=12, linewidth=1.5,
          markerfacecolor='black',
          markeredgecolor='black',
          markeredgewidth=1,zorder=0)

ax_8_2.plot(g[0],cc_sc[0], 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)

ax_8_2.plot(g[0],cc_direction_down[0], 'p', linestyle='None', color='black',
          markersize=12, linewidth=1.5,
          markerfacecolor='black',
          markeredgecolor='black',
          markeredgewidth=1,zorder=0)

ax_8_2.plot(g[0],cc_sc_direction_down[0], 'p', linestyle='-', color='indigo',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='indigo',
          markeredgewidth=1)

ax_8_2.plot(g[0],cc_1pct[0], 's', linestyle='None', color='black',
          markersize=12, linewidth=1.5,
          markerfacecolor='black',
          markeredgecolor='black',
          markeredgewidth=1,zorder=0)

ax_8_2.plot(g[0],cc_sc_1pct[0], 's', linestyle='-', color='olive',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1)

ax_8_2.yaxis.set_major_formatter(ScalarFormatter())
ax_8_2.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_8_2.tick_params(axis="x", labelsize=16)
ax_8_2.set_ylabel('Carrier concentration( #/m$^{3}$)', fontsize=16)
ax_8_2.tick_params(axis="y", labelsize=16)
ax_8_2.ticklabel_format(axis="y", style="sci", scilimits=None)
fig_8_2.tight_layout()
# fig_9 = plt.figure(figsize=(6.5,4.5))
# ax_9 = fig_9.add_subplot(111)
# ax_9.plot(g[0],fermi_no_inc[0], 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1,zorder=10)
# ax_9.plot(g[0],JD_f_no_inc[0], 'o', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_9.plot(g[0],fermi[0], 'o', linestyle='-.', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1,zorder=10)
# ax_9.plot(g[0],JD_f[0], 'o', linestyle='-.', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)

# ax_9.yaxis.set_major_formatter(ScalarFormatter())
# ax_9.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_9.tick_params(axis="x", labelsize=16)
# ax_9.set_ylabel('E$_f$ (eV)', fontsize=16)
# ax_9.tick_params(axis="y", labelsize=16)
# ax_9.ticklabel_format(axis="y", style="sci", scilimits=None)
# fig_9.tight_layout()


fig_9_2 = plt.figure(figsize=(6.5,4.5))
ax_9_2 = fig_9_2.add_subplot(111)
ax_9_2.plot(g[0],fermi_no_inc[0], 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1,zorder=10)
ax_9_2.plot(g[0],fermi[0], 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1,zorder=10)
ax_9_2.plot(g[0],fermi_direction_down[0], 'o', linestyle='-', color='indigo',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='indigo',
          markeredgewidth=1,zorder=10)
ax_9_2.plot(g[0],fermi_1pct[0], 'o', linestyle='-', color='olive',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1,zorder=10)

ax_9_2.yaxis.set_major_formatter(ScalarFormatter())
ax_9_2.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_9_2.tick_params(axis="x", labelsize=16)
ax_9_2.set_ylabel('E$_f$ (eV)', fontsize=16)
ax_9_2.tick_params(axis="y", labelsize=16)
ax_9_2.ticklabel_format(axis="y", style="sci", scilimits=None)
fig_9_2.tight_layout()

fig_9_3 = plt.figure(figsize=(6.5,4.5))
ax_9_3 = fig_9_3.add_subplot(111)
ax_9_3.plot(g[0],m_CB_no_inc[0]/Si.me, 'o', linestyle='-', color='maroon',
          markersize=12, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1,zorder=10)
ax_9_3.plot(g[0],m_CB_inc[0]/Si.me, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1,zorder=10)
ax_9_3.plot(g[0],m_CB_inc_direction_down[0]/Si.me, 'o', linestyle='-', color='indigo',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='indigo',
          markeredgewidth=1,zorder=10)
ax_9_3.plot(g[0],m_CB_inc_1pct[0]/Si.me, 'o', linestyle='-', color='olive',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1,zorder=10)

ax_9_3.yaxis.set_major_formatter(ScalarFormatter())
ax_9_3.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_9_3.tick_params(axis="x", labelsize=16)
ax_9_3.set_ylabel('Effective mass (kg)', fontsize=16)
ax_9_3.tick_params(axis="y", labelsize=16)
ax_9_3.ticklabel_format(axis="y", style="sci", scilimits=None)
fig_9_3.tight_layout()




fig_10 = plt.figure(figsize=(6.5,4.5))
ax_10 = fig_10.add_subplot(111)
ax_10.plot(g[0],Coeff_no_inc[0]*1e-5, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_10.plot(g[0],Coeff_no_np[0]*1e-5, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_10.plot(g[0],Coeff[0]*1e-5, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_10.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,2]*1e3 * 1e-5, '-o', linestyle='None', color='black',
        markersize=5, linewidth=4,
        markerfacecolor='white',
        markeredgecolor='black',
        markeredgewidth=1)
ax_10.plot(ExpData_SiCfrac_5pct_direction_up[:,0],  ExpData_SiCfrac_5pct_direction_up[:,2]*1e3 * 1e-5, '-o', linestyle='None', color='olive',
        markersize=5, linewidth=4,
        markerfacecolor='white',
        markeredgecolor='olive',
        markeredgewidth=1)
ax_10.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
ax_10.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_10.tick_params(axis="x", labelsize=16)
ax_10.set_ylabel('Conductivity(x10$^5$ S/m)', fontsize=16)
ax_10.tick_params(axis="y", labelsize=16)
fig_10.tight_layout()

fig_10_2 = plt.figure(figsize=(6.5,4.5))
ax_10_2 = fig_10_2.add_subplot(111)
ax_10_2.plot(g[0],Coeff_no_inc[0]*1e-5, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_10_2.plot(g[0],Coeff_direction_down_no_np[0]*1e-5, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_10_2.plot(g[0],Coeff_direction_down[0]*1e-5, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_10_2.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,2]*1e3 * 1e-5, '-o', linestyle='None', color='black',
        markersize=5, linewidth=4,
        markerfacecolor='white',
        markeredgecolor='black',
        markeredgewidth=1)
ax_10_2.plot(ExpData_SiCfrac_5pct_direction_down[:,0],  ExpData_SiCfrac_5pct_direction_down[:,2]*1e3 * 1e-5, '-o', linestyle='None', color='olive',
        markersize=5, linewidth=4,
        markerfacecolor='white',
        markeredgecolor='olive',
        markeredgewidth=1)
ax_10_2.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
ax_10_2.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_10_2.tick_params(axis="x", labelsize=16)
ax_10_2.set_ylabel('Conductivity(x10$^5$ S/m)', fontsize=16)
ax_10_2.tick_params(axis="y", labelsize=16)
fig_10_2.tight_layout()

fig_10_3 = plt.figure(figsize=(6.5,4.5))
ax_10_3 = fig_10_3.add_subplot(111)
ax_10_3.plot(g[0],Coeff_no_inc[0]*1e-5, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_10_3.plot(g[0],Coeff_no_np_1pct[0]*1e-5, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_10_3.plot(g[0],Coeff_1pct[0]*1e-5, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_10_3.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,2]*1e3 * 1e-5, '-o', linestyle='None', color='black',
        markersize=5, linewidth=4,
        markerfacecolor='white',
        markeredgecolor='black',
        markeredgewidth=1)
ax_10_3.plot(ExpData_SiCfrac_1pct_direction_up[:,0],  ExpData_SiCfrac_1pct_direction_up[:,2]*1e3 * 1e-5, '-o', linestyle='None', color='olive',
        markersize=5, linewidth=4,
        markerfacecolor='white',
        markeredgecolor='olive',
        markeredgewidth=1)
ax_10_3.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
ax_10_3.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_10_3.tick_params(axis="x", labelsize=16)
ax_10_3.set_ylabel('Conductivity(x10$^5$ S/m)', fontsize=16)
ax_10_3.tick_params(axis="y", labelsize=16)
fig_10_3.tight_layout()


fig_11 = plt.figure(figsize=(6.5,4.5))
ax_11 = fig_11.add_subplot(111)
ax_11.plot(g[0],Coeff_no_inc[1]*1e6, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_11.plot(g[0],Coeff_no_np[1]*1e6, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_11.plot(g[0],Coeff[1]*1e6, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_11.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,3], '-o', linestyle='None', color='black',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='black',
          markeredgewidth=1)
ax_11.plot(ExpData_SiCfrac_5pct_direction_up[:,0], ExpData_SiCfrac_5pct_direction_up[:,3], '-o', linestyle='None', color='olive',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1)

ax_11.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
ax_11.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_11.tick_params(axis="x", labelsize=16)
ax_11.set_ylabel('Seebeck($\mu$V/K)', fontsize=16)
ax_11.tick_params(axis="y", labelsize=16)
fig_11.tight_layout()

fig_11_2 = plt.figure(figsize=(6.5,4.5))
ax_11_2 = fig_11_2.add_subplot(111)
ax_11_2.plot(g[0],Coeff_no_inc[1]*1e6, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_11_2.plot(g[0],Coeff_direction_down_no_np[1]*1e6, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_11_2.plot(g[0],Coeff_direction_down[1]*1e6, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_11_2.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,3], '-o', linestyle='None', color='black',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='black',
          markeredgewidth=1)
ax_11_2.plot(ExpData_SiCfrac_5pct_direction_down[:,0], ExpData_SiCfrac_5pct_direction_down[:,3], '-o', linestyle='None', color='olive',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1)

ax_11_2.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
ax_11_2.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_11_2.tick_params(axis="x", labelsize=16)
ax_11_2.set_ylabel('Seebeck($\mu$V/K)', fontsize=16)
ax_11_2.tick_params(axis="y", labelsize=16)
fig_11_2.tight_layout()

fig_11_3 = plt.figure(figsize=(6.5,4.5))
ax_11_3 = fig_11_3.add_subplot(111)
ax_11_3.plot(g[0],Coeff_no_inc[1]*1e6, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_11_3.plot(g[0],Coeff_no_np_1pct[1]*1e6, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_11_3.plot(g[0],Coeff_1pct[1]*1e6, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_11_3.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,3], '-o', linestyle='None', color='black',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='black',
          markeredgewidth=1)
ax_11_3.plot(ExpData_SiCfrac_1pct_direction_up[:,0], ExpData_SiCfrac_1pct_direction_up[:,3], '-o', linestyle='None', color='olive',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1)

ax_11_3.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
ax_11_3.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_11_3.tick_params(axis="x", labelsize=16)
ax_11_3.set_ylabel('Seebeck($\mu$V/K)', fontsize=16)
ax_11_3.tick_params(axis="y", labelsize=16)
fig_11_3.tight_layout()

fig_12 = plt.figure(figsize=(6.5,4.5))
ax_12 = fig_12.add_subplot(111)
ax_12.plot(g[0],Coeff_no_inc[2]*1e3, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_12.plot(g[0],Coeff_no_np[2]*1e3, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_12.plot(g[0],Coeff[2]*1e3, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_12.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,4], '-o', linestyle='None', color='black',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='black',
          markeredgewidth=1)
ax_12.plot(ExpData_SiCfrac_5pct_direction_up[:,0], ExpData_SiCfrac_5pct_direction_up[:,4], '-o', linestyle='None', color='olive',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1)

ax_12.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
ax_12.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_12.tick_params(axis="x", labelsize=16)
ax_12.set_ylabel('Power factor(mW/mK$^2$)', fontsize=16, labelpad=10)
ax_12.tick_params(axis="y", labelsize=16)
fig_12.tight_layout()

fig_12_2 = plt.figure(figsize=(6.5,4.5))
ax_12_2 = fig_12_2.add_subplot(111)
ax_12_2.plot(g[0],Coeff_no_inc[2]*1e3, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_12_2.plot(g[0],Coeff_direction_down_no_np[2]*1e3, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_12_2.plot(g[0],Coeff_direction_down[2]*1e3, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_12_2.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,4], '-o', linestyle='None', color='black',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='black',
          markeredgewidth=1)
ax_12_2.plot(ExpData_SiCfrac_5pct_direction_down[:,0], ExpData_SiCfrac_5pct_direction_down[:,4], '-o', linestyle='None', color='olive',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1)

ax_12_2.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
ax_12_2.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_12_2.tick_params(axis="x", labelsize=16)
ax_12_2.set_ylabel('Power factor(mW/mK$^2$)', fontsize=16, labelpad=10)
ax_12_2.tick_params(axis="y", labelsize=16)
fig_12_2.tight_layout()

fig_12_3 = plt.figure(figsize=(6.5,4.5))
ax_12_3 = fig_12_3.add_subplot(111)
ax_12_3.plot(g[0],Coeff_no_inc[2]*1e3, 'o', linestyle='-', color='maroon',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='maroon',
          markeredgewidth=1)
ax_12_3.plot(g[0],Coeff_no_np_1pct[2]*1e3, 'o', linestyle='-', color='tan',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='tan',
          markeredgewidth=1)
ax_12_3.plot(g[0],Coeff_1pct[2]*1e3, 'o', linestyle='-', color='steelblue',
          markersize=6, linewidth=1.5,
          markerfacecolor='white',
          markeredgecolor='steelblue',
          markeredgewidth=1)
ax_12_3.plot(ExpData_SiCfra_0pct_direction_up[:,0], ExpData_SiCfra_0pct_direction_up[:,4], '-o', linestyle='None', color='black',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='black',
          markeredgewidth=1)
ax_12_3.plot(ExpData_SiCfrac_1pct_direction_up[:,0], ExpData_SiCfrac_1pct_direction_up[:,4], '-o', linestyle='None', color='olive',
          markersize=5, linewidth=4,
          markerfacecolor='white',
          markeredgecolor='olive',
          markeredgewidth=1)

ax_12_3.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
ax_12_3.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
ax_12_3.tick_params(axis="x", labelsize=16)
ax_12_3.set_ylabel('Power factor(mW/mK$^2$)', fontsize=16, labelpad=10)
ax_12_3.tick_params(axis="y", labelsize=16)
fig_12_3.tight_layout()


# fig_13 = plt.figure(figsize=(6.5,4.5))
# ax_13 = fig_13.add_subplot(111)

# ax_13.plot(g[0],Coeff_no_inc[3], 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_13.plot(g[0],Coeff[3], 'o', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# # ax_13.plot(g[0],Coeff[0]*g[0]*Coeff[6], 'o', linestyle='-', color='steelblue',
# #           markersize=6, linewidth=1.5,
# #           markerfacecolor='white',
# #           markeredgecolor='steelblue',
# #           markeredgewidth=1)

# ax_13.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
# ax_13.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_13.tick_params(axis="x", labelsize=16)
# ax_13.set_ylabel('$\kappa_e$(W/mK)', fontsize=16, labelpad=10)
# ax_13.tick_params(axis="y", labelsize=16)
# fig_13.tight_layout()

# fig_14 = plt.figure(figsize=(6.5,4.5))
# ax_14 = fig_14.add_subplot(111)
# ax_14.plot(g[0],Coeff_no_inc[4], 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_14.plot(g[0],Coeff[4], 'o', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_14.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
# ax_14.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_14.tick_params(axis="x", labelsize=16)
# ax_14.set_ylabel('$\Delta_1$(eV)', fontsize=16, labelpad=10)
# ax_14.tick_params(axis="y", labelsize=16)
# fig_14.tight_layout()

# fig_15 = plt.figure(figsize=(6.5,4.5))
# ax_15 = fig_15.add_subplot(111)
# ax_15.plot(g[0],Coeff_no_inc[5], 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_15.plot(g[0],Coeff[5], 'o', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_15.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
# ax_15.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_15.tick_params(axis="x", labelsize=16)
# ax_15.set_ylabel('$\Delta_2$([eV]$^2$)', fontsize=16, labelpad=10)
# ax_15.tick_params(axis="y", labelsize=16)
# fig_15.tight_layout()

# fig_16 = plt.figure(figsize=(6.5,4.5))
# ax_16 = fig_16.add_subplot(111)
# ax_16.plot(g[0],Coeff_no_inc[6]*1e8, 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_16.plot(g[0],Coeff[6]*1e8, 'o', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_16.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
# ax_16.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_16.tick_params(axis="x", labelsize=16)
# ax_16.set_ylabel('Lorenz number (x$10^{-8}$[V/K]$^2$)', fontsize=16, labelpad=10)
# ax_16.tick_params(axis="y", labelsize=16)
# fig_16.tight_layout()

# fig_17 = plt.figure(figsize=(6.5,4.5))
# ax_17 = fig_17.add_subplot(111)
# ax_17.plot(g[0],LD_nondegenerate_no_inc[0]*1e9, 'o', linestyle='-.', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)

# ax_17.plot(g[0],LD_no_inc[0]*1e9, 'o', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)

# ax_17.plot(g[0],LD_nondegenerate[0]*1e9, 'o', linestyle='-.', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)

# ax_17.plot(g[0],LD[0]*1e9, 'o', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)


# ax_17.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
# ax_17.set_xlabel('Temperature (K)', fontsize=16, labelpad=10)
# ax_17.tick_params(axis="x", labelsize=16)
# ax_17.set_ylabel('Debyle length (nm)', fontsize=16, labelpad=10)
# ax_17.tick_params(axis="y", labelsize=16)
# fig_17.tight_layout()

# fig_18 = plt.figure(figsize=(6.5,4.5))
# ax_18 = fig_18.add_subplot(111)
# ax_18.plot(e[0],np.log10(tau_no_np[0])+15, 'None', linestyle='-', color='maroon',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='maroon',
#           markeredgewidth=1)
# ax_18.plot(e[0],np.log10(tau_no_np[5])+15, 'None', linestyle='-', color='steelblue',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='steelblue',
#           markeredgewidth=1)
# ax_18.plot(e[0],np.log10(tau_no_np[-1])+15, 'None', linestyle='-', color='tan',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='tan',
#           markeredgewidth=1)

# ax_18.plot(e[0],np.log10(tau_np[0])+15, 'None', linestyle='-', color='olive',
#           markersize=6, linewidth=1.5,
#           markerfacecolor='white',
#           markeredgecolor='olive',
#           markeredgewidth=1)

# ax_18.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
# ax_18.set_xlabel('Energy (eV)', fontsize=16, labelpad=10)
# ax_18.tick_params(axis="x", labelsize=16)
# ax_18.set_ylabel('Lifetime (log$_{10}$[ps])', fontsize=16, labelpad=10)
# ax_18.tick_params(axis="y", labelsize=16)
# fig_18.tight_layout()

plt.show()
exit()

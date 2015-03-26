import os

import matplotlib.pyplot as plt
plt.interactive(True)
plt.xkcd()

import pymice as pm
import matplotlib.ticker as mtick
import matplotlib.dates as mpd
import pytz
import numpy as np
import collections
tzone = pytz.timezone('CET')
import time
import glob

print '  (\ /)'
print '  (0v0)'
print '  (> <)'
print '===#=#=='
print '   \\V/'
print

def get_correct_corner(md, mouse, incorrect=False, start=None, end=None):
    visits = md.getVisits(mice=mouse, startTime=start, endTime=end)
    for v in visits:
      if incorrect and v.CornerCondition < 0 or not incorrect and v.CornerCondition > 0:
        return int(v.Corner)



DATA_DIR = '.'
files = glob.glob('*.zip')
group = 'C57 (8B)'
#dt = -1800. #a magic shift
dt = 0.
cf = pm.ExperimentConfigFile('')

if '_initialized' not in locals() or _initialized != DATA_DIR:
  print 'Initializing...'
  tt00 = time.time()
  loaders = [pm.Loader(filename, getLog=True, getNp=True) for filename in files]
  mm = pm.Merger(*loaders, getNp=True,
                 logAnalysers=(pm.LickometerLogAnalyzer(),
                               pm.PresenceLogAnalyzer(),))

  cf.plotSections()
  for idx, sec in enumerate(cf.sections()):
    start, end = cf.getTime(sec)
    lickTest = pm.TestMiceData('Lickometer')(mm, (start, end))
    if not lickTest:
      print sec, ' Lickometer data corrupted'

    presTest = pm.TestMiceData('Presence')(mm, (start, end))
    if not presTest:
      print sec, ' Presence errors'

  print 'Initialized in %3.1fs!' % (time.time() - tt00)
  _initialized = DATA_DIR

PPcorners = {}
t1, t2 = cf.getTime('Place Pref 1 dark')
for mouse in mm.getMice():
  try:
    PPcorners[mouse] = get_correct_corner(mm, mouse, start=t1, end=t2)
  
  except IndexError:
    PPcorners[mouse] = None

t1, t2 = cf.gettime(['Place Pref 1 dark', 'Place Pref 3 light'])
t1 -= 24 * 3600.
  
nBins = np.ceil((t2 - t1) / bin)
timebins = np.linspace(t1, t1 + nBins * bin, int(nBins) + 1)

fig = plt.figure()
ax = plt.subplot(1, 1, 1)
ax.set_ylim(0, 70)
ax.set_xlim(*mpd.epoch2num([t1, t2]))

for group, label, colour in [('C57 (8B)', 'cohort A', '#00B0E9'),
                             ('C57 (8A)', 'cohort B', '#009C00'),]:
  gr_visits = []
  bin = 12 * 3600.
  mice = sorted(map(unicode, mm.getGroup(group).Animals))
  for mouse in mice:
    corner = PPcorners[mouse]
    visits = mm.getVisits(mice=mouse, startTime=t1, endTime=t2)
    allTimes = [float(v.Start) + dt for v in visits]
    cornerTimes = [float(v.Start) + dt for v in visits if v.Corner == corner]
  
  
    hist, _ = np.histogram(allTimes, bins=timebins)
    cornerHist, _ = np.histogram(cornerTimes, bins=timebins)
    probs = cornerHist / hist.astype(float)
  
    gr_visits.append(probs)
  
  visits = np.ma.masked_invalid(gr_visits)
  

  try:
    tmp = np.ma.masked_invalid(np.delete(data, j, axis=0)) if j is not None else data
    data_mean = visits.mean(axis=0)
    data_yerr = visits.std(axis=0) / np.sqrt(np.logical_not(visits.mask).sum(axis=0))
  
  except ValueError:
    pass
  
  else:
    print mouse
    print data_mean
    ax.errorbar(mpd.epoch2num(timebins[:-1]) + bin / 3600. / 24 / 2,
                data_mean * 100, yerr=data_yerr * 100, zorder=10,
                #lw=1, elinewidth=1,
                marker='o', #ecolor='0.5',
                ecolor='k',
                color=colour, ls='--',
                label=label)
  
hours=[01, 07, 13, 19]
ax.xaxis.set_major_locator(mpd.HourLocator(np.array(hours),tz=tzone))
ax.xaxis.set_major_formatter(mpd.DateFormatter('%d.%m %H:%M', tz=tzone))
ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.0f%%"))
ax.autoscale_view()
fig.autofmt_xdate()
plt.draw()
for sec in cf.sections():
  if sec.endswith('dark'):
    tt1, tt2 = cf.getTime(sec)
    plt.axvspan(mpd.epoch2num(tt1), mpd.epoch2num(tt2),
                color='#E0E0E0', zorder=-10)
for i in xrange(10, 70, 10):
  ax.axhline(i, color='#A0A0A0', lw=1)
plt.legend(loc='lower right')
plt.title('C57BL/6 - PLACE PREFERENCE LEARNING - %s removed' % mouse)
plt.ylabel('% of visits to sugar corner')

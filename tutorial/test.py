import os

import matplotlib.pyplot as plt
plt.interactive(True)
plt.xkcd()

import pymice as pm
import matplotlib.dates as mpd
import pytz
import numpy as np
import collections
tzone = pytz.timezone('CET')
import time

print '  (\ /)'
print '  (0v0)'
print '  (> <)'
print '===#=#=='
print '   \\V/'
print
def plot(*args, **kwargs):
    """Plots something against time; time given as epoch,
    x-axis will be formatted as date, """
    cf = kwargs.pop('cf', None)
    autofmt_date = kwargs.pop('autofmt_date', True)
    myargs = mpd.epoch2num(args[0])
    ax = kwargs.pop('ax', plt.gca())
    ax.plot(myargs, *args[1:], **kwargs)

    ax.xaxis.set_major_locator(mpd.HourLocator(np.array([00]),
                                               tz=tzone))
    if cf is None:
        ax.xaxis.set_major_formatter(mpd.DateFormatter('%d.%m %H:%M', tz=tzone))
    else:
        ax.xaxis.set_major_formatter(cf)

    ax.autoscale_view()
    if autofmt_date:
        ax.get_figure().autofmt_xdate()
    plt.draw()

def get_correct_corner(md, mouse, incorrect=False, start=None, end=None):
    visits = md.getVisits(mice=mouse, startTime=start, endTime=end)
    for v in visits:
      if incorrect and v.CornerCondition < 0 or not incorrect and v.CornerCondition > 0:
        return int(v.Corner)

def get_favorite_corner(md, mouse, start=None, end=None):
    """If more than one corner was visited the same maximum
    number of times then the first corner will be reported
    as 'favorite' (first as sorted in the dictionary)."""
    visits = md.getVisits(mice=mouse, startTime=start, endTime=end)

    corners = collections.Counter(v.Corner for v in visits)
    return corners.most_common(1)[0][0]

def get_stats_correct(md, mouse=None, corner=None, start=None, end=None):
    """Return statistics of visits to the 'correct' or given corner."""
    results = {}
    if mouse is None:
        mice = map(unicode, md.getMice())

    elif type(mouse) == list:
        mice = mouse

    else:
        mice = [mouse]

    for mm in mice:
        visits = md.getVisits(mice=mm, startTime=start, endTime=end)
        if corner is None:
            correct = [v for v in visits if float(v.CornerCondition) > 0]

        else:
            correct = [v for v in visits if int(v.Corner) == corner]

        if len(visits) == 0:
            results[mm] = [np.nan, np.nan, np.nan, np.nan]

        else:
            results[mm] = [len(correct), len(visits),
                    sum(float(v.Duration) for v in correct),
                    sum(float(v.Duration) for v in visits)]


    return results

def plot_nights(cf, ss):
    """Plot night from sections starting with ss"""
    for sec in cf.sections():
        if sec.startswith(ss) and sec.endswith('dark'):
            t1, t2 = cf.gettime(sec) #2time(cf, sec)
            plt.axvspan(mpd.epoch2num(t1), mpd.epoch2num(t2),
            #plt.bar(mpd.epoch2num(t1), 1., width=0.5, bottom=0.,
                        color='0.8', alpha=0.5, zorder=-10)


DATA_DIR = 'C57_NaCl_1'
files = [os.path.join(DATA_DIR, filename) for filename in os.listdir(DATA_DIR)]

if '_initialized' not in locals() or _initialized != DATA_DIR:
  print 'Initializing...'
  tt00 = time.time()
  loaders = [pm.Loader(filename, getLog=True, getNp=True) for filename in files]
  mm = pm.Merger(*loaders, getNp=True,
                 logAnalysers=(pm.LickometerLogAnalyzer(),
                               pm.PresenceLogAnalyzer(),))

  group = 'C57 NaCl (1)'
  cf = pm.ExperimentConfigFile('')
  cf.plotSections()
  for idx, sec in enumerate(cf.sections()):
    start, end = cf.getTime(sec)
    lickTest = pm.TestMiceData('Lickometer')(mm, (start, end))
    if not lickTest:
      print sec, ' Lickometer data corrupted'

    presTest = pm.TestMiceData('Presence')(mm, (start, end))
    if not presTest:
      print sec, ' Presence errors'

  fig = plt.figure()
  tms = [float(v.Start) for v in mm.getVisits(order='Start')]
  plot(tms, range(len(tms)))
  print 'Initialized in %3.1fs!' % (time.time() - tt00)
  _initialized = DATA_DIR

tt00 = time.time()

NPAcorners = {}
npadays = [int(xx.split(' ')[1]) for xx in cf.sections() if xx.startswith('NPA')]
lastnpaday = max(npadays)
t1, _ = cf.getTime('NPA %d dark' %lastnpaday)
_, t2 = cf.getTime('NPA %d light' %lastnpaday)
for mouse in mm.getGroup(group).Animals:
  mouse = unicode(mouse)
  NPAcorners[mouse] = get_favorite_corner(mm, mouse, start=t1, end=t2)

PPcorners = {}
t1, t2 = cf.getTime('Place Pref 1 dark')
for mouse in mm.getGroup(group).Animals:
  mouse = unicode(mouse)
  try:
    PPcorners[mouse] = get_correct_corner(mm, mouse, start=t1, end=t2)

  except IndexError:
    PPcorners[mouse] = None

RLcorners = {}
t1, t2 = cf.getTime('Rev Learning 2 dark')
for mouse in mm.getGroup(group).Animals:
  mouse = unicode(mouse)
  try:
    RLcorners[mouse] = get_correct_corner(mm, mouse, start=t1, end=t2)

  except IndexError:
    RLcorners[mouse] = None

for mouse in mm.getGroup(group).Animals:
  mouse = unicode(mouse)
  try:
    print mouse, NPAcorners[mouse], PPcorners[mouse], RLcorners[mouse]

  except KeyError:
    try:
      print mouse, PPcorners[mouse], RLcorners[mouse]

    except KeyError:
      print mouse, NPAcorners[mouse], PPcorners[mouse]

results = {}
res_aux = {}

for sec in cf.sections():
  if sec.startswith('P') or sec.startswith('R') or sec.startswith('E'):
    print '\n', sec
    t1, t2 = cf.getTime(sec)
    res_aux[sec] = {}

    if sec.startswith('E'):
      for mouse in mm.getGroup(group).Animals:
        mouse = unicode(mouse)
        res_aux[sec].update(get_stats_correct(mm, mouse, corner=RLcorners[mouse],
                                              start=t1, end=t2))

    else:
      results[sec] = get_stats_correct(mm, start=t1, end=t2)

      if sec.startswith('R'):
        for mouse in mm.getGroup(group).Animals:
          mouse = unicode(mouse)
          if RLcorners[mouse] != PPcorners[mouse]:
            res_aux[sec].update(get_stats_correct(mm, mouse, corner=PPcorners[mouse],
                                                  start=t1, end=t2))

          else:
            res_aux[sec][mouse] = [np.nan, np.nan, np.nan, np.nan]

      else: #sec.startswith('P'):
        for mouse in mm.getGroup(group).Animals:
          mouse = unicode(mouse)
          if PPcorners[mouse] != NPAcorners[mouse]:
            res_aux[sec].update(get_stats_correct(mm, mouse, corner=NPAcorners[mouse],
                                                  start=t1, end=t2))

          else:
            res_aux[sec][mouse] = [np.nan, np.nan, np.nan, np.nan]

print 'Elapsed time: ', time.time() - tt00

gr_visits = []
gr_dur = []
gr_licks = []
gr_nps = []
hours=[01, 07, 13, 19]
bin = 12 * 3600.
t1, t2 = cf.gettime(['Place Pref 1 dark', 'Place Pref 3 light'])
t1 -= 24 * 3600.

nBins = np.ceil((t2 - t1) / bin)
timebins = np.linspace(t1, t1 + nBins * bin, int(nBins) + 1)
for mouse, corner in PPcorners.items():
  visits = mm.getVisits(mice=mouse, startTime=t1, endTime=t2)
  allTimes = [float(v.Start) for v in visits]
  allDurations = [float(v.Duration) for v in visits]
  allLicks = [float(v.LickNumber) for v in visits]
  allNps = [float(len(v.Nosepokes)) for v in visits]
  cornerTimes = [float(v.Start) for v in visits if v.Corner == corner]
  cornerDurations = [float(v.Duration) for v in visits if v.Corner == corner]
  cornerLicks = [float(v.LickNumber) for v in visits if v.Corner == corner]
  cornerNps = [float(len(v.Nosepokes)) for v in visits if v.Corner == corner]


  hist, _ = np.histogram(allTimes, bins=timebins)
  cornerHist, _ = np.histogram(cornerTimes, bins=timebins)
  durHist, _ =  np.histogram(allTimes, bins=timebins, weights=allDurations)
  cornerDurHist, _ = np.histogram(cornerTimes, bins=timebins, weights=cornerDurations)
  lickHist, _ = np.histogram(allTimes, bins=timebins, weights=allLicks)
  cornerLicksHist, _ = np.histogram(cornerTimes, bins=timebins, weights=cornerLicks)
  npsHist, _ = np.histogram(allTimes, bins=timebins, weights=allNps)
  cornerNpsHist, _ = np.histogram(cornerTimes, bins=timebins, weights=cornerNps)
  probs = cornerHist / hist.astype(float)
  durationsRatio = cornerDurHist / durHist
  licksRatio = cornerLicksHist / lickHist
  npsRatio = cornerNpsHist / npsHist

  gr_visits.append(probs)
  gr_dur.append(durationsRatio)
  gr_licks.append(licksRatio)
  gr_nps.append(npsRatio)

visits = np.ma.masked_invalid(gr_visits)
durations = np.ma.masked_invalid(gr_dur)
licks = np.ma.masked_invalid(gr_licks)
nps = np.ma.masked_invalid(gr_nps)

fig = plt.figure()
ax = plt.subplot(1, 1, 1)

for label, data in [('visits', visits),
                    ('time', durations),
                    ('nosepokes', nps),
                    ('licks', licks),
                    ]:
  try:
    #data_mean = data.mean(axis=0)
    #data_yerr = data.std(axis=0) / np.sqrt(np.logical_not(data.mask).sum(axis=0))
    ratios = np.log(data / (1.0 - data))
    ratios_mean = np.exp(ratios.mean(axis=0))
    data_mean = ratios_mean / (ratios_mean + 1.0)
    ratios_yerr = np.exp(1.96 * ratios.std(axis=0) / np.sqrt(np.logical_not(ratios.mask).sum(axis=0)))
    ratios_top = ratios_mean * ratios_yerr
    ratios_bottom = ratios_mean / ratios_yerr
    data_top = ratios_top / (ratios_top + 1.0) - data_mean
    data_bottom = data_mean - ratios_bottom / (ratios_bottom + 1.0)
    data_yerr = [data_bottom, data_top]

  except ValueError:
    pass

  else:
    ax.errorbar(mpd.epoch2num(timebins[:-1]) + bin / 3600. / 24 / 2,
                data_mean, yerr=data_yerr, zorder=10,
                lw=1, elinewidth=1, marker='o', ecolor='0.5',
                label="PP, %s to corner with sugar" % label)

ax.xaxis.set_major_locator(mpd.HourLocator(np.array(hours),tz=tzone))
ax.xaxis.set_major_formatter(mpd.DateFormatter('%d.%m %H:%M', tz=tzone))
ax.autoscale_view()
fig.autofmt_xdate()
plt.draw()
plot_nights(cf, 'Place Pref')
plt.legend(loc='best')
plt.title('PP corners')

NPAcorners_copy = NPAcorners.copy()
gr_learn = []
for mouse, corner in NPAcorners.items():
  if corner == PPcorners[mouse]:
    continue

  visits = mm.getVisits(mice=mouse, startTime=t1, endTime=t2)

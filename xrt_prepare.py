import os,sys
import errno
import fnmatch
import numpy
import pexpect
import time

try:
    source_dir=sys.argv[1]
except:
    print("Usage: %s path_to_source_data")
    exit(1)


#source_dir="/SWIFT/S30218/"

xrt_dir=source_dir+"/XRT/"
if not os.path.exists(xrt_dir):
    os.mkdir(xrt_dir)


#################################
#### STEP 1: PREPARE FILES, #####
#################################

print('>> Looking for XRT files ...')


matches_all = []
matches_exp = []
matches_evt = []

def symlink_force(target, link_name):
    try:
        os.symlink(target, link_name)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise e


for root, dirnames, filenames in os.walk(source_dir,followlinks=True):
    print(root)

    for prefix in ["po", "pc"]: 
        for filename in filenames:
            if "/00" in root:
                matches_all.append(os.path.join(root, filename))

        for filename in fnmatch.filter(filenames, '*%s_ex.img*' %prefix):
            print(filename)
            if "/00" in root:
                matches_exp.append(os.path.join(root, filename))

        for filename in fnmatch.filter(filenames, '*%s_cl.evt*' %prefix):
            if "/00" in root:
                matches_evt.append(os.path.join(root, filename))

if not os.path.exists(xrt_dir+"/exposure/"):
    os.mkdir(xrt_dir+"/exposure/")

for match in matches_exp:
    symlink_force(match,xrt_dir+"exposure/"+match.split("/")[-1])

os.chdir(xrt_dir+"/exposure/")

ximage = pexpect.spawn('ximage')
ximage.expect('\[XIMAGE\>')
print('Adding %s' %matches_exp[0])
ximage.sendline('read '+matches_exp[0])
for k in xrange(1,len(matches_exp)):
    ximage.expect('\[XIMAGE\>',timeout=3600)
    print('Adding %s' %matches_exp[k])
    ximage.sendline('read '+matches_exp[k]+'; sum_ima; save_ima')

ximage.expect('\[XIMAGE\>',timeout=3600)
ximage.sendline('write_ima/file="sw_sum_exposures_po_ex.img" template=all')
ximage.expect('\[XIMAGE\>',timeout=3600)
ximage.close()
#print(ximage.before, ximage.after)

print('>> Setting vignetting correction')
pexpect.run("fparkey F sw_sum_exposures_po_ex.img+0 VIGNAPP add=yes")


#print('\n'.join(matches_evt))
if not os.path.exists(xrt_dir+"/events"):
    os.mkdir(xrt_dir+"/events")

#os.remove(xrt_dir+"/events/*")

for match in matches_all:
    #print(xrt_dir+"/events/"+match.split("/")[-1])
    if not os.path.exists(xrt_dir+"/events/"+match.split("/")[-1]):
        symlink_force(match,xrt_dir+"/events/"+match.split("/")[-1])

os.chdir(xrt_dir+"/events/")



#######################################################
#### STEP 2: USE REGIONS ON/OFF TO MEASURE FLUXES #####
#######################################################

xselect = pexpect.spawn('xselect')

try:
    xselect.expect('session name >',timeout=5)
    xselect.sendline('p')
except:
    print('ERR session name')
    print(xselect.before, xselect.after)
try:
    xselect.expect('Use saved session?', timeout=5)
    xselect.sendline('no')
except:
    print('No saved session msg')

#xselect.expect(pexpect.EOF)
lbl='p\:SUZAKU\ \>'

xselect.expect(lbl,timeout=60)
print('Adding %s' %str(matches_evt))
xselect.sendline('read events')
xselect.expect('Enter the Event file dir \>',timeout=60)
xselect.sendline(".")
xselect.expect('Enter Event file list \>',timeout=60)
xselect.sendline(matches_evt[0].split('/')[-1])
xselect.expect('Reset the mission \? \>',timeout=60)
xselect.sendline('yes')
xselect.expect('SWIFT-XRT-PHOTON \>',timeout=60)
#print xselect.before

for k in xrange(1,len(matches_evt)):    
    print('Adding %s' %matches_evt[k])
    xselect.sendline('read events '+matches_evt[k].split('/')[-1])
    try: xselect.expect('[yes]',timeout=10)
    except: pass
    else:
	print('yes!')
	time.sleep(1) 
	xselect.sendline('yes') 
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=60)
    #print xselect.before

print('Extracting events')
try:
    xselect.sendline('extract events copyall=yes')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save events sw_sum_events_po_cl.evt')
except:
    print('Cannot extract events')

try:
    xselect.expect('overwrite it?')
    xselect.sendline('yes')
except:
    print('No clobber needed')

try:
    xselect.expect('Use filtered events as input data file \? \>')
    xselect.sendline('yes')
except:
    print('No reload events needed')

try:
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('extract spectrum')
except:
    print('Cannot extract spectrum')

    
print('Extracting source spectra')
try:
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('filter region '+xrt_dir+'/source.reg')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('extract spectrum ')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save spectrum sw_sum_spectra_po_cl.pha')
    try:
        xselect.expect('overwrite it?')
        xselect.sendline('yes')
    except:
        print('No clobber needed')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('clear region')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('show status')
    print xselect.before
except:
    print('Cannot extract spectrum')



print('Extracting background spectra')
try:
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('filter region '+xrt_dir+'/background.reg')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('extract spectrum')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save spectrum sw_sum_spectra_background_po_cl.pha')
    try:
        xselect.expect('overwrite it?')
        xselect.sendline('yes')
    except:
        print('No clobber needed')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('clear region')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('show status')
    print xselect.before
except:
    print('Cannot extract light curve')

try:
    xselect.expect('overwrite it?')
    xselect.sendline('yes')
except:
    print('No clobber needed')   



print('Extracting source LC')
try:
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('filter region '+xrt_dir+'/source.reg')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('extract curve')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save curve sw_sum_curve_po_cl.fits')
    try:
        xselect.expect('overwrite it?')
        xselect.sendline('yes')
    except:
        print('No clobber needed')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save curve sw_sum_curve_po_cl.lc')
    try:
        xselect.expect('overwrite it?')
        xselect.sendline('yes')
    except:
        print('No clobber needed')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('clear region')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('show status')
    print xselect.before
except:
    print('Cannot extract light curve')

try:
    xselect.expect('overwrite it?')
    xselect.sendline('yes')
except:
    print('No clobber needed')

try:
    xselect = pexpect.spawn('rm sw_sum_curve_po_cl.dat; fplot sw_sum_curve_po_cl.fits TIME RATE[ERROR] - /null "wd sw_sum_curve_po_cl.dat"')
    print(xselect.before)
    xselect.expect('PLT\>',timeout=3600)
    xselect.sendline('exit')
except:
    print('Error exporting the LC to dat')


print('Extracting background LC')
try:
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('filter region '+xrt_dir+'/background.reg')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('extract curve')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save curve sw_sum_curve_background_po_cl.fits')
    try:
        xselect.expect('overwrite it?')
        xselect.sendline('yes')
    except:
        print('No clobber needed')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save curve sw_sum_curve_background_po_cl.lc')
    try:
        xselect.expect('overwrite it?')
        xselect.sendline('yes')
    except:
        print('No clobber needed')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('clear region')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('show status')
    print xselect.before
except:
    print('Cannot extract light curve')

try:
    xselect.expect('overwrite it?')
    xselect.sendline('yes')
except:
    print('No clobber needed')


try:
    x = pexpect.spawn('rm sw_sum_curve_background_po_cl.dat; fplot sw_sum_curve_background_po_cl.fits TIME RATE[ERROR] - /null "wd sw_sum_curve_background_po_cl.dat"')
    xselect.expect('PLT\>',timeout=3600)
    xselect.sendline('exit')
except:
    print('Error exporting the LC to dat')

print('Extracting source image')
try:
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('filter region '+xrt_dir+'/source.reg')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('extract image')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save image sw_sum_image_po_cl.fits')
    try:
        xselect.expect('overwrite it?')
        xselect.sendline('yes')
    except:
        print('No clobber needed')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('clear region')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('show status')
    print xselect.before
except:
    print('Cannot extract image')

try:
    xselect.expect('overwrite it?')
    xselect.sendline('yes')
except:
    print('No clobber needed')
    


print('Extracting background image')
try:
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('filter region '+xrt_dir+'/background.reg')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('extract image')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('save image sw_sum_image_background_po_cl.fits')
    try:
        xselect.expect('overwrite it?')
        xselect.sendline('yes')
    except:
        print('No clobber needed')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('clear region')
    xselect.expect('SWIFT-XRT-PHOTON \>',timeout=3600)
    xselect.sendline('show status')
    print xselect.before
except:
    print('Cannot extract image')

try:
    xselect.expect('overwrite it?')
    xselect.sendline('yes')
except:
    print('No clobber needed')

   
#print(xselect.before,xselect.after)

xselect.close()






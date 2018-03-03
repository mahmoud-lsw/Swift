#!/bin/env python2

import numpy as np

xrt_dir="./"

qdp_file = open(xrt_dir+"ObsData_UnfAbsModel.qdp","r")
qdp_content = qdp_file.read()
qdp_file.close()

qdp_header,qdp_data = qdp_content.split("NO")[0].split('!\n')

qdp_data = np.array([[float(k) for k in line.split(' ')] for line in qdp_data.strip().split('\n')])

observed_data0   = qdp_data[:,2]
observed_dataerr = qdp_data[:,3]

qdp_file = open(xrt_dir+"ObsData_FoldedModel_ratio.qdp","r")
qdp_content = qdp_file.read()
qdp_file.close()

qdp_header,qdp_data = qdp_content.split("NO")[0].split('!\n')

qdp_data = np.array([[float(k) for k in line.split(' ')] for line in qdp_data.strip().split('\n') if len(line)>4])

#### FOLDED DATA / FOLDED MODEL

observed_data        = qdp_data[:,1]
ratio_data2model     = qdp_data[:,2]
ratio_data2model_err = qdp_data[:,3]

qdp_file = open(xrt_dir+"/UnfData_UnfDeAbsModel.qdp","r")
qdp_content = qdp_file.read()
qdp_file.close()

qdp_header,qdp_data = qdp_content.split("NO")[0].split('!\n')

qdp_data = np.array([[float(k) for k in line.split(' ')] for line in qdp_data.strip().split('\n')])


#### UNFOLDED AND DEABSORBED MODEL
#### UNF+DEABS DATA = (UNF+DEABS MODEL / FOLDED MODEL)*FOLDED DATA [???]

#ratio_data2intrinsic     = qdp_data[:,2]
#ratio_data2intrinsic_err = qdp_data[:,3]

intrinsic_model = qdp_data[:,4]

data_deabsorbed     = 1.*ratio_data2model*intrinsic_model
data_deabsorbed_err = 1.*ratio_data2model_err*intrinsic_model

'''
ratio_deabsorb = 1.0*ratio_data2intrinsic/ratio_data2model
ratio_deabsorb_err = np.sqrt(\
    (ratio_data2intrinsic_err/ratio_data2model)**2 +\
    (ratio_data2model_err * ratio_data2intrinsic_err/(ratio_data2model**2))**2)
'''

SED_obsdata = observed_data0*qdp_data[:,0]**2
SED_obsdataerr = observed_dataerr*qdp_data[:,0]**2
SED_model = intrinsic_model*qdp_data[:,0]**2
SED_deabsorbed = data_deabsorbed*qdp_data[:,0]**2
SED_deabsorbed_err = data_deabsorbed_err*qdp_data[:,0]**2

data_all = np.transpose([qdp_data[:,0],qdp_data[:,1],data_deabsorbed,data_deabsorbed_err,intrinsic_model])
sed_all = np.transpose([qdp_data[:,0],qdp_data[:,1],SED_deabsorbed,SED_deabsorbed_err,SED_model])

np.save(xrt_dir+'/PKS1424_XRT_diffSpec_deabsorbed.npy',data_all)
np.save(xrt_dir+'/PKS1424_XRT_SED_deabsorbed.npy',sed_all)


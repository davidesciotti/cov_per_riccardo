import sys
import time
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

project_path = Path.cwd().parent

sys.path.append(f'{project_path.parent}/common_data/common_lib')
import my_module as mm
import cosmo_lib as csmlib

sys.path.append(f'{project_path.parent}/common_data/common_config')
import ISTF_fid_params as ISTFfid
import mpl_cfg

matplotlib.use('Qt5Agg')
plt.rcParams.update(mpl_cfg.mpl_rcParams_dict)
start_time = time.perf_counter()

# ! settings
survey_area_ISTF = 15_000  # deg^2
deg2_in_sphere = 41252.96  # deg^2 in a spere

fsky = survey_area_ISTF / deg2_in_sphere
zbins = 10
nbl = 32
n_gal = 30
sigma_eps = 0.3
EP_or_ED = 'EP'
GL_or_LG = 'GL'
triu_tril = 'triu'
row_col_major = 'row-major'
probe_ordering = [['L', 'L'], [GL_or_LG[0], GL_or_LG[1]], ['G', 'G']]
block_index = 'ell'
# ! end settings

ind = mm.build_full_ind(triu_tril, row_col_major, zbins)

cl_LL_3d = np.load(f'{project_path}/data/input_riccardo/CLL.npy').transpose(2, 0, 1)
cl_GG_3d = np.load(f'{project_path}/data/input_riccardo/CGG.npy').transpose(2, 0, 1)
cl_LG_3d = np.load(f'{project_path}/data/input_riccardo/CLG.npy').transpose(2, 0, 1)
cl_GL_3d = cl_LG_3d.transpose(0, 2, 1)

ell_values = np.load(f'{project_path}/data/input_riccardo/ell.npy')
delta_ell = np.load(f'{project_path}/data/input_riccardo/delta_ell.npy')

cl_3x2pt_5d = np.zeros((2, 2, nbl, zbins, zbins))
cl_3x2pt_5d[0, 0, :, :, :] = cl_LL_3d
cl_3x2pt_5d[0, 1, :, :, :] = cl_LG_3d
cl_3x2pt_5d[1, 0, :, :, :] = cl_GL_3d
cl_3x2pt_5d[1, 1, :, :, :] = cl_GG_3d

noise_3x2pt_4d = mm.build_noise(zbins, 2, sigma_eps2=sigma_eps ** 2, ng=n_gal, EP_or_ED=EP_or_ED)

# create a fake axis for ell, to have the same shape as cl_3x2pt_5d
noise_3x2pt_5d = np.zeros((2, 2, nbl, zbins, zbins))
for probe_A in (0, 1):
    for probe_B in (0, 1):
        for ell_idx in range(nbl):
            noise_3x2pt_5d[probe_A, probe_B, ell_idx, :, :] = noise_3x2pt_4d[probe_A, probe_B, ...]

cl_LL_5d = cl_LL_3d[np.newaxis, np.newaxis, ...]
cl_GG_5d = cl_GG_3d[np.newaxis, np.newaxis, ...]
noise_LL_5d = noise_3x2pt_5d[0, 0, ...][np.newaxis, np.newaxis, ...]
noise_GG_5d = noise_3x2pt_5d[1, 1, ...][np.newaxis, np.newaxis, ...]

cov_GO_WL_6D = mm.covariance_einsum(cl_LL_5d, noise_LL_5d, fsky, ell_values, delta_ell)[0, 0, 0, 0, ...]
cov_GO_GC_6D = mm.covariance_einsum(cl_GG_5d, noise_GG_5d, fsky, ell_values, delta_ell)[0, 0, 0, 0, ...]

# actually, only the 3x2pt is needed
cov_3x2pt_GO_10D_arr = mm.covariance_einsum(cl_3x2pt_5d, noise_3x2pt_5d, fsky, ell_values, delta_ell)
cov_3x2pt_dict_10D = mm.cov_10D_array_to_dict(cov_3x2pt_GO_10D_arr)
cov_3x2pt_GO_4D = mm.cov_3x2pt_dict_10D_to_4D(cov_3x2pt_dict_10D, probe_ordering, nbl, zbins, ind.copy(), GL_or_LG)
cov_3x2pt_GO_2D = mm.cov_4D_to_2D(cov_3x2pt_GO_4D, block_index=block_index)

mm.matshow(cov_3x2pt_GO_2D, log=True, abs_val=True)

np.savez_compressed('../output/cov_3x2pt_GO_10D_arr.npz', cov_3x2pt_GO_10D_arr)
np.savez_compressed('../output/cov_3x2pt_GO_4D.npz', cov_3x2pt_GO_4D)
np.savez_compressed('../output/cov_3x2pt_GO_2D.npz', cov_3x2pt_GO_2D)

cov_loaded = np.load('../output/cov_3x2pt_GO_10D_arr.npz')['arr_0']
# standard modules

# dependency modules
from niix2bids.classes import Volume
import nibabel
import numpy as np

# local modules


########################################################################################################################
def read_all_nifti_header(volume_list: list[Volume]) -> None:
    for vol in volume_list:
        
        # load header
        nii = nibabel.load(vol.nii.path)

        # fetch raw parmeters
        matrix = nii.header.get_data_shape()
        resolution = nii.header.get_zooms()
        fov = [ mx*res for mx,res in zip(matrix, resolution)]

        # format parameters
        matrix = list(matrix)
        resolution = np.round(resolution, 3).astype(float).tolist()
        fov = [int(x) for x in fov]

        # save parameters
        vol.seqparam['Matrix'    ] = matrix
        vol.seqparam['Resolution'] = resolution
        vol.seqparam['FoV'       ] = fov


########################################################################################################################
def concat_bidsfields_to_seqparam(volume_list: list[Volume]) -> None:
    for vol in volume_list:
        vol.seqparam.update( vol.bidsfields )


########################################################################################################################

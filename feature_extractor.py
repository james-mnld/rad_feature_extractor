'''
Expected folder structure:
- PATIENTS_FOLDER
	- Patient1
		- Day1
		- Day2
		- Day3
		- ...
	- Patient2
		- Day1
		- Day2
		- Day3
		- ...
	- Pattent3
		- Day1
		- Day2
		- Day3
		- ...
	...
- RESULTS_FOLDER
'''

'''
TO MODIFY:
'''
# folder where each patient folder is located
PATIENTS_FOLDER = 'Patients'

# folder where results for each patient will be saved
RESULTS_FOLDER = 'Patients_results'

# organ of interest. code might use MASK_OPTIONS dictionary defined below
organ = 'rectum'


# ______________________________________________________________________________________________________________________

import os, time, subprocess, shutil
import SimpleITK as sitk
import radiomics as rad
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from radiomics import featureextractor


'''
Function to instantiate extractor
- modify extractor parameters as needed
- check pyradiomics docs for more information: https://pyradiomics.readthedocs.io/en/latest/radiomics.html
'''
def instantiate_extractor():
    print('Instantiating extractor...')
    extractor = featureextractor.RadiomicsFeaturesExtractor(normalize=True,
                                                            correctMask=True,
                                                            resampledPixelSpacing=[0.5,0.5,0.5])
    extractor.addProvenance()
    extractor.enableAllImageTypes()
    return extractor

'''
Function to generate masks using RT-struct
- plastimatch must be installed and added to $PATH
- input:
	- src_folder: path to folder containing RT-struct file (recommended to be in the same folder as the rest of the dicom files)
	- msks_folder: destination path for the masks to be generated
'''
def generate_masks(src_folder, msks_folder):
    msks_cmd = 'plastimatch convert --input %s --output-prefix %s'%(src_folder, msks_folder)
    #print(msks_cmd)
    if os.path.isdir(msks_folder) and len(os.listdir(msks_folder)) > 0:
        print('Masks already at: ', msks_folder)
    else:
        print('Generating masks...')
        if len(os.listdir(src_folder)) == 0:
    	    print('Source folder is empty: ', src_folder)
    	    return 0
        proc = os.system(msks_cmd)
        #proc.wait()
        print('Masks generated at: ', msks_folder)
    return 1


'''
Function to combine all dicom slices to one nrrd file
- plastimatch must be installed and added to $PATH
- input:
	- src_folder: path to folder containing the dicom slices
	- scan_path: destination path for the combined image
'''
def generate_combined_image(src_folder, scan_path):
    scan_cmd = 'plastimatch convert --input %s --output-img %s'%(src_folder, scan_path)
    print(scan_cmd)
    if os.path.exists(scan_path):
        print('Full nrrd image already at: ', scan_path)
    else:        
        print('Combining dicoms and converting to nrrd...')
        if len(os.listdir(src_folder)) == 0:
    	    print('Source folder is empty: ', src_folder)
    	    return 0
        proc = os.system(scan_cmd)
        #proc.wait()
        print('Full nrrd image generated at: ', scan_path)
    return 1


# dictionary used for translation (mask names were in portuguese)
MASK_OPTIONS = {#'prostate':'prostata',
               'bladder':'bexiga',
               'penile_bulb':'bulbo peniano',
               #'rectum':'reto',
               'pelvic_lymph':'linf pelvicos',
               'sem_vesicles':'vesiculas sem',
               'femur_esq':'femur esq',
               'femur_dir':'femur dir',
               'intestinal_sac':'saco intestinal',
               'body':'corpo'
              }
'''
Function to fetch mask file corresponding to specified organ
- input:
	- organ: string name of organ ('bladder', 'rectum', 'prostate', etc.)
	- msks_folder: path to folder containing the generated masks
'''
def get_mask_for_organ(organ, msks_folder):
	# check translation dictionary
    if organ.lower() in MASK_OPTIONS.keys():
        organ_str = MASK_OPTIONS[organ]
    else:
        organ_str = organ.lower()
    # generate list of mask paths ignoring hidden files (names of hidden files start with '.')
    msk_filenames = sorted([f for f in os.listdir(msks_folder) if not f.startswith('.')], key=lambda f: f.lower())
    for msk_filename in msk_filenames:
        if organ_str in msk_filename.lower():
            msk_path = os.path.join(msks_folder, msk_filename)
            print('Found mask path: ', msk_path)
            return msk_path
    return None


'''
Function to get list of extracted features
- input:
	- results: data returned by 'execute' function of RadiomicsFeaturesExtractor instance
	- extractor: instance of RadiomicsFeaturesExtractor
'''
def get_features_list(results, extractor):
    features_list = []
    imageTypes = ['original','exponential','gradient','lbp-2D','logarithm','square','squareroot','wavelet']
    waveletTypes = ['LLH','LHL','LHH','HLL','HLH','HHL','HHH','LLL']
    for waveletType in waveletTypes:
        imageTypes.append('wavelet-' + waveletType)
    for imageType in imageTypes:
        for feature_class in rad.getFeatureClasses().keys():
            for feature in extractor.getFeatureNames(feature_class):
                feature_name = '_'.join([imageType, feature_class, feature])
                if feature_name in results.keys():
                    features_list.append(feature_name)
    return features_list


'''
Function to start extraction with some added options
- extractor: instance of RadiomicsFeaturesExtractor
- scan_path: path to combined image
- msk_path: path to mask
- day_name: folder for specific day of patient
- voxelbased: boolean. Set as True for voxelbased extraction
- verbose: boolean. Set as True for more info printed during extraction
'''
def execute_extraction(extractor, scan_path, msk_path, day_name, voxelbased, verbose):
    if verbose:
        rad.setVerbosity(20)
    
    print('Extracting features...')
    t0 = time.time()
    
    if voxelbased:
        results = extractor.execute(scan_path, msk_path, voxelBased=True)
    else:
        results = extractor.execute(scan_path, msk_path)
        
    features_list = get_features_list(results, extractor)
    data = {'Day':day_name}
    for feat in features_list:
        data[feat] = results[feat]
        
    tf = time.time()
    print('Feature extraction completed')
    
    if (tf-t0) > 3600:
        print('\tElapsed Time: %f hours'%((tf-t0)/3600))
    elif (tf-t0) > 60:
        print('\tElapsed Time: %f min'%((tf-t0)/60))
    else:
        print('\tElapsed Time: %f sec'%(tf-t0))
    return data


'''
Function to save data from freature extraction
- input:
	- data: dictionary contaning 'feature_name':value
	- csv_path: path to csv file where data will be stored
'''
def save_data(data, csv_path):
    data_frame = pd.DataFrame({f:[data[f]] for f in data.keys()})
    print('Saving data...')
    # check if csv file already exists
    if os.path.isfile(csv_path):
        existing_data = pd.read_csv(csv_path)
        if len(existing_data.columns) == len(data_frame.columns):
            with open(csv_path, 'a') as f:
                data_frame.to_csv(f, header=False, index=False)
        else:
            print('Data NOT saved: new data does not have the same length as existing data')
            return
    else:    
        with open(csv_path, 'w') as f:
            data_frame.to_csv(f, index=False)
    print('Data saved at: ', csv_path)


'''
Function to execute feature extraction pipeline
- input:
	- patient_name: string corresponding to name of patient folder (patient folder has folders corresponding to each day)
	- day_name: string corresponding to name of day folder
	- organ: string corresponding to specified organ ('rectum', 'prostate', etc.)
	- voxelbased: boolean. Set as True for voxelbased extraction
	- verbose: boolean. Set as True for more info printed during extraction
'''
def execute_extraction_pipeline(patient_name, day_name, organ, voxelbased=False, verbose=False):
	if verbose:
	    rad.setVerbosity(50)
    
    # define paths
    src_folder = os.path.join(PATIENTS_FOLDER, patient_name, day_name)
    dest_folder = os.path.join(RESULTS_FOLDER, patient_name, day_name)
    msks_folder = os.path.join(dest_folder, 'Masks')
    scan_path = os.path.join(dest_folder, '_'.join([patient_name, day_name])+'.nrrd') 
    
    if voxelbased:
        csv_path = os.path.join(RESULTS_FOLDER, patient_name, organ+'_results_vox.csv')
    else:
        csv_path = os.path.join(RESULTS_FOLDER, patient_name, organ+'_results.csv')
    
    # generate masks, and combine and convert dicoms
    if generate_masks(src_folder, msks_folder) == 0:
    	return
    if generate_combined_image(src_folder, scan_path) == 0:
    	return
    
    msk_path = get_mask_for_organ(organ, msks_folder)
    if msk_path is None:
        print('No mask available for %s'%(organ))
        print('\tTry: %a'%[x[:-4].lower() for x in os.listdir(msks_folder)])
        exit()
        return

    extractor = instantiate_extractor()
    
    if os.path.isfile(csv_path):
    	dat = pd.read_csv(csv_path)
    	for day in dat['Day']:
    	    if day == day_name:
    	    	print('Features for %s is already extracted'%day_name)
    	    	return
    data = execute_extraction(extractor, scan_path, msk_path, day_name, voxelbased, verbose)
    
    save_data(data, csv_path)
    return data


#___________________________________________________________________
# main program

def main():
	for patient in os.listdir(PATIENTS_FOLDER):
		print('Patient: ', patient, '\n')
		patient_path = os.path.join(PATIENTS_FOLDER, patient)
		for day in os.listdir(patient_path):
			print('Day: ', day)
			execute_extraction_pipeline(patient, day, organ)

if __name__ == "__main__":
	main()


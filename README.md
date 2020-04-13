# rad_feature_extractor
Feature extraction pipeline using pyradiomics (v 2.1.2).

feature_extractor.py extracts radiomic features from patient scans under PATIENTS_FOLDER and produces a RESULTS_FOLDER with the same folder structure as PATIENTS_FOLDER. Instead of having the dicom files, each day folder in RESULTS_FOLDER will have the combined image (.nrrd file) and a 'Masks' folder containing the generated masks (.mha files). Each patient folder in RESULTS_FOLDER will have the extracted data in csv form with the features as columns and day numbers as rows.

## Expected folder structure:

- PATIENTS_FOLDER:

	  - Patient1
	  
		    - Day1
		    
            		- RT-struct.dcm
            		- slice1.dcm
            		- slice2.dcm
            		- ...
			
		    - Day2
		    
            		- RT-struct.dcm
            		- slice1.dcm
            		- slice2.dcm
            		- ...
			
		    - Day3
		    
            		- RT-struct.dcm
            		- slice1.dcm
            		- slice2.dcm
            		- ...
			
		    - ...
		    
	  - Patient2
	  
		    - ...
		    
	  - Patient3
	  
		    - ...
		    
	  - ...
    
## To modify in code:
1. PATIENTS_FOLDER: folder where each patient folder is located
2. RESULTS_FOLDER: folder where results for each patient will be saved
3. organ: organ of interest ('prostate', 'rectum', 'bladder', etc.) (must be available from the RT-struct)
    - note that the string value for this variable must correspond to an available mask of the same name
    - also, the extraction pipeline might use a defined dictionary in the code that translates the english name of the organ into portuguese.

## Default settings of extractor:
The RadiomicsFeaturesExtractor instance uses a resampledPixelSpacing of 0.5cm x 0.5cm x 0.5cm, and normalizes the pixel values of the images. These settings can be modified in the instantiate_extractor() function. For more information, see https://pyradiomics.readthedocs.io/en/latest/radiomics.html.
The feature extractor instance also has all available image types enabled.

## Additional requirements:
- feature_extractor.py uses plastimatch (http://plastimatch.org/plastimatch.html) to combine the dicom slices and extract the masks from the RT-struct. plastimatch must be installed and added to $PATH.
- the code was written in python 3.6.8

## To run:
- python path_to_/feature_extractor.py
- python3 path_to_/feature_extractor.py

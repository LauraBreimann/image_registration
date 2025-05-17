<div align="center">
  
# Chromatic Aberration Correction Pipeline
</div>

This project provides a simple and flexible pipeline to correct chromatic aberrations in multi-channel fluorescence microscopy images.

Chromatic shifts are corrected using affine transformations, determined from bead samples or multi-spectral reference images. Once estimated, these transformations can then be applied to experimental images using Python scripts or Jupyter notebooks.

## Pipeline Overview

* _**1.	Prepare (bead) images for chromatic shift detection**_
* _**2.	Determine chromatic shifts**_
* _**3.	Apply chromatic shifts to experimental images**_
* _**4.	Check quality of alignment**_



<br />



<div style="text-align: justify">
  
 ## 1.	Prepare (bead) images for chromatic shift detection

To measure chromatic aberration reliably:

- Prepare a bead slide containing sub-resolution fluorescent beads (e.g. 100–200 nm) visible in all relevant channels
- Acquire z-stacks for each channel on the microscope system
- Generate a max intensity projection
- Convert that into a time-series stack in Fiji (one channel per timepoint, e.g. using macro Resave_as_timeseries) 

It’s recommended to save this as a before/after reference.

_TODO: Link to bead slide prep protocol._

---
  
## 2. Determine chromatic shiftst 

Use ImageJ/Fiji with the plugin:

> `Plugins > Registration > Descriptor Based Registration (2d/3d + T)`  
> by Stephan Preibisch

- Load your time-series image (one channel per timepoint).  
- Use "Affine" as the transformation and "Rigid" as regularization.  
- Inspect the registered result by converting the stack back to multichannel, overlaying channels (e.g. RGB).  
- Log window shows the transformation matrices.

Save these matrices into a JSON file (`transformation_dicts.json`):

```json
{
  "Microscope 1": {
    "ch1": [[1.0, 0.0, 0.5], [0.0, 1.0, -0.3], [0.0, 0.0, 1.0]],
    "ch2": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
  }
}
```

## 3. Apply Chromatic Shifts to Images

Use the scripts in this repository to apply the transformations to raw experimental images.

Supported input modes:
- multichannel — one TIFF per field of view with all channels: shape [C, Z, Y, X]
- split_channels_preserve_structure — one TIFF per channel (e.g. fov01_ch1.tif), defined via a CSV




### Command-Line Usage

#### Install required Python dependencies

```bash
pip install -r requirements.txt
```

##### Multichannel Images

```bash
python channel_alignment.py \
  --input_mode multichannel \
  --input_folder data/raw_multichannel \
  --output_folder data/aligned_multichannel \
  --transformation_file transformations/transformation_dicts.json \
  --microscope "Microscope 1" \
  --channel_order ch1 ch2 ch3
```


##### Split-Channel Images (based on CSV)

```bash
  python channel_alignment.py \
  --input_mode split_channels_preserve_structure \
  --channel_map_file metadata/channel_map.csv \
  --output_folder data/aligned \
  --transformation_file transformations/transformation_dicts.json \
  --microscope "Microscope 1"
```

##### Example channel_map.csv

fov,timepoint,channel,filepath
fov01,0,ch1,data/fov01_t000_ch1.tif
fov01,0,ch2,data/fov01_t000_ch2.tif
...


### Jupyter Notebooks (optional)

Jupyter notebook for interactive use:

registration_notbook.ipynb



## 4. Check quality of alignment   

- Visual inspection is essential (use overlays of aligned vs original images).
- Additionally, SSIM (Structural Similarity Index) or correlation metrics can help evaluate alignment.
📓 Notebook under development: notebooks/check_alignment_quality.ipynb

✅ Todo: Add before/after SSIM plots and batch summaries.


##  Requirements

- Python 3.7+
- numpy
- tifffile
- scikit-image
- pandas

Install dependencies:

```bash
pip install -r requirements.txt
```


## Authors

Laura Breimann

### Code and data for [Geometrical Levels of Detail for Indoor Daylight Simulation]()

![alt text](<Figures/graphical abstract.jpg>)


### Folder structure

- `code`:
  - `jobs`: *example cluster job scripts*.
  - `postprocess`: *post-processing scripts for analysis and visualization*
  - `src`: main source codes for daylight simulations, defining rooms with varying MCOA and GLOD
- `Figures`: figures and plots for both vizualisation and data analysis in the paper.
- `inputs`: *json geometries, simulation grids, and weather files for rooms 1 and 2*: **, *D2(S10)*, *D3(S11)*, and test scenes *S1(S01)*, *S2(S02)*, *S3(S04)*, *T1(S07)*, *T2(S08)*, *T3(S09)**


---
### Solid angle calculation
### Normalized Solid Angle (NSA)

The Normalized Solid Angle (NSA) is calculated as:

$`NSA = \frac{Ω}{A_w}`$

where:

- $`Ω`$ — cumulative apparent solid angle subtended by the window mesh triangles from the centroid of the non-permanent object, counted only when the line between the object's centroid and a triangle's centroid is unobstructed by other objects in the room (steradians).
- $`A_w`$ — total window area in the room (m²).

The implementation is in `input_station.py`, function `calculate_solid_angle()`.`Threshods` class 


This includes a visibility check.  For example, if from the centroid of the red flower box (<span style="color:red">x</span>). the first conjunction point (<span style="color:green">x</span>)  on the connecting line to the windows (<span style="color:yellow">—</span>) is on the window pane(🟦), then the solid angle of that triangle is added to the total solid angle of the window as seen from the centroid of the flower box.

<img src="Figures/65_page-0001.jpg" alt="Page 65" style="width:50%; height:auto;" />


---
### Cubic sensor grids and cubic quantities

`this class` creates cubic sensor definitions from a given list of points (as a simple .txt).

The cubic grid is defined in 


The cubic illuminance is calculated in ...?



---

### About the Daylight simulation engine
This respository uses an advance 2-phase annual daylight simulation method based on Radiance v5.4.

[![Radiance 5.4](https://img.shields.io/github/v/release/LBNL-ETA/Radiance?style=flat-square)](https://github.com/LBNL-ETA/Radiance/tree/rad5R4)
---
### Citation
If you use the code/program (or part) of this work, please cite our paper:

```
The manuscript is under review -- 
```

---

### License
This repository uses the [MIT License](https://opensource.org/licenses/MIT). This allows free use, modification, and redistribution with attribution. (see also `./LICENSE`)

---

If you have any questions, comments, or suggestions, please feel free to contact me at:
Forouzandeh.nima@gmail.com; n.forouzandeh@tudelft.nl

November, 2025

Copyright (C) 2025 | Nima Forouzandeh



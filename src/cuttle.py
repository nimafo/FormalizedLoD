import numpy as np
import pandas as pd
import os
""" ln test                 
    Implementation of "Research Note: A practical approach to cubic illuminance measurement" by Christopher Cuttle
    (https://www.researchgate.net/profile/Christopher-Cuttle/publication/274538293_Research_Note_A_practical_approach_to_cubic_illuminance_measurement/links/56a6d84b08ae997e22ba4fc6/Research-Note-A-practical-approach-to-cubic-illuminance-measurement.pdf)
    (also see https://journals.sagepub.com/doi/abs/10.1177/14771535970290010601)
    key features:
    0. generate cubic grid from points.txt file, and write it to a file for Radiance simulation.
    2. computes cubic quantities for each point in the grid.
    
    Attributes:
        - pointstxt_path (str): The file path to the grid file (points.txt). designing the grid, i.e. the location of the points is a separate task, this class only writes the the cuttle grid file for Radiance, and post process the simulation results.
        - result_path (str): path to the simulated cubic csv.gz file.
        - cubic_grid_and_results_dtype (np.dtype): The data type for the cubic grid and simulation results.        
        - rotation_matrix (np.ndarray):
                        
                                   
        
    Methods:
        __init__(self, pointstxt_path, space_angle=0, cubic_grid_write_path=None):
            Initializes the cuttle object with the path to the points file, an optional space angle for grid generation, and an optional path for writing the cubic grid.
            
            Parameters:
                pointstxt_path (str): The file path to the points.txt file. This file should contain the 3D coordinates of points in space, which will be used to generate the cubic grid. WARNING: this needs 
                space_angle (float, optional): The angle in degrees used to define the orientation of the cubic grid in space(to be further developed). Defaults to 0, which means the grid will be aligned with the global coordinate system.
                cubic_grid_write_path (str, optional): The file path where the generated cubic grid should be written for Radiance simulation. If not provided, a default path will be used based on the input file name.
                
        __compute_rotation_matrix(self):
            Computes the rotation matrix based on the space angle provided during initialization.
            
        write_cubic_grid(self):
            Writes the generated cubic grid to a file for Radiance simulation.
        
        __per_point_calculation(simulated_node_array: np.ndarray):
            Calculates the cubic illumination values for each point in the grid based on the simulation results.
            returns:
                illuminance components:
                    E_u: illumination vector component in the u direction
                    E_v: illumination vector component in the v direction
                    E_w: illumination vector component in the w direction
                symmetric illuminance components:
                    m_E_u: symmetric illuminance component in the u direction
                    m_E_v: symmetric illuminance component in the v direction
                    m_E_w: symmetric illuminance component in the w direction
                components of the unit vectors:
                    e_u: unit vector component in the u direction
                    e_v: unit vector component in the v direction
                    e_w: unit vector component in the w direction
                    e_x: unit vector component in the x direction
                    e_y: unit vector component in the y direction
                    e_z: unit vector component in the z direction
                OTHER:
                    abs_E: Illumination vector magnitute
                    Esr: scalar illuminance
                    m_E: symmetric illuminance
                    abs_E_to_Esr: ratio of |E| to Esr
                    Ewp: working plane illuminance, returns 0 if Ewp is nan
                    Ecl: mean cylindrical illuminance, returns 0 if Ecl is nan
                    Ecl_Ewp: ratio of Ecl to Ewp
                    Diffuseness: According to Xie et al.
                Parameters:
                    simulated_node_array (np.ndarray): An array with shape of (6, ) containing the simulated illuminance 
                    values for a single point in the grid (E_u_plus, E_u_minus, E_v_plus, E_v_minus, E_w_plus, E_w_minus).
"""
class cuttle:
    def __init__(self, 
                 pointstxt_path, 
                 space_angle=0, 
                 raw_result_path:str = None,
                 verbose:bool = False):
        time_step_count = 8761
        
        self.pointstxt_path = pointstxt_path
        self.space_angle = space_angle
        self.rotation_matrix = self.__compute_rotation_matrix()
        self.raw_result_path = raw_result_path
        self.verbose = verbose
        self.cubic_grid_and_results_dtype = np.dtype([
            # Grid information
            ('point', np.float64, (3,)),       # (x, y, z) coordinates 
            ('x_plus', np.float64, (3,)),      # x+ (unit vector)
            ('x_minus', np.float64, (3,)),     # x- (unit vector)
            ('y_plus', np.float64, (3,)),      # y+ (unit vector)
            ('y_minus', np.float64, (3,)),     # y- (unit vector)
            ('z_plus', np.float64, (3,)),      # z+ (unit vector)
            ('z_minus', np.float64, (3,)),     # z- (unit vector)
            ('u_plus', np.float64, (3,)),      # u+ (unit vector)
            ('u_minus', np.float64, (3,)),     # u- (unit vector)
            ('v_plus', np.float64, (3,)),      # v+ (unit vector)
            ('v_minus', np.float64, (3,)),     # v- (unit vector)
            ('w_plus', np.float64, (3,)),      # w+ (unit vector)
            ('w_minus', np.float64, (3,)),     # w- (unit vector)
            
            # From simulation outputs  
            # full directional
            ('E_u_plus', np.float64, (time_step_count,)), # illumination vector component in the u+ direction
            ('E_u_minus', np.float64, (time_step_count,)), # illumination vector component in the u- direction
            ('E_v_plus', np.float64, (time_step_count,)), # illumination vector component in the v+ direction
            ('E_v_minus', np.float64, (time_step_count,)), # illumination vector component in the v- direction
            ('E_w_plus', np.float64, (time_step_count,)), # illumination vector component in the w+ direction
            ('E_w_minus', np.float64, (time_step_count,)), # illumination vector component in the w- direction
            
            # Illuminance components       
            ('E_u', np.float64, (time_step_count,)), # illumination vector component in the u direction
            ('E_v', np.float64, (time_step_count,)), # illumination vector component in the v direction
            ('E_w', np.float64, (time_step_count,)), # illumination vector component in the w direction
            
            # Symmetric illuminance components
            ('m_E_u', np.float64, (time_step_count,)), 
            ('m_E_v', np.float64, (time_step_count,)),
            ('m_E_w', np.float64, (time_step_count,)),
            # Vector direction (unit vector)
            ('e_u', np.float64, (time_step_count,)),
            ('e_v', np.float64, (time_step_count,)),
            ('e_w', np.float64, (time_step_count,)),
            ('e_x', np.float64, (time_step_count,)),
            ('e_y', np.float64, (time_step_count,)),
            ('e_z', np.float64, (time_step_count,)),
            # Vector and scalar data
            ('|E|', np.float64, (time_step_count,)),
            ('Esr', np.float64, (time_step_count,)),
            ('m_E', np.float64, (time_step_count,)),
            ('|E|/Esr', np.float64, (time_step_count,)),
            # Horizontal and cylindrical data
            ('Ewp', np.float64, (time_step_count,)),
            ('Ecl', np.float64, (time_step_count,)),
            ('Ecl/Ewp', np.float64, (time_step_count,)),
            ('Diffuseness', np.float64, (time_step_count,)),
        ])
        points = np.loadtxt(self.pointstxt_path, usecols=(0, 1, 2)) # (vectorized reading)
        num_points = points.shape[0]
        
        # Precompute the static unit vectors based on the space_angle
        angle_rad = np.deg2rad(self.space_angle)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        self.x_plus = np.array([cos_angle, sin_angle, 0])
        self.x_minus = -self.x_plus
        self.y_plus = np.array([-sin_angle, cos_angle, 0])
        self.y_minus = -self.y_plus
        self.z_plus = np.array([0, 0, 1])
        self.z_minus = -self.z_plus
        self.u_plus = self.rotation_matrix @ self.x_plus
        self.u_minus = self.rotation_matrix @ self.x_minus
        self.v_plus = self.rotation_matrix @ self.y_plus
        self.v_minus = self.rotation_matrix @ self.y_minus
        self.w_plus = self.rotation_matrix @ self.z_plus
        self.w_minus = self.rotation_matrix @ self.z_minus

        
        # Create a structured array for all points with grid information
        self.cubic_grid_array = np.empty(num_points, dtype=self.cubic_grid_and_results_dtype)
        self.cubic_grid_array['point'] = points
        self.cubic_grid_array['x_plus'] = self.x_plus  # broadcast to all rows
        self.cubic_grid_array['x_minus'] = self.x_minus
        self.cubic_grid_array['y_plus'] = self.y_plus
        self.cubic_grid_array['y_minus'] = self.y_minus
        self.cubic_grid_array['z_plus'] = self.z_plus
        self.cubic_grid_array['z_minus'] = self.z_minus
        self.cubic_grid_array['u_plus'] = self.u_plus
        self.cubic_grid_array['u_minus'] = self.u_minus
        self.cubic_grid_array['v_plus'] = self.v_plus
        self.cubic_grid_array['v_minus'] = self.v_minus
        self.cubic_grid_array['w_plus'] = self.w_plus
        self.cubic_grid_array['w_minus'] = self.w_minus
        for field in ['E_u_plus', 'E_u_minus', 'E_v_plus', 'E_v_minus', 'E_w_plus', 'E_w_minus',
                      'E_u', 'E_v', 'E_w', 
                      'm_E_u', 'm_E_v', 'm_E_w',
                      'e_u', 'e_v', 'e_w', 'e_x', 'e_y', 'e_z',
                      '|E|', 'Esr', 'm_E', '|E|/Esr', 'Ewp', 'Ecl', 'Ecl/Ewp', 'Diffuseness']:
            self.cubic_grid_array[field].fill(np.nan)
        
        if self.raw_result_path:
            self.__compute_cubic_quantities()
    def __compute_rotation_matrix(self):
        theta = -np.pi / 4
        phi = np.arctan(np.sqrt(2))

        R_y = np.array([
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-np.sin(theta), 0, np.cos(theta)]
        ])
        
        R_x = np.array([
            [1, 0, 0],
            [0, np.cos(phi), -np.sin(phi)],
            [0, np.sin(phi), np.cos(phi)]
        ])
        
        return R_x @ R_y

    def write_cubic_grid(self, cubic_grid_write_path=None):
        if cubic_grid_write_path:
            self.cubic_grid_write_path = cubic_grid_write_path
        else:
            base, ext = os.path.splitext(self.pointstxt_path)
            self.cubic_grid_write_path = f"{base}_cubic_spaceAngle3D{self.space_angle}{ext}"

        with open(self.cubic_grid_write_path, 'w') as f: # vectorized writing
            for i in self.cubic_grid_array:
                x, y, z = i['point']
                for vec in [i['u_plus'], i['u_minus'], i['v_plus'], i['v_minus'], i['w_plus'], i['w_minus']]:
                    f.write(f"{x} {y} {z} {vec[0]} {vec[1]} {vec[2]}\n")
        print(rf"the grid is written to file with path:{self.cubic_grid_write_path}")

    def __compute_cubic_quantities(self):
        '''it should implement the __per_point_calculation function from the raw result file'''
        raw_result_array = np.asarray(pd.read_csv(self.raw_result_path, compression='gzip', header=None))
        # !!!apply a temporal multiplier vector to the raw result array.
        
        # check if the number of points in the grid file matches the number of points in the result file
        result_point_count = raw_result_array.shape[1] // 6
        cubic_grid_point_count = self.cubic_grid_array.shape[0]
        if result_point_count != cubic_grid_point_count: 
            raise ValueError(f"The number of points in the grid file ({cubic_grid_point_count}) does not match the number of points in the result file ({result_point_count}).")

        time_steps = raw_result_array.shape[0]

        # Reshape results to (time_steps, num_points, 6)
        sim_results = raw_result_array.reshape(time_steps, result_point_count, 6)

        # Separate the components (each has shape (time_steps, num_points))
        E_u_plus = sim_results[:, :, 0]
        E_u_minus = sim_results[:, :, 1]
        E_v_plus = sim_results[:, :, 2]
        E_v_minus = sim_results[:, :, 3]
        E_w_plus = sim_results[:, :, 4]
        E_w_minus = sim_results[:, :, 5]

        # Calculate vector components
        E_u = E_u_plus - E_u_minus
        E_v = E_v_plus - E_v_minus
        E_w = E_w_plus - E_w_minus
        abs_E = np.sqrt(E_u**2 + E_v**2 + E_w**2)
        m_E_u = (E_u_plus + E_u_minus - np.abs(E_u)) / 2
        m_E_v = (E_v_plus + E_v_minus - np.abs(E_v)) / 2
        m_E_w = (E_w_plus + E_w_minus - np.abs(E_w)) / 2
        m_E = (m_E_u + m_E_v + m_E_w) / 3
        Esr = m_E + abs_E / 4
        
        # From Xie et al. 2016 https://journals.sagepub.com/doi/10.1177/1477153516631392
        
        Diffuseness = 1 - (abs_E/Esr)/4

        # Compute unit vectors, avoiding division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            e_u = np.where(abs_E != 0, E_u / abs_E, np.nan)
            e_v = np.where(abs_E != 0, E_v / abs_E, np.nan)
            e_w = np.where(abs_E != 0, E_w / abs_E, np.nan)
        e_x = 0.707 * (e_v - e_w)
        e_y = 0.816 * e_u - 0.408 * (e_v + e_w)
        e_z = 0.577 * (e_u + e_v + e_w)

        # Horizontal working plane illuminance
        Ewp = np.where(e_z < 0, m_E, abs_E * e_z + m_E)

        # Mean cylindrical illuminance; avoid division by zero later
        Ecl = (abs_E * np.sqrt(e_x**2 + e_y**2) / np.pi) + m_E
        Ecl = np.where(np.isnan(Ecl), 0, Ecl)
        abs_E_to_Esr = np.where((Esr != 0) & (~np.isnan(Esr)), abs_E / Esr, np.nan)
        Ecl_Ewp = np.where((Ewp != 0) & (~np.isnan(Ewp)), Ecl / Ewp, np.nan)

        # assign the computed time series for each point into the structured array
        for field, data in zip(['E_u_plus', 'E_u_minus', 'E_v_plus', 'E_v_minus', 'E_w_plus', 'E_w_minus',
                                'E_u', 'E_v', 'E_w',
                                'm_E_u', 'm_E_v', 'm_E_w',
                                'e_u', 'e_v', 'e_w', 'e_x', 'e_y', 'e_z',
                                '|E|', 'Esr', 'm_E', '|E|/Esr', 'Ewp', 'Ecl', 'Ecl/Ewp', 'Diffuseness'
                                ],
                                 [E_u_plus, E_u_minus, E_v_plus, E_v_minus, E_w_plus, E_w_minus,
                                  E_u, E_v, E_w,
                                  m_E_u, m_E_v, m_E_w,
                                  e_u, e_v, e_w, e_x, e_y, e_z,
                                  abs_E, Esr, m_E, abs_E_to_Esr, Ewp, Ecl, Ecl_Ewp, Diffuseness
                                  ]):
            # data has shape (time_steps, num_points), transpose to match (num_points, time_steps)
            self.cubic_grid_array[field] = data.T
        if self.cubic_grid_array.size == 0:
            raise ValueError("The cubic grid array is empty. No calculations were performed.")
        return self.cubic_grid_array  # the shape should be (pointCount,) with each field having time_step_count entries

def make_cubic_head_poses_from_work_plane(path:str):
    '''
        Makes cubic grid from workplane points, these represent headposes from 120-220 cm height with 20 cm increment.

        assumes:
        - workplane point are in the same height. 
        - the directions are all 0 0 1.
    '''
    # read the txt file, it is formatted as -1.750383 -2.40181 0.259722 0 0 1 (x y z dx dy dz).
    array = np.loadtxt(path)
    print(rf"there are {len(array)} points in the workplane file")
    # base height is a workplane height, it is single value.
    base_height= array[0,2]
    
    # make array +40cm, +60cm, +80cm, +100cm, +120cm, +140cm
    array_1 = array.copy()
    array_1[:,2] = base_height + 0.40
    array_2 = array.copy()
    array_2[:,2] = base_height + 0.60
    array_3 = array.copy()
    array_3[:,2] = base_height + 0.80
    array_4 = array.copy()
    array_4[:,2] = base_height + 1.00
    array_5 = array.copy()
    array_5[:,2] = base_height + 1.20
    array_6 = array.copy()
    array_6[:,2] = base_height + 1.40

    # now merge the array , array_1, array_2, array_3, array_4, array_5, array_6
    array = np.vstack((array_1, array_2))
    array = np.vstack((array, array_3))
    array = np.vstack((array, array_4))
    array = np.vstack((array, array_5))
    array = np.vstack((array, array_6))

    # export the array to a text file in the same directory with the name "cubic_locations.txt"
    parent = os.path.dirname(path)
    with open (os.path.join(parent, "cubic_locations.txt"), 'w') as f:
        for i in range(array.shape[0]):
            f.write(f"{array[i,0]} {array[i,1]} {array[i,2]} {array[i,3]} {array[i,4]} {array[i,5]}\n")
    print(f"cubic_locations.txt is saved in {parent} -- there are {len(array)} points in it.")
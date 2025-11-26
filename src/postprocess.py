# uncompyle6 version 3.9.2
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.9.22 | packaged by conda-forge | (main, Apr 14 2025, 23:35:59) 
# [GCC 13.3.0]
# Embedded file name: /home/nforouzandehsh/RQ2_performance_evaluation/process/postprocess.py
# Compiled at: 2025-05-06 11:54:15
# Size of source mod 2**32: 27404 bytes --
if __name__ == "__main__":
    pass
import numpy as np, os, datetime
import matplotlib.pyplot as plt
import scipy.stats as stats
import pandas as pd, cuttle
import plotly.graph_objects as go
import trimesh
from matplotlib.collections import PolyCollection
from scipy.interpolate import griddata
from matplotlib.lines import Line2D

class workplane:
    def __init__(self,
                 path_to_results,
                 grid,
                 to_simulate,
                 udi_legend_range=(0, 30),
                 tai_legend_range=(0, 0.4),
                 timestep_count: int = None,
                 compression='gzip',
                 save_string=None,
                 plot_grid_points:bool=False):
        """
        path_to_results : .ill.csv.gz
        grid: str, path to the grid file
        """
        self.timestep_count = timestep_count # it is useful when using ill file from honeybee with only sun-up-hours.txt
        # number of timesteps for udi calculation
        self.to_simulate = to_simulate
        self.udi_legend_range = udi_legend_range
        self.tai_legend_range = tai_legend_range
        self.save_string = save_string
        if compression:
            self.df_results = pd.read_csv(path_to_results, compression=compression)
        else:
            self.df_results = pd.read_csv(path_to_results, sep='\t', header=None)
            # if the last column == "" then drop it
            if pd.isna(self.df_results.iloc[-1].to_list()[-1]):
                print(f"shape of df_results before cleaning: {self.df_results.shape}")
                self.df_results = self.df_results.iloc[:, :-1]
                print(f"shape of df_results after cleaning: {self.df_results.shape}")
        
        self.grid = pd.read_csv(grid, header=None, sep=' ')
        print(f"shape of df_results: {self.df_results.shape}")
        print(f"shape of grid: {self.grid.shape}")
        
        self.tai = self.__tai(self.df_results)
        self.udi_under, self.udi, self.udi_over = self.__udi(self.df_results)
        # print(f"udi under: {np.mean(self.udi_under):.2f}%, udi: {np.mean(self.udi):.2f}%, udi over: {np.mean(self.udi_over):.2f}%")
        self.plot_grid_points = plot_grid_points
        # print udi values
        

    def plot_single_point_illuminance(self,  # for comparative time stap plot.
                                      second_ill_file_path: str = None,
                                      point_index: int = 0,
                                      day_of_year: int = 80):
        '''
        Plots the illuminance values for a single point index for the 24 hours of the specified day.
        Also plots the point location in the room in red.

        Parameters:
        - point_index: Index of the grid point to plot.
        - day_of_year: Day of year to plot (default: 80, spring equinox).
        '''
        # Plot for the first 1/12th of the data (first month)
        num_rows = self.df_results.shape[0]
        num_days = num_rows // 24
        days_in_month = num_days // 12
        start_idx = 0
        end_idx = days_in_month * 24

        print("shape of the self.df_results: ", self.df_results.shape)
        if point_index >= self.df_results.shape[1]:
            raise ValueError(f"Requested point_index {point_index} exceeds available data columns.")

        illuminance_values = self.df_results.iloc[start_idx:end_idx, point_index].values
        hours = np.arange(illuminance_values.shape[0])

        plt.figure(figsize=(10, 5))
        plt.plot(hours, illuminance_values, marker='o', label='Illuminance (First Month)')
        plt.xlabel('Hour')
        plt.ylabel('Illuminance (lux)')
        plt.title(f'Illuminance at Point {point_index} for First Month')
        plt.grid()
        plt.legend()
        plt.show()

        # Plot the point location in the room in red
        all_mesh = [self.to_simulate[key]["mesh"] for key in self.to_simulate]
        all_mesh = trimesh.util.concatenate(all_mesh)
        xy = all_mesh.vertices[:, :2]
        faces = all_mesh.faces

        point_location = self.grid.iloc[point_index, :2].values

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.triplot(xy[:, 0], xy[:, 1], faces, color='lightgray', alpha=0.5)
        ax.scatter(point_location[0], point_location[1], c='red', s=100, label='Point Location')
        ax.set_aspect('equal', 'box')
        ax.legend()
        plt.title(f'Point Location in Room (Index {point_index})')
        plt.show()

    def plot_TAI(self,  
                 tai = None,
                 interpolate:bool=True):
        """
        Plot the spatial map, i.e. TAI for each point --
        add room obj objects. from top view.
        """
        
        X = self.grid.iloc[:, 0]
        Y = self.grid.iloc[:, 1]
        if tai is None:
            tai = self.tai
        
        # print shape of X, Y, tai
        print(f"X shape: {X.shape}, Y shape: {Y.shape}, tai shape: {tai.shape}")
        # if the shape of tai is not the same as X and Y, calculate the tai again with inverse axes
        if tai.shape[0] != X.shape[0]:
            print("Recalculating TAI...")
            self.tai = self.__tai(self.df_results.T)
            tai = self.tai
            print(f"New tai shape: {tai.shape}")
        plt.rcParams["font.family"] = "Times New Roman"
        fig, ax = plt.subplots(1, 1, figsize=(10, 5), dpi=150)
        all_mesh = [self.to_simulate[key]["mesh"] for key in self.to_simulate]
        all_mesh = trimesh.util.concatenate(all_mesh)
        xy = all_mesh.vertices[:, :2]
        faces = all_mesh.faces
        triangles = xy[faces]
        polygons = PolyCollection(triangles,
          alpha=0.05,
          edgecolor="k",
          facecolor="gray",
          linewidth=0.05)
        ax.add_collection(polygons)
        minX_mesh = np.min(xy[:, 0])
        maxX_mesh = np.max(xy[:, 0])
        minY_mesh = np.min(xy[:, 1])
        maxY_mesh = np.max(xy[:, 1])
        
        if interpolate:
            xi = np.linspace(X.min(), X.max(), 300)
            yi = np.linspace(Y.min(), Y.max(), 300)
            xi, yi = np.meshgrid(xi, yi)
            zi = griddata((X, Y), tai, (xi, yi), method="cubic")
            ax.set_aspect("equal", "box")
            ax.set_frame_on(False)
            cmap = plt.get_cmap("RdYlBu_r")
            
            im = ax.imshow(zi, 
                           extent=[minX_mesh, maxX_mesh, minY_mesh, maxY_mesh], 
                           origin="lower",
                           cmap=cmap,
                           aspect="equal",
                           alpha=0.5, 
                           vmin=self.tai_legend_range[0], 
                           vmax = self.tai_legend_range[1])
            
        else:
            # scatter plot, x is X, y is Y, Z is illuminance
            im = ax.scatter(X, 
                            Y, 
                            c=tai, 
                            cmap="RdYlBu_r", 
                            s=10, 
                            vmin=self.tai_legend_range[0], 
                            vmax = self.tai_legend_range[1])
            ax.set_aspect("equal", "box")
        
        if self.plot_grid_points:
            ax.scatter(X, Y, c="black", s=1,  vmin=self.tai_legend_range[0], vmax = self.tai_legend_range[1])
        ax.text((-0.1), 0.5, f"Mean TAI = {self.tai.mean():.2f} [klx.h/year]", fontsize=8,
          ha="center",
          va="center",
          rotation=90,
          transform=(ax.transAxes))
        ax.set_xticks([])
        ax.set_yticks([])
        cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.012, pad=0.04, shrink=0.6)
        cbar.set_label("TAI[klx.h/year]")
        if self.save_string:
            plt.savefig(f"UDI_TAI_{self.save_string}.pdf", dpi=300, bbox_inches="tight")
        else:
            plt.show()
            
    def plot_UDI(self, range:str="well-lit"):
        """
        Plot the spatial map, i.e. UDI for each point.
        add room obj objects. from top view,
        """
        if range not in ["well-lit", "over-lit", "under-lit"]:
            raise ValueError("range should be one of ['well-lit', 'over-lit', 'under-lit']")
        X = self.grid.iloc[:, 0]
        Y = self.grid.iloc[:, 1]
        if range == "well-lit":
            udi = self.udi
        elif range == "over-lit":
            udi = self.udi_over
        elif range == "under-lit":
            udi = self.udi_under
        plt.rcParams["font.family"] = "Times New Roman"
        fig, ax = plt.subplots(1, 1, figsize=(10, 5), dpi=150)
        all_mesh = [self.to_simulate[key]["mesh"] for key in self.to_simulate]
        all_mesh = trimesh.util.concatenate(all_mesh)
        xy = all_mesh.vertices[:, :2]
        faces = all_mesh.faces
        triangles = xy[faces]
        polygons = PolyCollection(triangles,
          alpha=0.05,
          edgecolor="k",
          facecolor="gray",
          linewidth=0.05)
        ax.add_collection(polygons)
        minX_mesh = np.min(xy[:, 0])
        maxX_mesh = np.max(xy[:, 0])
        minY_mesh = np.min(xy[:, 1])
        maxY_mesh = np.max(xy[:, 1])
        norm = plt.Normalize(vmin=(self.udi_legend_range[0]), vmax=(self.udi_legend_range[1]))
        xi = np.linspace(X.min(), X.max(), 300)
        yi = np.linspace(Y.min(), Y.max(), 300)
        xi, yi = np.meshgrid(xi, yi)
        zi = griddata((X, Y), udi, (xi, yi), method="cubic")
        ax.set_aspect("equal", "box")
        ax.set_frame_on(False)
        cmap = plt.get_cmap("OrRd")
        im = ax.imshow(zi, extent=[minX_mesh, maxX_mesh, minY_mesh, maxY_mesh], origin="lower",
          cmap=cmap,
          aspect="equal",
          alpha=0.5,
          norm=norm)
        if self.plot_grid_points:
            ax.scatter(X, Y, c="black", s=1)
        ax.text((-0.1), 0.5, f"TAI_{{mean}} = {self.tai.mean():.2f} [klx.hrs/year]", fontsize=8,
          ha="center",
          va="center",
          rotation=90,
          transform=(ax.transAxes))
        ax.set_xticks([])
        ax.set_yticks([])
        cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.012, pad=0.04, shrink=0.6)
        if range == "well-lit":
            cbar.set_label("UDI[well-lit %]")
        elif range == "over-lit":
            cbar.set_label("UDI[over-lit %]")
        elif range == "under-lit":
            cbar.set_label("UDI[under-lit %]")
        if self.save_string:
            plt.savefig(f"UDI_TAI_{self.save_string}.pdf", dpi=300, bbox_inches="tight")
        else:
            plt.show()
        print(f"averge UDI: {np.array(udi).mean():.2f}%")

    def plot_time_step(self, time_step:int=12, interpolate:bool=False):
        '''plots the timestep illuminance values for each point in the grid.'''

        X = self.grid.iloc[:, 0]
        Y = self.grid.iloc[:, 1]
        Z = self.df_results.iloc[time_step, :].values
        X.shape, Y.shape, Z.shape
        v_max = Z.max()

        plt.rcParams["font.family"] = "Times New Roman"
        if self.tai.shape[0] != X.shape[0]:
            print("Recalculating TAI...")
            self.tai = self.__tai(self.df_results.T)
            tai = self.tai
            print(f"New tai shape: {tai.shape}")
        fig, ax = plt.subplots(1, 1, figsize=(10, 5), dpi=150)
        all_mesh = [self.to_simulate[key]["mesh"] for key in self.to_simulate]
        all_mesh = trimesh.util.concatenate(all_mesh)
        xy = all_mesh.vertices[:, :2]
        faces = all_mesh.faces
        triangles = xy[faces]
        polygons = PolyCollection(triangles,
            alpha=0.05,
            edgecolor="k",
            facecolor="gray",
            linewidth=0.05)
        ax.add_collection(polygons)
        minX_mesh = np.min(xy[:, 0])
        maxX_mesh = np.max(xy[:, 0])
        minY_mesh = np.min(xy[:, 1])
        maxY_mesh = np.max(xy[:, 1])
        norm = plt.Normalize(vmin=0, vmax=v_max)
        if interpolate:
            xi = np.linspace(X.min(), X.max(), 300)
            yi = np.linspace(Y.min(), Y.max(), 300)
            xi, yi = np.meshgrid(xi, yi)
            zi = griddata((X, Y), Z, (xi, yi), method="cubic") # X is
            ax.set_aspect("equal", "box")
            ax.set_frame_on(False)
            cmap = plt.get_cmap("Reds")
            im = ax.imshow(zi, extent=[minX_mesh, maxX_mesh, minY_mesh, maxY_mesh], origin="lower",
                cmap=cmap,
                aspect="equal",
                alpha=0.5
                ,norm=norm)
        else:
            # scatter plot, x is X, y is Y, Z is illuminance
            im = ax.scatter(X, Y, c=Z, cmap="RdYlBu_r", s=10, norm=norm)
            ax.set_aspect("equal", "box")

        ax.text((-0.1), 0.5, f"Illuminance_{{mean}} = {Z.mean():.2f} [lx]", fontsize=8,
            ha="center",
            va="center",
            rotation=90,
            transform=(ax.transAxes))
        ax.set_xticks([])
        ax.set_yticks([])
        cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.012, pad=0.04, shrink=0.6)
        cbar.set_label("Illuminance[lx]")
        plt.show()

    def plot_value(self, value=None):
        '''plots single values per point, e.g. RMSE'''
        X = self.grid.iloc[:, 0]
        Y = self.grid.iloc[:, 1]
        if value is None:
            value = self.df_results.drop(columns=['Unnamed: 0'])
        plt.rcParams["font.family"] = "Times New Roman"
        fig, ax = plt.subplots(1, 1, figsize=(10, 5), dpi=150)
        all_mesh = [self.to_simulate[key]["mesh"] for key in self.to_simulate]
        all_mesh = trimesh.util.concatenate(all_mesh)
        xy = all_mesh.vertices[:, :2]
        faces = all_mesh.faces
        triangles = xy[faces]
        polygons = PolyCollection(triangles,
          alpha=0.05,
          edgecolor="k",
          facecolor="gray",
          linewidth=0.05)
        ax.add_collection(polygons)
        minX_mesh = np.min(xy[:, 0])
        maxX_mesh = np.max(xy[:, 0])
        minY_mesh = np.min(xy[:, 1])
        maxY_mesh = np.max(xy[:, 1])
        norm = plt.Normalize(vmin=0, vmax=3000)
        xi = np.linspace(X.min(), X.max(), 300)
        yi = np.linspace(Y.min(), Y.max(), 300)
        xi, yi = np.meshgrid(xi, yi)
        zi = griddata((X, Y), value, (xi, yi), method="cubic")
        ax.set_aspect("equal", "box")
        ax.set_frame_on(False)
        cmap = plt.get_cmap("Reds")
        im = ax.imshow(zi, extent=[minX_mesh, maxX_mesh, minY_mesh, maxY_mesh], origin="lower",
          cmap=cmap,
          aspect="equal",
          alpha=0.5
           ,norm=norm)
        if self.plot_grid_points:
            ax.scatter(X, Y, c="black", s=1)
        ax.text((-0.1), 0.5, f"RMSE_{{mean}} = {value.mean()[0]:.2f} [lx.hrs]", fontsize=8,
          ha="center",
          va="center",
          rotation=90,
          transform=(ax.transAxes))
        ax.set_xticks([])
        ax.set_yticks([])
        cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.012, pad=0.04, shrink=0.6)
        cbar.set_label("RMSE[lx]")
        if self.save_string:
            plt.savefig(f"_{self.save_string}.pdf", dpi=300, bbox_inches="tight")
        else:
            plt.show()

    def __udi(self, data):
        """UDI function, outputs the UDI for each node in the grid as a list"""
        data_np = data.to_numpy()
        
        if self.timestep_count is not None:
            print('number of sensors for udi calculation:', self.timestep_count)
            timestep_count = self.timestep_count
        else:
            print(rf"number of sensors for udi calculation: {data_np.shape[0]}")
            timestep_count = data_np.shape[0]
        
        udi_300 = np.sum((data_np < 300), axis=0) / timestep_count * 100
        udi_300_3000 = np.sum(((data_np >= 300) & (data_np < 3000)), axis=0) / timestep_count * 100
        udi_above_3000 = np.sum((data_np >= 3000), axis=0) / timestep_count * 100
        return (udi_300.tolist(), udi_300_3000.tolist(), udi_above_3000.tolist())

    def __tai(self, data):
        """TAI function, outputs the TAI for each node in the grid as a list klx.h/year"""
        data_np = data.to_numpy()
        tai_ = np.nansum(data_np, axis=0) / (1000) / data_np.shape[0]
        return tai_

class head_pose:
    '''
    visualize/summarize cuttle results.
    cuttle.py object as input.
    1. Single direction, single point location.
        - TAI_|E| = (1 / (1000 * G)) * sum(sum(|E|_ij)) : this sums all the |E| values for all the points and all the timesteps.
        - data type: single np.float64 value.
    2. All direction, single point location.
        - data tipe: dict with keys 'u', 'v', 'w' and values the TAI for each direction.
    3. Single direction, all point locations.
        -  data type: np.array with shape (num_points, 1)
    4. Keep direction, all point locations.
        - data type: np.array with shape (num_points, 3)"

    - !!! under constrction -- temporal_multiplier: vector of 8761 booleans
                                   to apply temporal filters, e.g. occupancy or weather.
                                   should either remove the corresponding timestep values or
                                   set them to -999, or set them to 0. by default is 1 for all timesteps.                   
    '''
    
    def __init__(self, 
                 results, 
                 grid, 
                 path_to_geometry_folder,
                 temporal_multiplier:np.ndarray = np.ones(8761)
                 ):
        """
        grid : str, path to the grid        
        path_to_geometry_folder: str, path to the folder containing the .obj files, Shouldn't this be for both geometries? 
        """
        self.grid_path = grid
        self.grid = pd.read_csv((self.grid_path), header=None, sep=" ")
        self.result_path = results
        self.df = pd.read_csv(results)
        self.path_to_geometry_folder = path_to_geometry_folder
        self.temporal_multiplier = temporal_multiplier
        self.cu = cuttle.cuttle(pointstxt_path=(self.grid_path), 
                                raw_result_path=(self.result_path))
        self.G = np.loadtxt((self.cu.pointstxt_path), usecols=(0, 1, 2)).shape[0]
        self.single_direction_single_point_location()
        
    def single_direction_single_point_location(self):
        """
        TAI = sqrt(TAI_Eu^2 + TAI_Ev^2 + TAI_Ew^2)
        
        TAI_Eu = (1 / (1000 * G)) * sum(sum((E_u)_ij))
        TAI_Ev = (1 / (1000 * G)) * sum(sum((E_v)_ij))
        TAI_Ew = (1 / (1000 * G)) * sum(sum((E_w)_ij))

        Where:
        - (Eu)_ij: illumination vector component at point i, timestep j, in the u direction.
        - (Ev)_ij: illumination vector component at point i, timestep j, in the v direction.
        - (Ew)_ij: illumination vector component at point i, timestep j, in the w direction.
        - G: The number of grid points.
        - H: The number of time steps.
        """
        TAI_Eu = np.round(1 / (1000 * self.G) * np.sum(self.cu.cubic_grid_array["E_u"]), 2)
        TAI_Ev = np.round(1 / (1000 * self.G) * np.sum(self.cu.cubic_grid_array["E_v"]), 2)
        TAI_Ew = np.round(1 / (1000 * self.G) * np.sum(self.cu.cubic_grid_array["E_w"]), 2)
        TAI = np.sqrt(np.power(TAI_Eu, 2) + np.power(TAI_Ev, 2) + np.power(TAI_Ew, 2))
        return TAI
    def all_directions_single_point_location(self):
        """        
        TAI_Eu = (1 / (1000 * G)) * sum(sum((E_u)_ij))
        TAI_Ev = (1 / (1000 * G)) * sum(sum((E_v)_ij))
        TAI_Ew = (1 / (1000 * G)) * sum(sum((E_w)_ij))
        
        Where:
        - (Eu)_ij: illumination vector component at point i, timestep j, in the u direction.
        - (Ev)_ij: illumination vector component at point i, timestep j, in the v direction.
        - (Ew)_ij: illumination vector component at point i, timestep j, in the w direction.
        - G: The number of grid points.
        - H: The number of time steps.
        """
        TAI_Eu = np.round(1 / (1000 * self.G) * np.sum(self.cu.cubic_grid_array["E_u"]), 2)
        TAI_Ev = np.round(1 / (1000 * self.G) * np.sum(self.cu.cubic_grid_array["E_v"]), 2)
        TAI_Ew = np.round(1 / (1000 * self.G) * np.sum(self.cu.cubic_grid_array["E_w"]), 2)
        return {'u':TAI_Eu,  'v':TAI_Ev,  'w':TAI_Ew}
    def single_direction_all_point_locations(self):
        """
        this will be a vizual comparison,
        a vizualiser plots all the point locations
        """
        points = np.asarray(self.grid.iloc[:,:3])
        colormap = "YlOrBr_r"
        tai_E_i = np.round(0.001 * np.sum((self.cu.cubic_grid_array["|E|"]), axis=1))
        fig = go.Figure()
        fig.add_trace(go.Scatter3d(x=(points[:, 0]),
          y=(points[:, 1]),
          z=(points[:, 2]),
          mode="markers",
          marker=dict(size=2,
          color=tai_E_i,
          colorscale=colormap,
          colorbar=dict(title="TAI<sub>|E|,i</sub>[klx]"),
          opacity=0.8)))
        for filename in os.listdir(self.path_to_geometry_folder):
            if filename.endswith(".obj"):
                file_path = os.path.join(self.path_to_geometry_folder, filename)
                mesh = trimesh.load(file_path)
                vertices = mesh.vertices
                faces = mesh.faces
                fig.add_trace(go.Mesh3d(x=(vertices[:, 0]),
                  y=(vertices[:, 1]),
                  z=(vertices[:, 2]),
                  i=(faces[:, 0]),
                  j=(faces[:, 1]),
                  k=(faces[:, 2]),
                  color="lightgrey",
                  opacity=0.2,
                  name=f"wireframe_{filename}",
                  showlegend=False,
                  lighting=dict(ambient=0.5),
                  flatshading=True))

        tai_Eu_i = np.round(0.001 * np.sum((self.cu.cubic_grid_array["E_u"]), axis=1))
        tai_Ev_i = np.round(0.001 * np.sum((self.cu.cubic_grid_array["E_v"]), axis=1))
        tai_Ew_i = np.round(0.001 * np.sum((self.cu.cubic_grid_array["E_w"]), axis=1))
        tai_E_i = np.round(np.sqrt(np.power(tai_Eu_i, 2) + np.power(tai_Ev_i, 2) + np.power(tai_Ew_i, 2)), 2)
        direction = np.array([tai_Eu_i / tai_E_i, tai_Ev_i / tai_E_i, tai_Ew_i / tai_E_i]).T
        vector_length = 0.4
        arrow_tips = points + direction * vector_length
        for i in range(len(points)):
            fig.add_trace(go.Scatter3d(x=[
             points[(i, 0)], arrow_tips[(i, 0)]],
              y=[
             points[(i, 1)], arrow_tips[(i, 1)]],
              z=[
             points[(i, 2)], arrow_tips[(i, 2)]],
              mode="lines",
              line=dict(color=tai_E_i, width=2),
              showlegend=False))

        fig.update_layout(title="-",
          scene=dict(xaxis_title="X",
          yaxis_title="Y",
          zaxis_title="Z"),
          margin=dict(l=0, r=0, b=0, t=40))
        fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)
        fig.show()
    def all_directions_all_point_locations(self):
        '''only reduces the temporal dimension. tai_Eu_plus is summation of all the'''
        
        '''
        1. No multiplier, all timesteps
        2. overcast multiplier
        3. clear sky multiplier
        
        for each: 
        - double check the number of timesteps in TAI
        - plot the results + quartiles


        '''
        
        print(f"shape of multiplier: {self.temporal_multiplier.sum()}")
        
        # apply temporal multiplier here
        # if the temporal multiplier is 0, pop the corresponding timestep values out, so I can verify the number of timesteps.
        tai_Eu_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_u_plus'] * self.temporal_multiplier, axis=1) / self.temporal_multiplier.sum()
        tai_Ev_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_v_plus'] * self.temporal_multiplier, axis=1) / self.temporal_multiplier.sum()
        tai_Ew_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_w_plus'] * self.temporal_multiplier, axis=1) / self.temporal_multiplier.sum()
        tai_Eu_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_u_minus'] * self.temporal_multiplier, axis=1) / self.temporal_multiplier.sum()
        tai_Ev_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_v_minus'] * self.temporal_multiplier, axis=1) / self.temporal_multiplier.sum()
        tai_Ew_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_w_minus'] * self.temporal_multiplier, axis=1) / self.temporal_multiplier.sum()
        
        
        
        
        # tai_Eu_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_u_plus']* self.temporal_multiplier, axis = 1)
        # tai_Ev_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_v_plus']* self.temporal_multiplier, axis = 1)
        # tai_Ew_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_w_plus']* self.temporal_multiplier, axis = 1)
        # tai_Eu_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_u_minus']* self.temporal_multiplier, axis = 1)
        # tai_Ev_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_v_minus']* self.temporal_multiplier, axis = 1)
        # tai_Ew_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_w_minus']* self.temporal_multiplier, axis = 1)
        # tai_Eu_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_u_plus'], axis = 1)
        # tai_Ev_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_v_plus'], axis = 1)
        # tai_Ew_plus = 0.001 * np.sum(self.cu.cubic_grid_array['E_w_plus'], axis = 1)
        # tai_Eu_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_u_minus'], axis = 1)
        # tai_Ev_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_v_minus'], axis = 1)
        # tai_Ew_minus = 0.001 * np.sum(self.cu.cubic_grid_array['E_w_minus'], axis = 1)
        
        return {'u_plus': tai_Eu_plus, 'v_plus': tai_Ev_plus, 'w_plus': tai_Ew_plus,
                'u_minus': tai_Eu_minus, 'v_minus': tai_Ev_minus, 'w_minus': tai_Ew_minus}

class sky_influence:
    def __init__(self,
                 path_to_results: str,
                 path_to_geometry_folder: str,
                 epwpath: str,
                 grid: str,
                 ):
        
        data = {'all': [],
        'overcast': [],
        'clear sky': [],
        'intermediate': []}
        
        # address = grid
        # raw_result_path = path_to_results
        # raw_result_array = np.asarray(pd.read_csv(raw_result_path, compression='gzip', header=None))

        df = pd.read_csv(epwpath, skiprows=8, header=None)
        df.columns = list(range(df.shape[1]))
        cloud_cover = df[22].values

        all_mask = np.ones(len(cloud_cover), dtype=bool)
        overcast_mask = np.isin(cloud_cover, [8, 9, 10])
        clear_sky = np.isin(cloud_cover, [0,1,2])
        intermediate_mask = np.isin(cloud_cover, [3,4,5,6,7])
        
        for sky in ['all', 'overcast', 'clear sky', 'intermediate']:
            if sky == 'all':
                mask = np.insert(all_mask,0, True)
            elif sky == 'overcast':
                mask = np.insert(overcast_mask,0, True)
            elif sky == 'clear sky':
                mask = np.insert(clear_sky,0, True)
            elif sky == 'intermediate':
                mask = np.insert(intermediate_mask,0, True)
            else:
                raise ValueError(f"Unknown sky type: {sky}")

            hp = head_pose(results = path_to_results,
                        grid = grid, 
                        temporal_multiplier = mask,
                        path_to_geometry_folder = path_to_geometry_folder,
                        )

            adapl = hp.all_directions_all_point_locations()

            data_clearsky = [adapl["u_plus"], 
                    adapl["u_minus"], 
                    adapl["v_plus"], 
                    adapl["v_minus"], 
                    adapl["w_plus"], 
                    adapl["w_minus"]]
            data[sky] = data_clearsky
        # set font to Times New Roman
        plt.rcParams["font.family"] = "Times New Roman"
        # plot the histograms for each direction
        dirs = ['U+', 'U-', 'V+', 'V-', 'W+', 'W-']
        fig, axes = plt.subplots(2, 3, figsize=(12, 6))
        colors = {'all': 'black', 'intermediate': 'green', 'clear sky': 'orange', 'overcast': 'darkturquoise'}
        
        for i, d in enumerate(dirs):
            ax = axes.flat[i]
            for sky, color in colors.items():
                vals = data[sky][i]
                ax.hist(vals, bins=30, alpha=1, histtype='step', edgecolor=color,
                        weights=np.ones(len(vals))/len(vals))
            ax.set_title(d)
            # set y limit to [0, 0.5]
            ax.set_ylim(0, 0.2)

        fig.text(0.5, 0.0, r'TAI_{d}', ha='center', va='center')
        fig.text(0.0, 0.5, 'Normalised Frequency', ha='center', va='center', rotation='vertical')

        fig.legend(colors.keys(), loc='upper center', ncol=4)
        # set y 
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        # save 
        plt.savefig(f"sky_influence_{os.path.basename(path_to_results)}.pdf", dpi=300, bbox_inches="tight")
        print(f"saved to sky_influence_{os.path.basename(path_to_results)}.pdf")
        plt.show()

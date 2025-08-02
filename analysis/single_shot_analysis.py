# -*- coding: utf-8 -*-
"""
Created on Sat Mar 29 16:08:09 2025

This code takes in blobs of ground and excited state and determine the assignment fidelty 
for the data.


SNR fidelity : Ideal Fidelity
to define this we only take the area under the 'ground' and 'excited' gaussian
we donot take into account any shots of ground in excited and of excited in ground.
its like we forget the number of 'incorrect' shots.

For this I willhave to fit the histograms and then get the fidelity numbers from them
After fitting bimodal gaussian, we only take single gaussian corresponding to ground and excited.
The infidelity is calculated as the area of ground gaussian from intersection point(threshold) to the 
start of single ground gaussian + the area under the excited single gaussain from end point
to intersection point. It assumes that excited blob is on left and ground blob is on right.
The code bove rotates the blob in this manner. 



@author: mk
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy as sc
import os


def Ideal_Fidelity(g_hist, e_hist, bins, intersection_id):
    import scipy as sc
    def gaussian_fit(x, mean, std, a):
        return a*np.exp(-(x-mean)**2 / 2/std**2)
    
    def bimodal(x, m1, std1, a1, m2, std2, a2):
        return gaussian_fit(x, m1, std1, a1) + gaussian_fit(x, m2, std2, a2)
    
    fit_x = np.arange(0, bins, 1)
    init_guess_e = [bins/4, bins/8, 100, 3*bins/4, bins/8, 10]
    init_guess_g = [bins/4, bins/8, 10, 3*bins/4, bins/8, 100]
    fit_g_hist, _ =  sc.optimize.curve_fit(bimodal, fit_x, g_hist, init_guess_g)
    fit_e_hist, _ =  sc.optimize.curve_fit(bimodal, fit_x, e_hist, init_guess_e)
    # assumption that exited blob is on left nd ground blob is on right of excited
    g_gauss = gaussian_fit(fit_x, fit_g_hist[3], fit_g_hist[4], fit_g_hist[5])
    e_gauss = gaussian_fit(fit_x, fit_e_hist[0], fit_e_hist[1], fit_e_hist[2])
    
    infidel = (np.trapz(g_gauss[:intersection_id])+np.trapz(e_gauss[intersection_id:]))/(np.trapz(g_gauss)+np.trapz(e_gauss))
    
    return 1- infidel

def analysis_ss(file_path, bins=2**8, g_signal_vals=0, q0_signal_vals=0, cal_ideal_fidelity=True, save_fig= False):    
    
    result_rot = []
    intersection_id_arr = []
    Ground_State_fidelity = []
    Excited_State_fidelity = []
    readout_fidelity = []
    ideal_fidelity = []
    all_figures = []  # Store figures to return
    
    # if multiple_power_points:
    #     multiplicity = int(input('Enter the multiplicity of the blob data= '))
    
    
    if file_path == None:
        g_signal = g_signal_vals
        q0_signal = q0_signal_vals
        multiplicity = 1
    else:
        multiplicity = int(input('Enter the multiplicity of the blob data= '))
        data = np.loadtxt(file_path, unpack=True)
        g_signal = data[0] + 1j*data[1]
        q0_signal = data[2] + 1j*data[3]
    
    num = len(g_signal) // multiplicity
    
    for i in range(multiplicity):
        g_signal1 = g_signal[int(i*num) : int((i+1)*num)]
        q0_signal1 = q0_signal[int(i*num) : int((i+1)*num)]

        theta_guess = -np.pi/180 * 34
        result = sc.optimize.minimize(optimisation_function, theta_guess, args=(g_signal1, q0_signal1), method='Nelder-Mead')
        
        result_rot.append(result.x[0])
        
        g_signal1_rotated = rotate_complex(g_signal1, result.x[0])
        q0_signal1_rotated = rotate_complex(q0_signal1, result.x[0])
        
        if np.mean(q0_signal1_rotated) > np.mean(g_signal1_rotated):
            g_signal1_rotated = rotate_complex(g_signal1_rotated, np.pi)
            q0_signal1_rotated = rotate_complex(q0_signal1_rotated, np.pi)

        bins = bins
        g_hist, counts_g = np.histogram(np.real(g_signal1_rotated), bins=bins)
        e_hist, counts_e = np.histogram(np.real(q0_signal1_rotated), bins=bins)
        
        err = [np.sum(e_hist[i:]) + np.sum(g_hist[:i]) for i in range(bins)]
        intersection_id = np.argmin(err)
        intersection_id_arr.append(intersection_id)
        
        # Fidelity calculations
        area_g_left = abs(np.trapz(g_hist[:intersection_id]))
        area_g_right = abs(np.trapz(g_hist[intersection_id:]))
        area_e_right = abs(np.trapz(e_hist[intersection_id:]))
        area_e_left = abs(np.trapz(e_hist[:intersection_id]))
        
        Ground_State_fidelity.append(area_g_right / (area_g_left + area_g_right))
        Excited_State_fidelity.append(area_e_left / (area_e_left + area_e_right))
        readout_fidelity.append(((area_g_right / (area_g_left + area_g_right)) + 
                                 (area_e_left / (area_e_left + area_e_right))) / 2)
        if cal_ideal_fidelity == True:
            ideal_fidelity.append(Ideal_Fidelity(g_hist, e_hist, bins, intersection_id))
        
        threshold_I = (counts_e[np.argmin(err)]+counts_g[np.argmin(err)])/2

        # Create a 2x2 figure
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        
        # Plot 1: Raw data
        axes[0, 0].plot(np.real(g_signal1), np.imag(g_signal1), 'o', markersize=0.5, label='Ground')
        axes[0, 0].plot(np.real(q0_signal1), np.imag(q0_signal1), '*', markersize=0.5, label='Excited')
        axes[0, 0].set_title(f'Raw IQ Data {i+1}')
        axes[0, 0].legend()
        axes[0, 0].grid()

        # Plot 2: Rotated Data
        axes[0, 1].plot(np.real(g_signal1_rotated), np.imag(g_signal1_rotated), '.', markersize=0.5, label=f'G-Fd {Ground_State_fidelity[-1]:.6f}')
        axes[0, 1].plot(np.real(q0_signal1_rotated), np.imag(q0_signal1_rotated), '.', markersize=0.5, label=f'E-Fd {Excited_State_fidelity[-1]:.6f}')
        axes[0, 1].set_title(f'Rotated IQ Data {i+1}')
        axes[0, 1].legend()
        axes[0, 1].grid()

        # Plot 3: Error function
        axes[1, 0].plot(err)
        axes[1, 0].set_title(f'Error Function {i+1}')
        axes[1, 0].axvline(x=intersection_id, color='gray', linestyle='--')

        # Plot 4: Histograms
        #axes[1, 1].plot(np.log10(g_hist), '.', label='Ground')
        #axes[1, 1].plot(np.log10(e_hist), '.', label='Excited')
        axes[1, 1].plot((g_hist), '.', label='Ground')
        axes[1, 1].plot((e_hist), '.', label='Excited')
        axes[1, 1].axvline(x=intersection_id, color='grey', linestyle='--')
        axes[1, 1].set_title(f'Histograms {i+1} and total fidelity {readout_fidelity[-1]:.6f}')
        axes[1, 1].legend()

        plt.tight_layout()
        if save_fig:
            plt.savefig(rf'{os.path.dirname(file_path)}\\_analysis_ss_{str(i).zfill(3)}.png')
        plt.close()
        # plt.show()
        
        all_figures.append(fig)  # Store the figure

    return Ground_State_fidelity, Excited_State_fidelity, readout_fidelity, ideal_fidelity, threshold_I, np.array(result_rot), np.array(intersection_id_arr), all_figures


def optimisation_function(theta, g, q0):
    g_signal_dc_rotated = rotate_complex(g, theta)
    q0_signal_dc_rotated = rotate_complex(q0, theta)
    min_var = np.abs(np.mean(np.imag(q0_signal_dc_rotated)) - np.mean(np.imag(g_signal_dc_rotated)))
    return min_var


def rotate_complex(data, theta):
    """Rotates complex data points by a given angle."""
    return data * np.exp(1j * theta)

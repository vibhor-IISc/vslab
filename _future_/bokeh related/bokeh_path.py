#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 11 18:27:38 2025

@author: vibhor
"""

from bokeh.models import Button, CustomJS
from bokeh.layouts import column
from bokeh.io import show

import os

def create_file_browser_button():
    """
    Creates a bokeh button for selecting a file with .dat extension.

    Returns:
        Button: A bokeh Button object.
    """
    button = Button(label="Select .dat File")
    button.js_on_click(CustomJS(args={}, code="""
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.dat'; 
        input.onchange = () => {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    // You can process the file content here (e.target.result)
                    console.log(input.files[0].path); // Print the absolute path
                };
                reader.readAsText(input.files[0]);
            }
        };
        input.click();
    """))
    return button

# Create the button and display it
button = create_file_browser_button()
layout = column(button)
show(layout)
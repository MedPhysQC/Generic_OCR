#!/usr/bin/env python
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# PyWAD is open-source software and consists of a set of modules written in python for the WAD-Software medical physics quality control software. 
# The WAD Software can be found on https://github.com/wadqc
# 
# The pywad package includes modules for the automated analysis of QC images for various imaging modalities. 
# PyWAD has been originaly initiated by Dennis Dickerscheid (AZN), Arnold Schilham (UMCU), Rob van Rooij (UMCU) and Tim de Wit (AMC) 
#
#
# Changelog:
#   20180329: Changed "sum" value for rgb to "avg" and fixed implementation.
#   20180328: Fix reading of US_RGB data using pydicom 1.x; added rgb2gray of JG
#   20171117: sync with US module; removed data reading by wadwrapper_lib
#   20161220: removed class variables; removed testing stuff
#   20160901: first version, combination of TdW, JG, AS
#
# mkdir -p TestSet/StudyCurve
# mkdir -p TestSet/Config
# cp ~/Downloads/1/us_philips_*.xml TestSet/Config/
# ln -s /home/nol/WAD/pyWADdemodata/US/US_AirReverberations/dicom_curve/ TestSet/StudyCurve/
# ./ocr_wadwrapper.py -d TestSet/StudyEpiqCurve/ -c Config/ocr_philips_epiq.json -r results_epiq.json
#
from __future__ import print_function

__version__ = '20180329'
__author__ = 'aschilham'

import os
# this will fail unless wad_qc is already installed
from wad_qc.module import pyWADinput
from wad_qc.modulelibs import wadwrapper_lib
try:
    import pydicom as dicom
except ImportError:
    import dicom

import numpy as np
import ocr_lib

def logTag():
    return "[OCR_wadwrapper] "

# function for changing RGB image to grayscale
def rgb2gray(rgb):
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray

def readdcm(inputfile, channel, slicenr):
    """
    Use pydicom to read the image. Only implement 2D reading, and do not transpose axes.
      channel: either a number in [0, number of channels] or one of 'avg', 'rgb':
          use the given channel only or averare all channels, or use rgb2gray to get a 
          gray scale image.
      slicenr: use the given slicenr if the dicom file contains a 3D image
    """
    dcmInfile = dicom.read_file(inputfile)
    pixeldataIn = dcmInfile.pixel_array

    # check if this is multi-channel (RGB) data. If so, use the user defined method to convert it to gray scale
    channels = dcmInfile.get('SamplesPerPixel', 1)

    # first check single channel data
    if channels == 1: #
        # if this is 3D data in a single image, use only the defined slice
        if len(np.shape(pixeldataIn)) == 3:
            pixeldataIn = pixeldataIn[slicenr]

        return dcmInfile, pixeldataIn

    ## multi-channel data
    # AS: this fix was only needed in pydicom < 1.0; solved in later versions
    try:
        dicomversion = int(dicom.__version_info__[0])
    except:
        dicomversion = 0
    if dicomversion == 0:
        try:
            nofframes = dcmInfile.NumberOfFrames
        except AttributeError:
            nofframes = 1
        if dcmInfile.PlanarConfiguration==0:
            pixel_array = pixeldataIn.reshape(nofframes, dcmInfile.Rows, dcmInfile.Columns, dcmInfile.SamplesPerPixel)
        else:
            pixel_array = pixeldataIn.reshape(dcmInfile.SamplesPerPixel, nofframes, dcmInfile.Rows, dcmInfile.Columns)
    else:
        pixel_array = pixeldataIn 

    # first simple cases
    if isinstance(channel, int):
        if(channel>=channels or channel<0):
            raise ValueError("Data has {} channels. Invalid selected channel {}!".format(channels, channel))

        if len(np.shape(pixel_array)) == 4: #3d multi channel
            if dcmInfile.PlanarConfiguration==0:
                pixeldataIn = pixel_array[slicenr, :, :, channel]
            else:
                pixeldataIn = pixel_array[channel, slicenr, :, :]# e.g. ALOKA images
        else:
            pixeldataIn = pixeldataIn[:, :, channel]
            
        return dcmInfile, pixeldataIn
        
    # special values for channel:
    if channel == 'avg':
        # add all channels
        if len(np.shape(pixel_array)) == 4: #3d multi channel
            pixeldataIn = pixel_array[slicenr, :, :, 0].astype(float)
            for c in range(1, channels):
                pixeldataIn += pixel_array[slicenr, :, :, c]
        else:
            pixeldataIn = pixel_array[:, :, 0].astype(float)
            for c in range(1, channels):
                pixeldataIn += pixel_array[:, :, c]

        return dcmInfile, pixeldataIn/channels # ocr_lib expects pixel values 0-255

    if channel == 'rgb':
        print('{} Converting RGB-image to grayscale'.format(logTag()))
        # weigthed average of RGB data to make grayscale image
        if len(np.shape(pixel_array)) == 4: #3d multi channel
            pixeldataIn = pixel_array[slicenr, :, :, :]
        else:
            pixeldataIn = pixel_array[:, :, :]
        pixeldataIn = rgb2gray(pixeldataIn)
        return dcmInfile, pixeldataIn # ocr_lib expects pixel values 0-255

    raise ValueError("Data has {} channels. Invalid selected channel {}! Should be a number or one of 'avg', 'rgb'.".format(channels, channel))
    
    
def OCR(data, results, action):
    """
    Use pyOCR which for OCR
    """
    try:
        params = action['params']
    except KeyError:
        params = {}

    channel = params.get('channel', 'avg')
    slicenr = params.get('slicenr', -1)
    ocr_threshold = params.get('ocr_threshold', 0)
    ocr_zoom = params.get('ocr_zoom', 10)

    inputfile = data.series_filelist[0][0] # only single images 
    dcmInfile, pixeldataIn = readdcm(inputfile, channel, slicenr)

    # solve ocr params
    regions = {}
    for k,v in params.items():       
        #"Parameter1:name":"H1_Countrate",
        #"Parameter1:suffix": "Kcts/sec",
        #"Parameter1:type": "float",
        #"Parameter1:xywh": "157;320;130;21",
          
        if k.startswith('Parameter'):
            split = k.find(':')
            p = k[:split]
            p = p[9:]
            stuff = k[split+1:]
            if not p in regions:
                regions[p] = {'prefix':'', 'suffix':''}
            if stuff == 'xywh':
                regions[p]['xywh'] = [int(p) for p in v.split(';')]
            elif stuff == 'prefix':
                regions[p]['prefix'] = v
            elif stuff == 'suffix':
                regions[p]['suffix'] = v
            elif stuff == 'type':
                regions[p]['type'] = v
            elif stuff == 'name':
                regions[p]['name'] = v

    for p, region in regions.items():
        txt, part = ocr_lib.OCR(pixeldataIn, region['xywh'], ocr_zoom=ocr_zoom, ocr_threshold=ocr_threshold, transposed=False)
        if region['type'] == 'object':
            import scipy
            im = scipy.misc.toimage(part) 
            fn = '%s.jpg'%region['name']
            im.save(fn)
            results.addObject(region['name'], fn)
            
        else:
            value = ocr_lib.txt2type(txt, region['type'], region['prefix'],region['suffix'])
            if region['type'] == 'float':
                results.addFloat(region['name'], value)
            elif region['type'] == 'string':
                results.addString(region['name'], value)
            elif region['type'] == 'bool':
                results.addBool(region['name'], value)

def acqdatetime_series(data, results, action):
    """
    Read acqdatetime from dicomheaders and write to IQC database

    Workflow:
        1. Read only headers
    """
    try:
        params = action['params']
    except KeyError:
        params = {}

    ## 1. read only headers
    dcmInfile = dicom.read_file(data.series_filelist[0][0], stop_before_pixels=True)

    dt = wadwrapper_lib.acqdatetime_series(dcmInfile)

    results.addDateTime('AcquisitionDateTime', dt) 

if __name__ == "__main__":
    data, results, config = pyWADinput()

    # read runtime parameters for module
    for name,action in config['actions'].items():
        if name == 'acqdatetime':
            acqdatetime_series(data, results, action)
        elif name == 'qc_series':
            OCR(data, results, action)

    #results.limits["minlowhighmax"]["mydynamicresult"] = [1,2,3,4]

    results.write()

# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Standard Library Imports
import logging
from typing import Any, Dict, Optional
import ctypes

# Third Party Imports
from ximea import xiapi
import numpy as np

# Local Imports
from navigate.model.devices.camera.base import CameraBase
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class XimeaBase(CameraBase):
    """Ximea camera base class.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize MU196XR class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        """
        super().__init__(microscope_name, device_connection, configuration)

        #: str: Name of the microscope
        self.microscope_name = microscope_name

        #: object: Camera Object
        self.cam = device_connection

        #: dict: Configuration settings
        self.configuration = configuration

        #: dict: Camera parameters
        self.camera_parameters["x_pixels"] = self.cam.get_param("width:max")
        self.camera_parameters["y_pixels"] = self.cam.get_param("height:max")
        self.camera_parameters["x_pixels_min"] = self.cam.get_param("width:min")
        self.camera_parameters["y_pixels_min"] = self.cam.get_param("height:min")
        self.camera_parameters["x_pixels_step"] = self.cam.get_param("width:inc")
        self.camera_parameters["y_pixels_step"] = self.cam.get_param("height:inc")
        self.offset_x_min = self.cam.get_param("offsetX:min")
        self.offset_x_max = self.cam.get_param("offsetX:max")
        self.offset_x_step = self.cam.get_param("offsetX:inc")
        self.offset_y_min = self.cam.get_param("offsetY:min")
        self.offset_y_max = self.cam.get_param("offsetY:max")
        self.offset_y_step = self.cam.get_param("offsetY:inc")
        self.minimum_exposure_time = self.cam.get_param("exposure:min")

        # set external rising edge trigger: XI_TRG_EDGE_RISING
        # the input signal port should be set in configuration
        self.cam.set_param("gpi_selector", "XI_GPI_PORT1")
        self.cam.set_param("gpi_mode", "XI_GPI_TRIGGER")
        self.cam.set_param('trigger_source', "XI_TRG_EDGE_RISING")


    def __str__(str):
        """Return string representation of Ximea Base class
        
        Returns
        -------
        str
            String representation of Ximea Base class.
        """
        return "XimeaBase"
    
    def __del__(self):
        """Delete Ximea Camera class."""
        self.cam.close_device()

    @classmethod
    def get_connect_params(cls):
        """Register the parameters required to connect to the camera.

        Returns
        -------
        list
            List of parameters required to connect to the camera.
        """
        return ["serial_number"]

    @classmethod
    def connect(cls, serial_number):
        """Build Photometrics Stage Serial Port connection

        Import Photometrics API and Initialize Camera Controller.

        Parameters
        ----------
        serial_number : str
            Camera serial number

        Returns
        -------
        cam : object
            Camera object.
        """
        try:
            cam = xiapi.Camera()
            # XI_OPEN_BY_SN
            cam.open_device_by_SN(str(serial_number))
            return cam
        except Exception as e:
            logger.error(f"Could not establish connection with camera: {e}.")
            raise UserWarning(
                "Could not establish connection with XIMEA camera", serial_number
            )
        
    @property
    def serial_number(self):
        """Get Camera Serial Number

        Returns
        -------
        serial_number : str
            Serial number for the camera.
        """
        self.cam.get_param("device_sn")

    def report_settings(self):
        """Print Camera Settings.

        Prints the current camera settings to the console and the log file.
        """
        params = ["exposure", ]
        for param in params:
            print(param, self.camera_controller.get_property_value(param))
            logger.info(f"{param}, {self.camera_controller.get_property_value(param)}")

    def set_sensor_mode(self, mode):
        """Set Ximea sensor mode.

        On the manual page 72:
        Cameras can be operated in two shutter modes, Rolling Shutter or Global Reset Release. 
        The Rolling Shutter mode is used if the camera is operated in free-run mode. 
        If the camera is triggered, either by hardware trigger or through software, 
        the sensor uses the Global Reset Release mode.

        Parameters
        ----------
        mode : str
            'Normal' or 'Light-Sheet'
        """
        #TODO: test if the shutter
    
    def set_readout_direction(self, mode):
        """Set readout direction"""
        pass

    def calculate_readout_time(self):
        """Get the duration of time needed to read out an image.

        Returns
        -------
        readout_time : float
            Duration of time needed to read out an image.
        """
        return 0
    
    def set_exposure_time(self, exposure_time):
        """Set Ximea exposure time.

        Note
        ----
            Units of the Ximea API are in microseconds.

        Parameters
        ----------
        exposure_time : float
            Exposure time in seconds.
        """
        return self.cam.set_param("exposure", exposure_time * 1000000)
    
    def set_line_interval(self, line_interval_time):
        """Set line interval.

        Parameters
        ----------
        line_interval_time : float
            Line interval duration.
        """
        return False

    def get_line_interval(self):
        """Get line interval.

        Returns
        -------
        line_interval_time : float
            Line interval duration.
        """
        self.line_interval = 0

    def set_binning(self, binning_string):
        """Set Ximea Camera binning mode.

        Parameters
        ----------
        binning_string : str
            Desired binning properties (e.g., '1x1', '2x2', '4x4', '8x8', '16x16',
            '1x2', '2x4')

        Returns
        -------
        result: bool
            True if successful, False otherwise.
        """
        binning_dict = {
            "1x1": 1,
            "2x2": 2,
            "3x3": 3,
            "4x4": 4,
            "5x5": 5,
            "6x6": 6,
            "7x7": 7,
            "8x8": 8,
            "9x9": 9,
            "10x10": 10,
            "16x16": 16
        }
        if binning_string not in binning_dict.keys():
            logger.debug(f"can't set binning to {binning_string}")
            print(f"can't set binning to {binning_string}")
            return False
        # self.cam.set_param("downsampling_type", 0) # XI_BINNING
        self.cam.set_param("downsampling", binning_dict[binning_string])
        return True

    def set_ROI(self, roi_width=2048, roi_height=2048, center_x=1024, center_y=1024):
        """Change the size of the active region on the camera.

        Parameters
        ----------
        roi_width : int
            Width of active camera region.
        roi_height : int
            Height of active camera region.
        center_x : int
            X position of the center of view
        center_y : int
            Y position of the center of view

        Returns
        -------
        result: bool
            True if successful, False otherwise.
        """
        offset_x = center_x - roi_width // 2
        offset_y = center_y - roi_height // 2
        if (self.roi_width % self.camera_parameters["x_pixels_step"] != 0
            or self.roi_height % self.camera_parameters["y_pixels_step"] != 0
            or offset_x < self.offset_x_min
            or offset_x > self.offset_x_max
            or offset_x % self.offset_x_step != 0
            or offset_y < self.offset_y_min
            or offset_y > self.offset_y_max
            or offset_y % self.offset_y_step != 0
            or offset_x + roi_width > self.camera_parameters["x_pixels"]
            or offset_y + roi_height > self.camera_parameters["y_pixels"]
        ):
            logger.debug(f"can't set roi to {roi_width} and {roi_height} with the center ({center_x}, {center_y})")
            return False
        
        self.cam.set_param("width", roi_width)
        self.cam.set_param("height", roi_height)
        self.cam.set_param("offsetX", offset_x)
        self.cam.set_param("offsetY", offset_y)

        self.x_pixels = self.cam.get_param("width")
        self.y_pixels = self.cam.get_param("height")

        return self.x_pixels == roi_width and self.y_pixels == roi_height

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        """Initialize Ximea Camera image series.

        Parameters
        ----------
        data_buffer :
            List of SharedNDArrays of shape=(self.img_height,
            self.img_width) and dtype="uint16"
            Default is None.
        number_of_frames : int
            Number of frames.  Default is 100.
        """
        self._data_buffer = data_buffer
        self._number_of_frames = number_of_frames
        self._frames_received = 0

        # set buffer policy: XI_BP_SAFE
        self.cam.set_param("buffer_policy", 1)
        # set image data format to XI_MONO16
        self.set_param('imgdataformat', 1)
        #TODO: test if setting imgpayloadsize is necessary
        self.cam.get_param("imgpayloadsize")
        # start_acquisition
        self._image = xiapi.Image()
        self.cam.start_acquisition()
        self.is_acquiring = True
        self.cam.get_param("imgpayloadsize")

    def close_image_series(self):
        """Close image series.

        Stops the acquisition and sets is_acquiring flag to False.
        """
        self.cam.stop_acquisition()
        self.is_acquiring = False

    def get_new_frame(self):
        """Get frame from Ximea camera.

        Returns
        -------
        frame : numpy.ndarray
            Frame ids from Ximea camera.
        """
        # attach buffer to image object
        self._image.bp = ctypes.c_void_p(self._data_buffer[self._frames_received].ctypes.data)
        self.cam.get_image(self._image, 500)

        # if attach buffer doesn't work
        # self._data_buffer[self._frames_received][:, :] = np.copy(
        #     self._image.get_image_data_numpy()[:]
        # )

        self._frames_received += 1
        if self._frames_received >= self._number_of_frames:
            self._frames_received = 0

class MU196XRCamera(XimeaBase):
    """Ximea MU196XR class.

    This camear class supports ximea camera models: MU196MR/MU196CR.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize MU196XR class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        """
        super().__init__(microscope_name, device_connection, configuration)

    def __str__(str):
        """Return string representation of Ximea MU196XR class
        
        Returns
        -------
        str
            String representation of Ximea MU196XR class.
        """
        return "Ximea MU196XR Camera"


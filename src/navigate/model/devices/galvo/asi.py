# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

#  Standard Library Imports
import logging
import time
from typing import Any, Dict


# Local Imports
from navigate.model.devices.galvo.base import GalvoBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASIGalvo(GalvoBase , SerialDevice):
    """GalvoASI Class - ASI DAQ Control of Galvanometers"""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the GalvoNI class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            Connection to the NI DAQ device.
        configuration : Dict[str, Any]
            Dictionary of configuration parameters.
        device_id : int
            Galvo ID. Default is 0.
        """
        super().__init__(microscope_name, device_connection, configuration, device_id)

        #: Any: Device connection.
        self.galvo = device_connection

        #: dict: Dictionary of microscope configuration parameters.
        self.configuration = configuration
        
        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: int: Galvo ID.
        self.galvo_id = device_id

        #: str: Name of the NI port for galvo control.
        self.trigger_source = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["trigger_source"]

        #: str: Name of the galvo.
        self.galvo_name = "Galvo " + str(device_id)

        #: dict: Dictionary of device connections.
        self.device_config = configuration["configuration"]["microscopes"][
            microscope_name
        ]["galvo"][device_id]

        #: int: Sample rate.
        self.sample_rate = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sample_rate"]

        #: float: Sweep time.
        self.sweep_time = 0

        #: float: Camera delay
        self.camera_delay = (
            configuration["configuration"]["microscopes"][microscope_name]["camera"][
                "delay"
            ]
            / 1000
        )

        #: float: Galvo max voltage.
        self.galvo_max_voltage = self.device_config["hardware"]["max"]

        #: float: Galvo min voltage.
        self.galvo_min_voltage = self.device_config["hardware"]["min"]

        # Galvo Waveform Information
        #: str: Galvo waveform. Waveform or Sawtooth.
        self.galvo_waveform = self.device_config.get("waveform", "sawtooth")

        self.axis = self.device_config["hardware"].get("axis","B")

    def __str__(self) -> str:
        """Return string representation of the GalvoASI."""
        return "GalvoASI"
    
    @classmethod
    def connect(cls, port, baudrate=115200, timeout=0.25):
        """Build ASILaser Serial Port connection

        Parameters
        ----------
        port : str
            Port for communicating with the filter wheel, e.g., COM1.
        baudrate : int
            Baud rate for communicating with the filter wheel, default is 115200.
        timeout : float
            Timeout for communicating with the filter wheel, default is 0.25.

        Returns
        -------
        tiger_controller : TigerController
            ASI Tiger Controller object.
        """
        # wait until ASI device is ready
        tiger_controller = TigerController(port, baudrate)
        tiger_controller.connect_to_serial()
        if not tiger_controller.is_open():
            logger.error("ASI stage connection failed.")
            raise Exception("ASI stage connection failed.")
        return tiger_controller

    def adjust(self, exposure_times, sweep_times):
        """Adjust the galvo waveform to account for the camera readout time.

        Parameters
        ----------
        exposure_times : dict
            Dictionary of camera exposure time in seconds on a per-channel basis.
            e.g., exposure_times = {"channel_1": 0.1, "channel_2": 0.2}
        sweep_times : dict
            Dictionary of acquisition sweep time in seconds on a per-channel basis.
            e.g., sweep_times = {"channel_1": 0.1, "channel_2": 0.2}

        Returns
        -------
        waveform_dict : dict
            Dictionary that includes the galvo waveforms on a per-channel basis.
        """
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        microscope_name = microscope_state["microscope_name"]
        zoom_value = microscope_state["zoom"]
        galvo_factor = self.configuration["waveform_constants"]["other_constants"].get(
            "galvo_factor", "none"
        )
        galvo_parameters = self.configuration["waveform_constants"]["galvo_constants"][
            self.galvo_name
        ][microscope_name][zoom_value]
        self.sample_rate = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["sample_rate"]

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.
                # Should Assert.
                exposure_time = exposure_times[channel_key]
                self.sweep_time = sweep_times[channel_key]

                # galvo Parameters
                try:
                    galvo_amplitude = float(galvo_parameters.get("amplitude", 0))
                    galvo_offset = float(galvo_parameters.get("offset", 0))
                    galvo_frequency = (
                        float(galvo_parameters.get("frequency", 0)) / exposure_time
                    )
                    factor_name = None
                    if galvo_factor == "channel":
                        factor_name = (
                            f"Channel {channel_key[channel_key.index('_')+1:]}"
                        )
                    elif galvo_factor == "laser":
                        factor_name = channel["laser"]
                    if factor_name and factor_name in galvo_parameters.keys():
                        galvo_amplitude = float(
                            galvo_parameters[factor_name].get("amplitude", 0)
                        )
                        galvo_offset = float(
                            galvo_parameters[factor_name].get("offset", 0)
                        )

                except ValueError as e:
                    logger.debug(
                        f"{e} waveform constants.yml doesn't have parameter "
                        f"amplitude/offset/frequency for {self.galvo_name}"
                    )
                    return

                # Calculate the Waveforms
                if self.galvo_waveform == "sawtooth":
                    frequency=galvo_frequency
                    amplitude=galvo_amplitude
                    offset=galvo_offset

                    self.sawtooth(frequency, amplitude, offset)

                elif self.galvo_waveform == "sine":
                    frequency=galvo_frequency
                    amplitude=galvo_amplitude
                    offset=galvo_offset
                
                    self.sine_wave(frequency, amplitude, offset)
                
                elif self.galvo_waveform == "halfsaw":
                    frequency=galvo_frequency
                    amplitude=galvo_amplitude
                    offset=galvo_offset
                    
                    self.half_saw(frequency, amplitude, offset)
                else:
                    print("Unknown Galvo waveform specified in configuration file.")
                    continue
    
    def sawtooth(
        self,
        frequency=10,
        amplitude=1,
        offset=0,
    ):
        """
        Sends the tiger controller commands to make the sawtooth wave

        Parameters
        ----------
        frequency : Float
            Unit - Hz
        amplitude : Float
            Unit - Volts
        offset : Float
            Unit - Volts
        """

        period = int((1.0 / frequency)*1000)
        amplitude *= 1000
        offset *= 1000

        self.galvo.SA_waveform(self.axis, 128, amplitude, offset, period)
        self.galvo.SAM(self.axis, 4)

        # need to adjust it so it only runs for the duration of the sweep time
        # do we want to do anything with duty cycle or phase, or accept that as a limitation

    def sine_wave(
        self,
        frequency=10.0,  
        amplitude=1.0, 
        offset=0.0
    ):
        """Returns a numpy array with a sine waveform

        Used for creating analog laser drive voltage.

        Parameters
        ----------
        sample_rate : int, optional
            Unit - Hz, by default 100000
        sweep_time : float, optional
            Unit - Seconds, by default 0.4
        frequency : int, optional
            Unit - Hz, by default 10
        amplitude : float, optional
            Unit - Volts, by default 1
        offset : float, optional
            Unit - Volts, by default 0
        phase : float, optional
            Unit - Radians, by default 0

        Returns
        -------
        waveform : np.array

        Examples
        --------
        >>> typical_laser = sine_wave(sample_rate, sweep_time, 10, 1, 0, 0)

        """
        period = int((1.0 / frequency)*1000)
        amplitude *= 1000
        offset *= 1000

        self.galvo.SA_waveform(self.axis, 131, amplitude, offset, period)
        self.galvo.SAM(self.axis, 4)
    
        # need to adjust it so it only runs for the duration of the sweep time
        # do we want to do anything with phase, or accept that as a limitation

    def half_saw(
        self,
        frequency=10,
        amplitude=1,
        offset=0,
    ):
        """Sends the tiger controller commands to make the ramp wave

        Parameters
        ----------
        exposure_time : Float
            Unit - Seconds
        sweep_time : Float
            Unit - Seconds
        remote_focus_delay : Float
            Unit - seconds
        camera_delay : Float
            Unit - seconds
        fall : Float
            Unit - seconds
        amplitude : Float
            Unit - Volts
        offset : Float
            Unit - Volts
        """

        # rise period
        period = int((1.0 / frequency)*1000)
        
        amplitude *= 1000/2
        offset *= 1000

        self.galvo.SA_waveform(self.axis, 128, amplitude, offset, period)
        time.sleep(1/frequency)
        self.galvo.SAM(self.axis, 2)

    def turn_off(self): 
        """Stops the galvo waveform"""
        self.galvo.SAM(self.axis, 0)

    def close(self):
        """Close the ASI galvo serial port.

        Stops the remote focus waveform and then closes the port.
        """
        if self.galvo.is_open():
            self.turn_off()
            logger.debug("ASI Remote Focus - Closing Device.")
            self.galvo.disconnect_from_serial()

    def __del__(self):
        """Destructor for the ASIGalvo class."""
        self.close()

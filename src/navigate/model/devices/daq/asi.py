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


# Standard Imports
import logging
from threading import Lock
import traceback
import time
from typing import Union, Dict, Any

# Third Party Imports
import numpy as np
import serial
# Local Imports
from navigate.model.devices.remote_focus.asi import ASIRemoteFocus
#from navigate.model.devices.galvo.asi import galvo
from navigate.model.devices.daq.base import DAQBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization
#from navigate.tools.waveform_template_funcs import get_waveform_template_parameters


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

@log_initialization
class ASIDaq(DAQBase, SerialDevice):
    """ASIDAQ class for Data Acquisition (DAQ). 

    Representation of Tiger Controller in action. 
    Triggers all devices and outputs to camera trigger channel.
    """

    def __init__(self, microscope_name, device_connection, configuration: Dict[str, Any], device_id) -> None:
        """Initialize the ASI DAQ.

        Parameters
        ----------
        configuration : Dict[str, Any]
            Configuration dictionary.
        """
        super().__init__(configuration)

        #: dict: Configuration dictionary.
        self.configuration = configuration

        #: dict: Camera object.
        self.camera = {}

        #: Lock: Lock for waiting to run.
        self.wait_to_run_lock = Lock()

        #: dict: Analog output tasks.
        self.analog_outputs = {}

        #: bool: Flag for updating analog task.
        self.is_updating_analog_task = False

        #: str: Trigger mode. Self-trigger or external-trigger.
        self.trigger_mode = "self-trigger"

        self.daq = device_connection

        self.daq.setup_control_loop(3, .12)
        self.microscope_name = microscope_name

        self.remote_focus = ASIRemoteFocus

        #self.galvo = ASIGalvo

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

    def create_camera_task(self, channel_key: str) -> None:
        """
        Set up the camera trigger pulse using ASI Tiger Controller.

        Parameters
        ----------
        channel_key : str
            Channel key for current channel.
        """
        camera_waveform_repeat_num = self.waveform_repeat_num * self.waveform_expand_num

        if self.analog_outputs:
            camera_high_time = 4  # ms
        elif camera_waveform_repeat_num == 1:
            camera_high_time = (self.sweep_times[channel_key] * 1000) - (self.camera_delay * 1000)
        else:
            camera_high_time = (self.sweep_times[channel_key] * 1000) - 4

        camera_delay_ms = int(self.camera_delay * 1000)

        ttl_channel = int(self.configuration["configuration"]["microscopes"][self.microscope_name]["daq"]["camera_trigger_out_line"])

        try:
            response = TigerController.send_ttl_pulse(
                channel=ttl_channel,
                pulse_width_ms=int(camera_high_time),
                delay_ms=camera_delay_ms
            )
            logger.info(f"Sent TTL command to ASI: {response}")
        except Exception:
            logger.exception("Failed to send TTL command to ASI.")

    def prepare_acquisition(self, channel_key: str) -> None:
        # self.create_analog_output_tasks(channel_key)

        # self.create_camera_task(channel_key)
        sweep_time = self.sweep_times[channel_key]
        print(f'Sweep Time: {sweep_time}')
        #phase = self.configuration["configuration"]["microscopes"][self.microscope_name]["galvo"][galvo_name]["phase"]
        self.daq.setup_control_loop(3,sweep_time)
        time.sleep(0.2)
        self.daq.trigger_acquisition()
        self.current_channel_key = channel_key
        self.is_updating_analog_task = False
        # if self.wait_to_run_lock.locked():
        #     self.wait_to_run_lock.release()

    def run_acquisition(self) -> None:

        # if self.is_updating_analog_task:
        #     self.wait_to_run_lock.acquire()
        #     self.wait_to_run_lock.release()

        # try:
        #send logic card on to cell 1
        self.daq.logic_cell_on("1")
        # except Exception:
        #     logger.debug("DAQ cannot turn on")
        #     pass

    def stop_acquisition(self) -> None:
        #send logic card off to cell 1
        try:
            self.daq.logic_cell_off("1") 
            self.daq.logic_cell_on("8")
            self.daq.send_command("sam a =0")
            self.daq.read_response()                   
        except Exception:
            logger.debug("DAQ cannot turn off")
            pass

        # if self.wait_to_run_lock.locked():
        #     self.wait_to_run_lock.release()

    # def create_analog_output_tasks(self, channel_key: str) -> None:
    #     galvo_channel = self.configuration["configuration"]["microscopes"][self.microscope_name]["galvo"][0]["hardware"]["axis"]
    #     if isinstance(galvo_channel, list):
    #         for channel in galvo_channel:
    #            self.analog_outputs.update({channel: "galvo"})
    #            self.galvo.move(self.exposure_times,self.sweep_times,offset=None)
    #     else:
    #         self.analog_outputs.update({galvo_channel: "galvo"})
    #     remote_focus_channel = self.configuration["configuration"]["microscopes"][self.microscope_name]["remote_focus"]["hardware"]["axis"]
    #     self.analog_outputs.update({remote_focus_channel: "remote_focus"})
    #     print(self.exposure_times)
    #     print(self.sweep_times)
    #     self.remote_focus.move(self.exposure_times, self.sweep_times)




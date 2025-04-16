Case Studies
============

Setting Up a Microscope
------------------------

In the first case study, we demonstrate how to set up a microscope using the **navigate** software. This is shown using the 'configuration.yaml' file, which provides very granular control over the microscope settings.

.. toctree::
   :maxdepth: 2

   setup_voodoo

------------------

Operating a Microscope
------------------------

Light sheet microscopy is a very versatile technique. Here we present some case studies
that demonstrate how **navigate** can be used to acquire data from different types of
light sheet microscopes. These include:

- An Axially Swept Light-Sheet Microscope that scans the beam in both the laser propagation (``Y``)
  and detection (``Z``) directions synchronously with a piezo mounted objective.
  Tiling in ``X``, ``Y``, and ``Z`` is provided by a motorized stage.

- A Digitally Scanned, Axially Swept Light-Sheet Microscope that scans the beam laterally
  (``X``) with galvanometric mirrors to create a virtual sheet of light, and axially
  (``Y``) with an electronically tunable lens. The sample is moved in the detection direction
  (``Z``) to acquire a stack. Tiling in ``X``, ``Y``, and ``Z`` is provided by a motorized stage.

- An Axially Swept Light-Sheet Microscope that scans the beam in the laser propagation
  direction (``Y``), but acquires a stack by moving the sample in the detection direction (``Z``.
  Tiling in ``X``, ``Y``, and ``Z`` is provided by a motorized stage.

- An Axially Swept Light-Sheet Microscope that is configured in an upright, di-SPIM-like,
  geometry. The beam is scanned in the laser propagation direction (``Y``), but the sample
  is scanned at a constant velocity in a direction that is 45 degrees to the detection and
  laser propagation directions (``X``). Acquiring data in this format permits imaging of thinner (e.g., ~2 mm)
  specimens with very large lateral extents without the overhead associated with stepping and settling
  the sample stage. Tiling in ``X``, ``Y``, and ``Z`` is provided by a motorized stage.

.. toctree::
   :maxdepth: 2

   acquire_mesospimbt
   acquire_CT-ASLM-V1_and_CT-ASLM-V2
   acquire_exASLM


------------------


Using the REST-API
------------------------

.. toctree::
   :maxdepth: 2

   ilastik_segmentation


------------------

Performing Smart Microscopy
---------------------------

.. toctree::
   :maxdepth: 2

   06_human_in_the_loop/human_in_the_loop
   07_smart_tiling/smart_tiling
   08_smart_object_detection/smart_object_detection

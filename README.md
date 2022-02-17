# INGInious-dispenser-demo

Additional INGInious task dispenser example. The simple one offers the ability to 
filter and determine the order in which tasks are shown to the students.

## Installing

    pip3 install git+https://github.com/UCL-INGI/INGInious-dispenser-demo

## Activating

In your ``configuration.yaml`` file, add the following plugin entry:

    plugins:
      - plugin_module: "inginious-dispenser-demo"

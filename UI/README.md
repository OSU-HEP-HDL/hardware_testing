# hardware_testing UI
Adapted tools used for the UI

In order to run these scripts, the user must have an account with the ITk database. https://itkpd-test.unicorncollege.cz/

A tutorial on these scripts can be found at https://github.com/OSU-HEP-HDL/hardware_database_tutorial

## Register Component
This now takes arguments instead of giving prompts. The ```--help``` shows the arguments:
```
options:
  -h, --help            show this help message and exit
  -t TYPE, --type TYPE  Component Type, ex. DATA FLEX
  -s STATUS, --status STATUS
                        Component Status, ex. Pre-Production
  -pl PLACEMENT, --placement PLACEMENT
                        Component Placement, ex. Barrel or Ring
  -m MODULE, --module MODULE
                        Module Type, ex. TRIPLET
  -f FLAVOR, --flavor FLAVOR
                        Component Flavor
  -v VENDOR, --vendor VENDOR
                        Vendor Name, ex. Altaflex
  -b BATCH, --batch BATCH
                        Batch boolean (y or n)
  -bs BATCH_SIZE, --batch_size BATCH_SIZE
                        Batch Size (integer)
```
---------------------------------------------------------------------
Here's an example:
```
python register_components_ui.py -t 'DATA FLEX' -s Dummy -pl BARREL -m TRIPLET -f 2 -v Vector -b y -bs 2
```

The argument `-bs or --batch_size` is optional but is required **IF** you are entering a batch, `-b y --batch y`.
Otherwise,
```
python register_components_ui.py -t 'DATA FLEX' -s Dummy -pl BARREL -m TRIPLET -f 2 -v Vector -b n
```
---------------------------------------------------------------------
The options for each argument that should be in included in the drop down menues on the UI are as follows:

| TYPE | STATUS | PLACEMENT | MODULES | FLAVOR | VENDOR | BATCH | BATCH SIZE |
| ---- | ------ | --------- | ------- | ------ | ------ | ----- | ---------- |
| DATA FLEX | Prototype | BARREL | TRIPLET | 0 | Altaflex | yes| Type Number |
| POWER FLEX | Pre-Production | RING | QUAD | 1 | PFC | no |    |
| RING | Production |   | BOTH | 2 | Cirexx |   |   |
| Z-RAY | Dummy |   |   | 3 | EPEC |    |   |
| PPO |     |   |   | 4 | Vector |  |   |
|   |   |   |   |   | Summit |  |   |

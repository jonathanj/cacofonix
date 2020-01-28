=========
cacofonix
=========

.. image:: docs/Cacofonix.png

Composing and compiling the epics of conquest, self-reflection and defeat in
your software projects. Singing them is better left as an exercise for the
reader.

Installation
------------

For general use purposes:

.. code:: bash

   pip3 install git+ssh://git@github.com:jonathanj/cacofonix.git


For development purposes:

.. code:: bash

   # Clone the repo.
   git clone git@github.com:jonathanj/cacofonix.git
   cd cacofonix
   # Install the package with -e to use a "source" install, this runs the
   # package from source instead of installing it, avoiding the need to
   # continually install it when developing.
   pip3 install -e .

After installing the package, a command-line script will installed that can be
run as ``cacofonix``. If the script cannot be found then it is likely not on
your shell search path.


Configuration
-------------

See `config.example.yaml`_ for a commented example configuration.

.. _config.example.yaml: https://github.com/jonathanj/cacofonix/blob/master/config.example.yaml


Usage
-----

Cacofonix has two modes of operation:

1. Compose new change fragments, to store in the repo until a later time.
2. Compile a changelog from the existing change fragments, and merge these with
   an existing changelog.

In both of these modes the ``--config`` option (required) must be specified
before the subcommand:

.. code:: bash

   cacofonix --config path/to/config.yaml compose …


Composing new fragments
^^^^^^^^^^^^^^^^^^^^^^^

The basic usage is to use ``cacofonix compose`` to do the following:

* Compose a new change fragment;
* Write it to the change fragment directory, as specified in the configuration;
* Stage the file in git.

Consult ``cacofonix compose --help`` for detailed command-line help.


Compiling changelogs
^^^^^^^^^^^^^^^^^^^^

The basic usage is to use ``cacofonix compile`` to do the following:

* Find uncompiled change fragments;
* Convert each fragment to suitable markup;
* Compile them together to create a new changelog, for one version;
* Merge the new changelog into an existing changelog;
* Clean up and stage the removals in git.

Consult ``cacofonix compile --help`` for detailed command-line help.


Acknowledgements
----------------

Thanks to Amber Brown for `towncrier`_, upon which Cacofonix is built, (using
private APIs, sorry!)

.. _towncrier: https://github.com/hawkowl/towncrier

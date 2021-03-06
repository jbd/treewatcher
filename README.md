Treewatcher
===========

Treewatcher is a python library to monitor a directory recursively using inotify.
The user can define callbacks by subclassing a class. Depending from the type of
the class the user subclass from, callbacks can be executed in the same process of
the monitoring process, in a thread or a pool of thread.

Treewatcher is still a work in progress and the main focus for now is automated testing.

It's inspired from some parts of the pytagsfs project : http://www.pytagsfs.org/

Dependencies
============

inotifyx (>=0.1.1) : http://www.alittletooquiet.net/software/inotifyx/
You can install it using pip: $ pip install inotifyx

You can also run python setup.py install from the project root directory,
it will pull the needed dependencies.

Installation
============

I suggest to use virtualenv. It will help keeping your distribution happy :)
Install inotifyx (see Dependencies) and install treewatcher :

	$ git clone git://github.com/jbd/treewatcher.git
	$ cd treewatcher && python setup.py install

Here is a complete example using virtualenv and virtualenvwrapper from http://www.doughellmann.com/projects/virtualenvwrapper/

	$ mkvirtualenv test
	$ easy_install pip
	$ git clone git://github.com/jbd/treewatcher.git
	$ cd treewatcher
	$ python setup.py install

You're done ! You can now launch the test suite :

	$ cd tests && ./run_all.py

Launching tests
===============

Tests are in the 'tests' directory. They can all be launch using the run_all.py script :

	$ ./run_all.py (it takes 10 minutes on my machine)

You can also list all available test using le -l option :

	$ ./run_all.py -l

You can pick one, or more from the list and run them :

	$ ./run_all.py TestSerialTreeWatcher.test_nosublevel_onefile TestFourThreadsTreeWatcher.test_one_sublevel_one

You can also run each test files individually :

	$ python test_serialevents.py

You can list tests available from a specific file :

	$ python test_serialevents.py -l

And run specifics tests from a specific file :

	$ python test_serialevents.py TestSerialTreeWatcher.test_nosublevel_onedir  TestSerialTreeWatcher.test_nosublevel_onefile


Examples
========

You will find examples in the examples directory.


How does it work ?
==================

Events Process (Producer) ------> Events Queue ------> Events Dispatcher (serial, threaded, processes) ------> Event consumer

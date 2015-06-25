# -*- coding: utf-8 -*-
"""
.. invisible:
    _   _ _____ _     _____ _____
   | | | |  ___| |   |  ___/  ___|
   | | | | |__ | |   | |__ \ `--.
   | | | |  __|| |   |  __| `--. \
   \ \_/ / |___| |___| |___/\__/ /
    \___/\____/\_____|____/\____/

.. container:: flexbox

   .. image:: _static/veles_big.png
      :class: left

   .. container::

      %s

███████████████████████████████████████████████████████████████████████████████

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.

███████████████████████████████████████████████████████████████████████████████
"""


from email.utils import parsedate_tz, mktime_tz, formatdate
from importlib import import_module
from sys import version_info, modules
from types import ModuleType
from warnings import warn
from veles.compat import is_interactive
from veles.paths import __root__

__project__ = "Veles Machine Learning Platform"
__versioninfo__ = 0, 8, 11
__version__ = ".".join(map(str, __versioninfo__))
__license__ = "Samsung Proprietary License"
__copyright__ = u"© 2013 Samsung Electronics Co., Ltd."
__authors__ = ["Gennady Kuznetsov", "Vadim Markovtsev", "Alexey Kazantsev",
               "Lyubov Podoynitsina", "Denis Seresov", "Dmitry Senin",
               "Alexey Golovizin", "Egor Bulychev", "Ernesto Sanches"]
__contact__ = "Gennady Kuznetsov <g.kuznetsov@samsung.com>"
__plugins__ = set()

try:
    __git__ = "$Commit$"
    __date__ = mktime_tz(parsedate_tz("$Date$"))
except Exception as ex:
    warn("Cannot expand variables generated by Git, setting them to None")
    __git__ = None
    __date__ = None

__logo_ext__ = ("Copyright %s" % __copyright__,
                "Released under Apache 2.0 license.",
                "https://velesnet.ml",
                "https://github.com/samsung/veles/issues")

__logo__ = \
    r" _   _ _____ _     _____ _____  " "\n" \
    r"| | | |  ___| |   |  ___/  ___| " + \
    (" Version %s." % __version__) + \
    (" %s\n" % formatdate(__date__, True)) + \
    r"| | | | |__ | |   | |__ \ `--.  " + \
    (" %s\n" % __logo_ext__[0]) + \
    r"| | | |  __|| |   |  __| `--. \ " + \
    (" %s\n" % __logo_ext__[1]) + \
    r"\ \_/ / |___| |___| |___/\__/ / " + \
    (" %s\n" % __logo_ext__[2]) + \
    r" \___/\____/\_____|____/\____/  " \
    " %s\n" % __logo_ext__[3]

if "sphinx" in modules:
    __doc__ %= "| %s\n      | Version %s %s\n      | %s\n\n      Authors:" \
        "\n\n      * %s" % (__project__, __version__,
                            formatdate(__date__, True), __copyright__,
                            "\n      * ".join(__authors__))
else:
    __doc__ = __logo__.replace(" ", "_", 2)  # nopep8

if version_info.major == 3 and version_info.minor == 4 and \
   version_info.micro < 1:
    warn("Python 3.4.0 has a bug which is critical to Veles OpenCL subsystem ("
         "see issue #21435). It is recommended to upgrade to 3.4.1.")


def __html__():
    """
    Opens VELES html documentation in the default web browser and builds it,
    if it does not exist.
    """
    import os
    from veles.config import root
    from veles.portable import show_file

    if not os.path.exists(root.common.help_dir):
        print("\"%s\" does not exist, unable to open the docs" %
              root.common.help_dir)
        return
    page = os.path.join(root.common.help_dir, "index.html")
    if not os.path.exists(page):
        from runpy import run_path
        print("Building the documentation...")
        run_path(os.path.join(__root__, "docs/generate_docs.py"))
    if os.path.exists(page):
        show_file(page)


class VelesModule(ModuleType):
    """Redefined module class with added properties which are lazily evaluated.
    """

    class PythonPathError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(VelesModule, self).__init__(__name__, *args, **kwargs)
        self.__dict__.update(modules[__name__].__dict__)
        self.__units_cache__ = None
        self.__modules_cache_ = None
        self.__plugins = None
        self.__loc = None

    def __call__(self, workflow, config=None, *args, **kwargs):
        """
        Launcher the specified workflow and returns the corresponding
        :class:`veles.launcher.Launcher` instance.
        If there exists a standard input, returns immediately after the
        workflow is initialized; otherwise, blocks until it finishes.
        If this command runs under IPython, it's local variables are passed
        into the workflow's :meth:`__init__()`.
        If "subprocess" keyword argument is set to True, runs in a separate
        process.

        Arguments:
            workflow: path to the Python file with workflow definition.
            config: path to the workflow configuration. If None, *_config.py
                    is taken.
            kwargs: arguments to be passed as if "veles" is executed from the
                    command line. They match the command line arguments except
                    that "-" must be substituted with "_". For example,
                    "backend" -> "--backend", random_seed -> "--random-seed".
                    See "veles --help" for the complete list.

        Returns:
            veles.launcher.Launcher instance which can be used to manage the
            execution (e.g., pause() and resume()); if "subprocess" was set to
            True, a started multiprocessing.Process instance is returned
            instead, which can be join()-ed.
        """
        if kwargs.get("subprocess", False):
            del kwargs["subprocess"]
            from multiprocessing import Process
            proc = Process(target=self.__call__, name="veles.__call__",
                           args=(workflow, config) + args, kwargs=kwargs)
            proc.start()
            return proc
        # FIXME(v.markovtsev): disable R0401 locally when pylint issue is fixed
        # https://bitbucket.org/logilab/pylint/issue/61
        # from veles.__main__ import Main  # pylint: disable=R0401
        Main = import_module("veles.__main__").Main
        if config is None:
            config = "-"
        if "interactive" in kwargs:
            interactive = kwargs["interactive"]
            del kwargs["interactive"]
        else:
            interactive = is_interactive()
        main = Main(interactive, workflow, config, *args, **kwargs)
        main.run()
        return main.launcher

    def __scan(self):
        import os
        import sys

        blacklist = {"tests", "external", "libVeles", "libZnicz"}
        # Temporarily disable standard output since some modules produce spam
        # during import
        stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        for root, dirs, files in os.walk(os.path.dirname(self.__file__)):
            if any(b in root for b in blacklist):
                del dirs[:]
                continue
            for file in files:
                modname, ext = os.path.splitext(file)
                if ext != '.py':
                    continue
                modpath = os.path.relpath(root, self.__root__).replace(
                    os.path.sep, '.')
                try:
                    yield import_module("%s.%s" % (modpath, modname))
                except Exception as e:
                    stdout.write("%s: %s\n" % (
                        os.path.relpath(os.path.join(root, file),
                                        self.__root__),
                        e))
        sys.stdout.close()
        sys.stdout = stdout

    @property
    def __units__(self):
        """
        Returns the array with all Unit classes found in the package file tree.
        """
        if self.__units_cache__ is not None:
            return self.__units_cache__

        for _ in self.__scan():
            pass

        from veles.unit_registry import UnitRegistry
        self.__units_cache__ = UnitRegistry.units
        return self.__units_cache__

    @property
    def __modules__(self):
        if self.__modules_cache_ is None:
            self.__modules_cache_ = set(self.__scan())
        return self.__modules_cache_

    @property
    def __loc__(self):
        """Calculates of lines of code relies on "cloc" utility.
        """
        if self.__loc is not None:
            return self.__loc

        from subprocess import Popen, PIPE

        result = {}

        def calc(cond):
            cmd = ("cd %s && echo $(find %s ! -path '*debian*' "
                   "! -path '*docs*' ! -path '*.pybuild*' "
                   "-exec cloc --quiet --csv {} \; | "
                   "sed -n '1p;0~3p' | tail -n +2 | cut -d ',' -f 5 | "
                   "tr '\n' '+' | head -c -1) | bc") %\
                  (self.__root__, cond)
            print(cmd)
            discovery = Popen(cmd, shell=True, stdout=PIPE)
            num, _ = discovery.communicate()
            return int(num)
        result["core"] = \
            calc("-name '*.py' ! -path '*cpplint*' ! -path './deploy/*' "
                 "! -path './web/*' ! -path './veles/external/*' "
                 "! -name create-emitter-tests.py ! -path "
                 "'./veles/tests/*' ! -path './veles/znicz/tests/*'")
        result["tests"] = calc("'./veles/tests' './veles/znicz/tests' "
                               "-name '*.py'")
        result["c/c++"] = calc(
            "\( -name '*.cc' -o -name '*.h' -o -name '*.c' \) ! -path "
            "'*google*' ! -path '*web*' ! -path '*zlib*' !"
            " -path '*libarchive*' ! -path '*jsoncpp*' ! -path '*boost*'")
        result["js"] = calc("-name '*.js' ! -path '*node_modules*' "
                            "! -path '*dist*' ! -path '*libs*' "
                            "! -path '*jquery*' "
                            "! -path '*viz.js*' ! -path '*emscripten*'")
        result["sass"] = calc("-name '*.scss' ! -path '*node_modules*' "
                              "! -path '*dist*' ! -path '*libs*' "
                              "! -path '*viz.js*' ! -path '*emscripten*'")
        result["html"] = calc("-name '*.html' ! -path '*node_modules*' "
                              "! -path '*dist*' ! -path '*libs*' "
                              "! -path '*viz.js*' ! -path '*emscripten*'")
        result["opencl/cuda"] = calc(
            "\( -name '*.cl' -o -name '*.cu' \) ! -path './web/*'")
        result["java"] = calc("'./mastodon/lib/src/main' -name '*.java'")
        result["tests"] += calc("'./mastodon/lib/src/test' -name '*.java'")

        result["all"] = sum(result.values())
        self.__loc = result
        return result

    @property
    def __plugins__(self):
        if self.__plugins is None:
            self.__plugins = set()
            from os import walk, path
            for root, dirs, files in walk(self.__root__):
                if ".veles" in files:
                    package = path.relpath(root, self.__root__).replace(
                        path.sep, '.')
                    try:
                        self.__plugins.add(self.import_module(package))
                    except ImportError:
                        continue
        return self.__plugins

    @classmethod
    def validate_environment(cls):
        """
        This method verifies the sequence of PYTHONPATH and warns about
        the crappy ones.
        """
        from sys import version_info, executable  # pylint: disable=W0404,W0621
        import os
        from subprocess import call
        from uuid import uuid4

        pypath = os.path.join(os.getcwd(), str(uuid4()), "crap", "check")
        if call((executable, "-c",
                 "import sys; sys.exit(sys.path[1] != \"%s\")" % pypath),
                env={"PYTHONPATH": pypath}):
            excmsg = (
                "Your Python environment looks crappy because PYTHONPATH does "
                "not have priority over other paths. Veles is sensitive to "
                "PYTHONPATH order. To reproduce the problem, run:\n"
                "PYTHONPATH=/tmp %s -c \"import sys; print(sys.path)\"\n"
                "Check your *.pth files, e.g. "
                "/usr/local/lib/python%d.%d/dist-packages/easy-install.pth. "
                "Perhaps, you should set sys.__egginsert to 1 on the first "
                "line of that file." %
                (executable, version_info.major, version_info.minor))
            raise cls.PythonPathError(excmsg)


if not isinstance(modules[__name__], VelesModule):
    modules[__name__] = VelesModule()

if __name__ == "__main__":
    __html__()

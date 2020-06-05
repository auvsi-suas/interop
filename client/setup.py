import os
import setuptools
import shutil
import subprocess
import sys
from distutils.command.build_py import build_py as _build_py
from distutils.command.clean import clean as _clean
from distutils.spawn import find_executable


class build_py(_build_py):
    def run(self):
        protoc = find_executable("protoc")
        if not protoc:
            sys.stderr.write('Cant find protoc.\n')
            sys.exit(-1)
        if not os.path.exists('auvsi_suas/proto'):
            shutil.copytree('../proto', 'auvsi_suas/proto')
        for (dirpath, dirnames, filenames) in os.walk("auvsi_suas/proto"):
            for filename in filenames:
                if not filename.endswith(".proto"):
                    continue
                filepath = os.path.join(dirpath, filename)
                if subprocess.call([protoc, '--python_out=.', filepath]) != 0:
                    sys.stderr.write('Failed to compile protos.\n')
                    sys.exit(-1)

        _build_py.run(self)


class clean(_clean):
    def run(self):
        if os.path.exists('auvsi_suas/proto'):
            shutil.rmtree('auvsi_suas/proto')
        _clean.run(self)


if __name__ == '__main__':
    reqs = []
    with open('requirements.txt', 'r') as f:
        reqs = f.readlines()

    setuptools.setup(
        name='auvsi_suas',
        description='AUVSI SUAS interoperability client library.',
        license='Apache 2.0',
        packages=setuptools.find_packages(),
        cmdclass = { 'clean': clean, 'build_py': build_py },
        install_requires=reqs,
    )  # yapf: disable

"""Copy portable catalogs into wheels; source checkout keeps one canonical copy."""
from pathlib import Path
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithResources(build_py):
    def run(self):
        super().run()
        root = Path(__file__).parent
        destination = Path(self.build_lib) / 'uasek/resources'
        for name in ('configs', 'templates', 'workflows'):
            shutil.copytree(root / name, destination / name, dirs_exist_ok=True)


setup(cmdclass={'build_py': BuildWithResources})

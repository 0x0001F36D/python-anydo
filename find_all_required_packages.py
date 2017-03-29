#!/usr/bin/env python3
import distutils.sysconfig as sysconfig
import os
import re


class FindAllRequiredPackages:
    @classmethod
    def _set_standard_packages(cls):
        modules = set()
        std_lib = sysconfig.get_python_lib(standard_lib=True)
        for root, dirs, files in os.walk(std_lib):
            for module in files:
                if module is not '__init__.py' and module.endswith('.py'):
                    full_name = os.path.join(root, module)[len(std_lib) + 1:-3].replace('\\', '.')
                    if '/' in full_name:
                        full_name = full_name.split('/')[0]
                    modules.add(full_name)

        cls.standard_packages = frozenset(sorted(modules))

    def __init__(self, excludes: list=None):
        default_exclusion = ['setuptools', 'sys', 'time']
        FindAllRequiredPackages._set_standard_packages()
        self.excludes = excludes + default_exclusion if excludes else default_exclusion
        self.found_third_party_modules = set()

    def find_packages(self, path: str='.') -> set:
        for root, dirs, files in os.walk(path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                self.search_for_packages(file, root)
        return sorted(self.found_third_party_modules)

    def search_for_packages(self, file: str, root: str):
        full_package_path = "{}/{}".format(root, file)
        with open(full_package_path) as fd:
            self.find_package_name_by_line(fd.readlines())

    def find_package_name_by_line(self, lines_in_package: list):
        """
        Does not support new line continuation, ie import os,\
                                                       re
        """
        found_packages = set()
        packages_is_word = re.compile('^\w+')

        for line in lines_in_package:
            if line.startswith("import") and ',' in line:
                FindAllRequiredPackages.get_multiples_packages_on_same_line(found_packages,
                                                                            line,
                                                                            packages_is_word)
            elif line.startswith("import") or line.startswith("from"):
                found_packages.add(line.split()[1])
            self.add_packages(found_packages)

    @staticmethod
    def get_multiples_packages_on_same_line(found_packages, line, packages_is_word):
        multiple_packages_on_same_line = line.split('import')[1].split(',')
        stripped_package_names = [p.strip() for p in multiple_packages_on_same_line
                                  if packages_is_word.match(p)]
        found_packages.update(stripped_package_names)

    def add_packages(self, found_packages: set):
        for package in found_packages:
            package_name = package.split('.')[0] if '.' in package else package

            if package_name not in self.standard_packages and package_name not in self.excludes:
                    self.found_third_party_modules.add(package_name)

if __name__ == '__main__':
    fp = FindAllRequiredPackages()
    print(fp.find_packages())

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
from glob import glob
import os


class openblasConan(ConanFile):
    name = "openblas"
    version = "0.3.1"
    url = "https://github.com/xianyi/OpenBLAS"
    homepage = "http://www.openblas.net/"
    description = "OpenBLAS is an optimized BLAS library based on GotoBLAS2 1.13 BSD version."
    license = "BSD 3-Clause"
    exports_sources = ["CMakeLists.txt", "LICENSE"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "USE_MASS": [True, False],
               "USE_OPENMP": [True, False],
               "NO_LAPACKE": [True, False]
              }
    default_options = "shared=True", "USE_MASS=False", "USE_OPENMP=False", "NO_LAPACKE=False"

    def get_make_arch(self):
        return "32" if self.settings.arch == "x86" else "64"

    def get_make_build_type_debug(self):
        return "0" if self.settings.build_type == "Release" else "1"

    def get_make_option_value(self, option):
        return "1" if option else "0"

    def configure(self):
        if self.settings.compiler == "Visual Studio":
            if not self.options.shared:
                raise Exception("Static build not supported in Visual Studio: "
                                "https://github.com/xianyi/OpenBLAS/blob/v0.2.20/CMakeLists.txt#L177")

    def source(self):
        self.output.info("source()")
        source_url = "https://sourceforge.net/projects/openblas"
        file_name = ("{0} {1} version".format("OpenBLAS", self.version))
        tools.get("{0}/files/v{1}/{2}.tar.gz".format(source_url, self.version, file_name))
        os.rename(glob("xianyi-OpenBLAS-*")[0], "sources")

    def build(self):
        if self.settings.compiler != "Visual Studio":
            make_options = "DEBUG={debug} BINARY={binary} USE_MASS={mass} USE_OPENMP={openmp}".format(
                debug  = self.get_make_build_type_debug(),
                binary = self.get_make_arch(),
                mass   = self.get_make_option_value(self.options.USE_MASS),
                openmp = self.get_make_option_value(self.options.USE_OPENMP),
            )

            if not self.options.shared:      make_options += ' NO_SHARED=1'
            if     self.options.NO_LAPACKE:  make_options += ' NO_LAPACKE=1'

            self.output.info('Running make with: %s'%make_options)
            self.run("cd sources && make %s" % make_options, cwd=self.source_folder)

            self.output.info('Calling make install')
            self.run('cd sources && make PREFIX=%s install'%self.package_folder)

        else:
            self.output.warn("Building with CMake: Some options won't make any effect")
            cmake = CMake(self)
            cmake.definitions["USE_MASS"]   = self.options.USE_MASS
            cmake.definitions["USE_OPENMP"] = self.options.USE_OPENMP
            cmake.definitions["NO_LAPACKE"] = self.options.NO_LAPACKE
            cmake.configure(source_dir="sources")
            cmake.build()

    def package(self):
        self.fixPkgConfig(os.path.join(self.package_folder, 'lib', 'pkgconfig', 'openblas.pc'))
        self.fixCMakeConfig(os.path.join(self.package_folder, 'lib', 'cmake', 'openblas', 'OpenBLASConfig.cmake'))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")

    def fixPkgConfig(self, openblas):
        # pkg config files don't seem to be generated on windows by default.
        if self.settings.os == "Linux":
            self.output.info('Modifying pkg-config file to start with a prefix')
            with open(openblas) as f: data = f.read()
            data = 'prefix=%s\n'%self.package_folder + data
            with open(openblas, 'w') as f: f.write(data)

            self.output.info('Modifying pkg-config file to use a variable prefix')
            tools.replace_in_file(
                file_path=openblas,
                search=self.package_folder,
                replace="${prefix}"
            )

    def fixCMakeConfig(self, cmake_config_file):
        self.output.info('Modifying %s a prefix'%cmake_config_file)
        tools.replace_in_file(
            file_path=cmake_config_file,
            search=self.package_folder,
            replace="${CONAN_OPENBLAS_ROOT}"
        )

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :

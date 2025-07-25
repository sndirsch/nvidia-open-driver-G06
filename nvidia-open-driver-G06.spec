#
# spec file for package nvidia-open-driver-G06
#
# Copyright (c) 2022 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#

%define kernel_flavors default
%ifnarch aarch64
# limit build of -azure flavor to SP6
%if (!0%{?is_opensuse} && (0%{?sle_version} >= 150600 && 0%{?sle_version} < 150700))
%define kernel_flavors azure default
%else
%define kernel_flavors default
%endif
%else
%define kernel_flavors 64kb default
%endif

%if %{undefined kernel_module_directory}
%if 0%{?usrmerged}
%define kernel_module_directory /usr/lib/modules
%else
%define kernel_module_directory /lib/modules
%endif
%endif

%define compress_modules xz
Name:           nvidia-open-driver-G06
Version:        570.172.08
Release:        0
Summary:        NVIDIA open kernel module driver for Turing GPUs and later
License:        GPL-2.0 and MIT
Group:          System/Kernel
URL:            https://github.com/NVIDIA/open-gpu-kernel-modules/
Source0:        open-gpu-kernel-modules-%{version}.tar.gz
Source4:        kmp-post.sh
Source5:        kmp-postun.sh
Source8:        json-to-pci-id-list.py
Source9:        kmp-preun.sh
Source11:       nvidia-open-driver-G06.rpmlintrc
Source12:       supported-gpus-%{version}.json
Source13:       supported-gpus.json.LICENSE
BuildRequires:  %{kernel_module_package_buildreqs}
BuildRequires:  gcc-c++
BuildRequires:  kernel-source
BuildRequires:  kernel-syms
BuildRequires:  kernel-devel
BuildRequires:  kernel-default-devel
BuildRequires:  kmod
BuildRequires:  python3
BuildRequires:  zstd
%ifnarch aarch64
# limit build of -azure flavor to SP6
%if (!0%{?is_opensuse} && (0%{?sle_version} >= 150600 && 0%{?sle_version} < 150700))
BuildRequires:  kernel-azure-devel
BuildRequires:  kernel-syms-azure
%endif
%endif
ExclusiveArch:  x86_64 aarch64

%description
This package provides the open-source NVIDIA kernel module driver
for Turing GPUs and later.

%package kmp-default
Summary:        NVIDIA open kernel module driver for Turing GPUs and later (default kernel flavor)
BuildRequires: kernel-syms
BuildRequires: kmod
PreReq: kernel-default
PreReq: kernel-default-devel make gcc gcc-c++
Requires: openssl
Requires: mokutil
# Firmware files, modprobe configuration, etc. are actually required at run
# time, but they are not required for manipulating the modules once built (ex.
# signing after building):
Recommends: nvidia-common-G06 = %{version}
Conflicts: nvidia-gfxG06-kmp nvidia-driver-G06-kmp nvidia-open-driver-G06-signed-kmp nvidia-gfxG05-kmp
Provides: %name
Supplements: (kernel-default and %name)
%{expand:%(python3 %{S:8} --flavor default --open %{S:12})}

%description kmp-default
This package provides the open-source NVIDIA kernel module driver
for Turing GPUs and later. This is for default kernel flavor.

%ifnarch aarch64

# limit build of -azure flavor to SP6
%if (!0%{?is_opensuse} && (0%{?sle_version} >= 150600 && 0%{?sle_version} < 150700))

%package kmp-azure
Summary:        NVIDIA open kernel module driver for Turing GPUs and later (azure kernel flavor)
BuildRequires: kernel-syms
BuildRequires: kmod
PreReq: kernel-azure
PreReq: kernel-azure-devel make gcc gcc-c++
Requires: openssl
Requires: mokutil
# Firmware files, modprobe configuration, etc. are actually required at run
# time, but they are not required for manipulating the modules once built (ex.
# signing after building):
Recommends: nvidia-common-G06 = %{version}
Conflicts: nvidia-gfxG06-kmp nvidia-driver-G06-kmp nvidia-open-driver-G06-signed-kmp nvidia-gfxG05-kmp
Provides: %name
Supplements: (kernel-azure and %name)
%{expand:%(python3 %{S:8} --flavor azure --open %{S:12})}

%description kmp-azure
This package provides the open-source NVIDIA kernel module driver
for Turing GPUs and later. This is for azure kernel flavor.

%endif

%else

%package kmp-64kb
Summary:        NVIDIA open kernel module driver for Turing GPUs and later (64kb kernel flavor)
BuildRequires: kernel-syms
BuildRequires: kmod
PreReq: kernel-64kb
PreReq: kernel-64kb-devel make gcc gcc-c++
Requires: openssl
Requires: mokutil
# Firmware files, modprobe configuration, etc. are actually required at run
# time, but they are not required for manipulating the modules once built (ex.
# signing after building):
Recommends: nvidia-common-G06 = %{version}
Conflicts: nvidia-gfxG06-kmp nvidia-driver-G06-kmp nvidia-open-driver-G06-signed-kmp nvidia-gfxG05-kmp
Provides: %name
Supplements: (kernel-64kb and %name)
%{expand:%(python3 %{S:8} --flavor 64kb --open %{S:12})}

%description kmp-64kb
This package provides the open-source NVIDIA kernel module driver
for Turing GPUs and later. This is for 64kb kernel flavor.

%endif

%prep
%autosetup -p1 -n open-gpu-kernel-modules-%-%{version}
set -- *
mkdir source
mv "$@" source/
mkdir obj

%build
%ifarch aarch64
# -Wall is upstream default
export CFLAGS="-Wall -mno-outline-atomics"
%endif
# kernel was compiled using a different compiler
export CC=gcc
# no longer needed and never worked anyway (it was only a stub) [boo#1211892]
export NV_EXCLUDE_KERNEL_MODULES=nvidia-peermem
for flavor in %kernel_flavors; do
        rm -rf obj/$flavor
        cp -r source obj/$flavor
	pushd obj/$flavor
	if [ -d /usr/src/linux-$flavor ]; then
	  export SYSSRC=/usr/src/linux-$flavor
	else
	  export SYSSRC=/usr/src/linux
	fi
	export SYSOUT=/usr/src/linux-obj/%_target_cpu/$flavor
        make %{?_smp_mflags} modules modules DATE="date -d @${SOURCE_DATE_EPOCH:-$(date +%s)}" NV_BUILD_HOST=OBS HOSTNAME=OBS
        popd
done

%install
### do not sign the ghost .ko file, it is generated on target system anyway
export BRP_PESIGN_FILES=""
export INSTALL_MOD_PATH=%{buildroot}
export INSTALL_MOD_DIR=updates
for flavor in %kernel_flavors; do
	pushd obj/$flavor
	if [ -d /usr/src/linux-$flavor ]; then
	  export SYSSRC=/usr/src/linux-$flavor
	else
	  export SYSSRC=/usr/src/linux
	fi
	export SYSOUT=/usr/src/linux-obj/%_target_cpu/$flavor
        make modules_install
	popd
%ifarch x86_64
	arch=x86_64
%endif
%ifarch aarch64
	arch=aarch64
%endif
        if [ "$flavor" = "azure" ]; then
          dir=$(pushd /usr/src &> /dev/null; ls -d linux-*-azure-obj|sort -n|tail -n 1; popd &> /dev/null)
          kver_build=$(make -j$(nproc) -sC /usr/src/${dir}/${arch}/$flavor kernelrelease)
        else
          kver_build=$(make -j$(nproc) -sC /usr/src/linux-obj/${arch}/$flavor kernelrelease)
        fi
        mkdir -p %{buildroot}/usr/src/kernel-modules/nvidia-%{version}-${flavor}
        cp -r source/* %{buildroot}/usr/src/kernel-modules/nvidia-%{version}-${flavor}
        # save kernel version for later
        echo $kver_build > %{buildroot}/usr/src/kernel-modules/nvidia-%{version}-${flavor}/kernel_version
        # zero fake kernel modules to prevent generation of ksyms in package
        for i in %{buildroot}/%{kernel_module_directory}/${kver_build}/updates/*.ko; do
          rm -f $i; touch $i; chmod 644 $i
        done
done

%files kmp-default
%ghost %dir %{kernel_module_directory}/*-default/updates
%ghost %{kernel_module_directory}/*-default/updates/nvidia*.ko
%ghost %attr(755,root,root) %dir /var/lib/nvidia-pubkeys
%ghost %attr(644,root,root) /var/lib/nvidia-pubkeys/MOK-%{name}-%{version}.der
%dir /usr/src/kernel-modules
/usr/src/kernel-modules/nvidia-%{version}-default/

%post kmp-default
RES=0
tw="false"
cat /etc/os-release | grep ^NAME | grep -q Tumbleweed && tw=true
if [ "$tw" = "false" ]; then
#kmp-post.sh
flavor=default
%include %{S:4}
fi
exit $RES

%triggerin kmp-default -- kernel-default-devel
RES=0
tw="false"
cat /etc/os-release | grep ^NAME | grep -q Tumbleweed && tw=true
if [ "$tw" = "true" ]; then
#kmp-post.sh
flavor=default
%include %{S:4}
fi
exit $RES

%preun kmp-default
#kmp-preun.sh
flavor=default
%include %{S:9}

%postun kmp-default
#kmp-postun.sh
flavor=default
%include %{S:5}

%ifnarch aarch64

# limit build of -azure flavor to SP6
%if (!0%{?is_opensuse} && (0%{?sle_version} >= 150600 && 0%{?sle_version} < 150700))

%files kmp-azure
%exclude %{kernel_module_directory}/*-azure/updates/
%ghost %attr(755,root,root) %dir /var/lib/nvidia-pubkeys
%ghost %attr(644,root,root) /var/lib/nvidia-pubkeys/MOK-%{name}-%{version}.der
%dir /usr/src/kernel-modules
/usr/src/kernel-modules/nvidia-%{version}-azure/

%triggerin kmp-azure -- kernel-azure-devel
#kmp-post.sh
flavor=azure
%include %{S:4}
exit $RES

%preun kmp-azure
#kmp-preun.sh
flavor=azure
%include %{S:9}

%postun kmp-azure
#kmp-postun.sh
flavor=azure
%include %{S:5}

%endif

%else

%files kmp-64kb
%ghost %dir %{kernel_module_directory}/*-64kb/updates
%ghost %{kernel_module_directory}/*-64kb/updates/nvidia*.ko
%ghost %attr(755,root,root) %dir /var/lib/nvidia-pubkeys
%ghost %attr(644,root,root) /var/lib/nvidia-pubkeys/MOK-%{name}-%{version}.der
%dir /usr/src/kernel-modules
/usr/src/kernel-modules/nvidia-%{version}-64kb/

%post kmp-64kb
RES=0
tw="false"
cat /etc/os-release | grep ^NAME | grep -q Tumbleweed && tw=true
if [ "$tw" = "false" ]; then
#kmp-post.sh
flavor=64kb
%include %{S:4}
fi
exit $RES

%triggerin kmp-64kb -- kernel-64kb-devel
RES=0
tw="false"
cat /etc/os-release | grep ^NAME | grep -q Tumbleweed && tw=true
if [ "$tw" = "true" ]; then
#kmp-post.sh
flavor=64kb
%include %{S:4}
fi
exit $RES

%preun kmp-64kb
#kmp-preun.sh
%include %{S:9}

%postun kmp-64kb
#kmp-postun.sh
flavor=64kb
%include %{S:5}

%endif


%if 0%{?rhel} <= 5
%define __python /usr/bin/python2.6
%endif
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           cloud-init
Version:        0.6.3
Release:        0.12.bzr532%{?dist}
Summary:        Cloud instance init scripts

Group:          System Environment/Base
License:        GPLv3
URL:            http://launchpad.net/cloud-init
# bzr export -r 532 cloud-init-0.6.3-bzr532.tar.gz lp:cloud-init
Source0:        %{name}-%{version}-bzr532.tar.gz
Source1:        cloud-init-fedora.cfg
Source2:        cloud-init-README.fedora

Patch0:         cloud-init-0.6.3-fedora.patch
# Make runparts() work on Fedora
# https://bugs.launchpad.net/cloud-init/+bug/934404
Patch1:         cloud-init-0.6.3-no-runparts.patch
# https://bugs.launchpad.net/cloud-init/+bug/970071
Patch2:         cloud-init-0.6.3-lp970071.patch
# Add sysv init scripts
Patch3:         cloud-init-0.6.3-sysv.patch
# Support subprocess on python < 2.7
Patch4:         cloud-init-0.6.3-subprocess-2.6.patch
# Add support for installing packages with yum
Patch5:         cloud-init-0.6.3-yum.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=850916
# https://bugs.launchpad.net/cloud-init/+bug/1040200
# http://bazaar.launchpad.net/~cloud-init-dev/cloud-init/trunk/revision/635
Patch6:         cloud-init-0.6.3-fqdn.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=857502
# https://bugs.launchpad.net/cloud-init/+bug/1050962
Patch7:         cloud-init-0.6.3-ip-based-hostname.patch

Patch100:       cloud-init-0.6.3-use-python2.6.patch
Patch101:       cloud-init-0.6.3-ext4.patch

BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%if 0%{?rhel} >= 6
BuildRequires:  python-devel
BuildRequires:  python-setuptools-devel
Requires:       e2fsprogs
%else
BuildRequires:  python26-devel
BuildRequires:  python-setuptools
Requires:       e4fsprogs
%endif
Requires:       iproute
Requires:       libselinux-python
Requires:       net-tools
Requires:       procps
%if 0%{?rhel} >= 6
Requires:       python-boto
Requires:       python-cheetah
Requires:       python-configobj
Requires:       PyYAML
%else
Requires:       python26-boto
Requires:       python26-cheetah
Requires:       python26-configobj
Requires:       python26-PyYAML
%endif
Requires:       rsyslog
Requires:       shadow-utils
Requires:       /usr/bin/run-parts
Requires(post):   chkconfig
Requires(preun):  chkconfig
Requires(postun): initscripts

%description
Cloud-init is a set of init scripts for cloud instances.  Cloud instances
need special scripts to run during initialization to retrieve and install
ssh keys and to let the user run various scripts.


%prep
%setup -q -n %{name}-%{version}-bzr532
%patch0 -p0
%patch1 -p0
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p0
%if 0%{?rhel} <= 5
%patch100 -p0
%patch101 -p1
%endif

cp -p %{SOURCE2} README.fedora


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

for x in $RPM_BUILD_ROOT/%{_bindir}/*.py; do mv "$x" "${x%.py}"; done
chmod +x $RPM_BUILD_ROOT/%{python_sitelib}/cloudinit/SshUtil.py
mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/cloud

# We supply our own config file since our software differs from Ubuntu's.
cp -p %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg

# Note that /etc/rsyslog.d didn't exist by default until F15.
# el6 request: https://bugzilla.redhat.com/show_bug.cgi?id=740420
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p tools/21-cloudinit.conf $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/21-cloudinit.conf

# Install the init scripts
mkdir -p $RPM_BUILD_ROOT/%{_initrddir}
install -p -m 755 sysv/* $RPM_BUILD_ROOT/%{_initrddir}/


%clean
rm -rf $RPM_BUILD_ROOT


%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    # Enabled by default per "runs once then goes away" exception
    for svc in init-local init config final; do
        chkconfig --add cloud-$svc
        chkconfig cloud-$svc on
    done
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    for svc in init-local init config final; do
        chkconfig cloud-$svc off
        chkconfig --del cloud-$svc
    done
    # One-shot services -> no need to stop
fi

%postun
# One-shot services -> no need to restart


%files
%doc ChangeLog LICENSE TODO README.fedora
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg
%dir               %{_sysconfdir}/cloud/cloud.cfg.d
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg.d/*.cfg
%doc               %{_sysconfdir}/cloud/cloud.cfg.d/README
%dir               %{_sysconfdir}/cloud/templates
%config(noreplace) %{_sysconfdir}/cloud/templates/*
%{_initrddir}/cloud-*
%{python_sitelib}/*
%{_libexecdir}/%{name}
%{_bindir}/cloud-init*
%doc %{_datadir}/doc/%{name}
%dir %{_sharedstatedir}/cloud

%config(noreplace) %{_sysconfdir}/rsyslog.d/21-cloudinit.conf


%changelog
* Wed Dec 13 2012 Andy Grimm <agrimm@gmail.com> - 0.6.3-0.12.bzr532
- Correctly generate IP-based hostnames [RH:857502 LP:1050962]

* Thu Sep 13 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.11.bzr532
- Use a FQDN (instance-data.) for instance data URL fallback [RH:850916 LP:1040200]

* Tue Sep 11 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.10.bzr532
- Add support for ext4 on EPEL5

* Thu Jul 19 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 0.6.3-0.9.bzr532
- Support EPEL5 using python 2.6 and adjustment of chkconfig order

* Wed Jun 27 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.7.bzr532
- Add support for installing yum packages

* Mon Jun 18 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.6.bzr532
- Further adjustments to support EPEL 6

* Fri Jun 15 2012 Tomas Karasek <tomas.karasek@cern.ch> - 0.6.3-0.5.bzr532
- Fix cloud-init-cfg invocation in init script

* Tue May 22 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.4.bzr532
- Support EPEL 6

* Sat Mar 31 2012 Andy Grimm <agrimm@gmail.com> - 0.6.3-0.2.bzr532
- Fixed incorrect interpretation of relative path for
  AuthorizedKeysFile (BZ #735521)

* Mon Mar  5 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.1.bzr532
- Rebased against upstream rev 532
- Fixed runparts() incompatibility with Fedora

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.2-0.8.bzr457
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Oct  5 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.7.bzr457
- Disabled SSH key-deleting on startup

* Wed Sep 28 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.6.bzr457
- Consolidated selinux file context patches
- Fixed cloud-init.service dependencies
- Updated sshkeytypes patch
- Dealt with differences from Ubuntu's sshd

* Sat Sep 24 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.5.bzr457
- Rebased against upstream rev 457
- Added missing dependencies

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.4.bzr450
- Added more macros to the spec file

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.3.bzr450
- Fixed logfile permission checking
- Fixed SSH key generation
- Fixed a bad method call in FQDN-guessing [LP:857891]
- Updated localefile patch
- Disabled the grub_dpkg module
- Fixed failures due to empty script dirs [LP:857926]

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.2.bzr450
- Updated tzsysconfig patch

* Wed Sep 21 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.1.bzr450
- Initial packaging

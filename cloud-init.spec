%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           cloud-init
Version:        0.7.0
Release:        0.2.bzr659%{?dist}
Summary:        Cloud instance init scripts

Group:          System Environment/Base
License:        GPLv3
URL:            http://launchpad.net/cloud-init
# bzr export -r 659 cloud-init-0.7.0-bzr659.tar.gz lp:cloud-init
Source0:        %{name}-%{version}-bzr659.tar.gz
Source1:        cloud-init-fedora.cfg
Source2:        cloud-init-README.fedora
Patch0:         cloud-init-0.7.0-fedora.patch
# Make Fedora use the same hostname-updating code as Debian (/etc/hostname)
# https://code.launchpad.net/~gholms/cloud-init/hostname-refactor/+merge/125869
Patch1:         cloud-init-0.7.0-hostname-refactor.patch
# Fix fingerprint printing caused by recent user code refactoring
# https://code.launchpad.net/~harlowja/cloud-init/patch-ssh-key-users/+merge/125606
Patch2:         cloud-init-0.7.0-ssh-key-users.patch

BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-devel
BuildRequires:  python-setuptools-devel
BuildRequires:  systemd-units
Requires:       e2fsprogs
Requires:       iproute
Requires:       libselinux-python
Requires:       net-tools
Requires:       policycoreutils-python
Requires:       procps
Requires:       python-boto
Requires:       python-cheetah
Requires:       python-configobj
Requires:       python-prettytable
Requires:       PyYAML
Requires:       rsyslog
Requires:       shadow-utils
Requires:       xfsprogs
Requires:       /usr/bin/run-parts
Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units

%description
Cloud-init is a set of init scripts for cloud instances.  Cloud instances
need special scripts to run during initialization to retrieve and install
ssh keys and to let the user run various scripts.


%prep
%setup -q -n %{name}-%{version}-bzr659
%patch0 -p1
%patch1 -p1
%patch2 -p1

cp -p %{SOURCE2} README.fedora


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/cloud

# We supply our own config file since our software differs from Ubuntu's.
cp -p %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p tools/21-cloudinit.conf $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/21-cloudinit.conf

# Install the systemd bits
mkdir -p        $RPM_BUILD_ROOT/%{_unitdir}
cp -p systemd/* $RPM_BUILD_ROOT/%{_unitdir}


%clean
rm -rf $RPM_BUILD_ROOT


%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    # Enabled by default per "runs once then goes away" exception
    /bin/systemctl enable cloud-config.service     >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-final.service      >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-init.service       >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-init-local.service >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable cloud-config.service >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-final.service  >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-init.service   >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-init-local.service >/dev/null 2>&1 || :
    # One-shot services -> no need to stop
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
# One-shot services -> no need to restart


%files
%doc ChangeLog LICENSE TODO README.fedora
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg
%dir               %{_sysconfdir}/cloud/cloud.cfg.d
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg.d/*.cfg
%doc               %{_sysconfdir}/cloud/cloud.cfg.d/README
%dir               %{_sysconfdir}/cloud/templates
%config(noreplace) %{_sysconfdir}/cloud/templates/*
%{_unitdir}/cloud-config.service
%{_unitdir}/cloud-config.target
%{_unitdir}/cloud-final.service
%{_unitdir}/cloud-init-local.service
%{_unitdir}/cloud-init.service
%{python_sitelib}/*
%{_libexecdir}/%{name}
%{_bindir}/cloud-init*
%doc %{_datadir}/doc/%{name}
%dir %{_sharedstatedir}/cloud

%config(noreplace) %{_sysconfdir}/rsyslog.d/21-cloudinit.conf


%changelog
* Sat Sep 22 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.2.bzr659
- Rebased against upstream rev 659
- Fixed hostname persistence
- Fixed ssh key printing

* Mon Sep 17 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.1.bzr650
- Rebased against upstream rev 650
- Added support for useradd --selinux-user

* Thu Sep 13 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.5.bzr532
- Use a FQDN (instance-data.) for instance data URL fallback [RH:850916 LP:1040200]
- Shut off systemd timeouts [RH:836269]
- Send output to the console [RH:854654]

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.3-0.4.bzr532
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jun 27 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.3.bzr532
- Add support for installing yum packages

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
